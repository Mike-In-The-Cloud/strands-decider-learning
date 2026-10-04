SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

-include .env
export

DECIDER_MODEL ?= StrandsAgents/strands-decider-2B-hobson-v19
DECIDER_PORT  ?= 8099
AGENT_PORT    ?= 8080
WEB_PORT      ?= 5173
AGENTCORE     ?= pnpm dlx @aws/agentcore
# Standalone `make agent` gets the interactive TUI; `make dev` uses --logs so the
# three processes share one terminal and the Vite URL stays visible.
AGENT_DEV_FLAGS ?= --no-browser

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)
ifeq ($(UNAME_S)-$(UNAME_M),Darwin-arm64)
DECIDER_DEVICE ?= mps
else
DECIDER_DEVICE ?= cpu
endif

.PHONY: help check install aws-check aws-login decider agent web dev test

help: ## List targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo
	@echo "First run:  cp .env.example .env  (set AWS_PROFILE, optionally HF_TOKEN)"

check: ## Verify uv, pnpm, and aws are installed
	@command -v uv >/dev/null 2>&1 || { \
	  echo "uv is not installed."; \
	  echo "  install: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
	  echo "  or:      brew install uv"; \
	  exit 1; }
	@command -v pnpm >/dev/null 2>&1 || { \
	  echo "pnpm is not installed."; \
	  echo "  install: corepack enable pnpm"; \
	  echo "  or:      npm install -g pnpm"; \
	  exit 1; }
	@command -v aws >/dev/null 2>&1 || { \
	  echo "aws CLI is not installed."; \
	  echo "  install: brew install awscli"; \
	  echo "  or:      https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"; \
	  exit 1; }
	@echo "uv, pnpm, aws: ok"

install: check ## Install decider, agent, and web dependencies
	cd decider && uv sync
	cd agent && uv sync
	cd web && pnpm install

aws-check: ## Verify AWS_PROFILE is set, exists, and has a live SSO session
	@if [ -z "$${AWS_PROFILE:-}" ]; then \
	  echo "AWS_PROFILE is not set."; \
	  echo "  cp .env.example .env and set AWS_PROFILE to an SSO profile from ~/.aws/config"; \
	  exit 1; fi
	@if ! aws configure list-profiles 2>/dev/null | grep -qx "$$AWS_PROFILE"; then \
	  echo "AWS profile '$$AWS_PROFILE' is not in ~/.aws/config."; \
	  echo "  configure: aws configure sso --profile $$AWS_PROFILE"; \
	  exit 1; fi
	@if ! aws sts get-caller-identity --profile "$$AWS_PROFILE" >/dev/null 2>&1; then \
	  echo "No valid AWS session for profile '$$AWS_PROFILE'."; \
	  echo "  login: make aws-login   (runs: aws sso login --profile $$AWS_PROFILE)"; \
	  exit 1; fi
	@echo "AWS profile '$$AWS_PROFILE': ok"

aws-login: ## Start an AWS SSO session for AWS_PROFILE
	@if [ -z "$${AWS_PROFILE:-}" ]; then \
	  echo "AWS_PROFILE is not set. cp .env.example .env and set it."; exit 1; fi
	aws sso login --profile "$$AWS_PROFILE"

decider: ## Run Strands Decider on port 8099
	@if [ -z "$${HF_TOKEN:-}" ]; then \
	  echo "HF_TOKEN is not set. The first model download will be slower. Set it in .env to speed it up."; fi
	cd decider && uv run strands-decider serve $(DECIDER_MODEL) --device $(DECIDER_DEVICE) --port $(DECIDER_PORT)

agent: aws-check ## Run the AgentCore dev server on port 8080
	@# A just-stopped agent can hold the port for a few seconds; wait before giving up.
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
	  lsof -nP -iTCP:$(AGENT_PORT) -sTCP:LISTEN >/dev/null 2>&1 || break; \
	  [ $$i -eq 1 ] && echo "Port $(AGENT_PORT) is in use, waiting for it to free up..."; \
	  sleep 1; \
	done; \
	if lsof -nP -iTCP:$(AGENT_PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
	  echo "Port $(AGENT_PORT) is still in use:"; \
	  lsof -nP -iTCP:$(AGENT_PORT) -sTCP:LISTEN | tail -n +2; \
	  echo "  stop that process (kill <PID>), or set AGENT_PORT to another port"; \
	  exit 1; \
	fi
	$(AGENTCORE) dev $(AGENT_DEV_FLAGS) --port $(AGENT_PORT)

web: ## Run the Vite UI on port 5173
	cd web && pnpm dev --port $(WEB_PORT)

dev: check aws-check ## Run decider, agent, and web together (Ctrl-C stops all)
	$(MAKE) -j4 AGENT_DEV_FLAGS=--logs decider agent web ready

ready: ## Wait for the three services, then print the UI URL
	@i=0; until curl -fsS -o /dev/null http://localhost:$(WEB_PORT)/ \
	        && curl -fsS -o /dev/null http://localhost:$(AGENT_PORT)/ping; do \
	  i=$$((i+1)); [ $$i -lt 120 ] || { echo "web/agent not up after 2 minutes; check the logs above"; exit 0; }; sleep 1; done
	@i=0; until curl -fsS -o /dev/null http://localhost:$(DECIDER_PORT)/health; do \
	  [ $$i -eq 0 ] && echo && echo "  Web + agent up. Waiting for the decider (first run downloads the model)..."; \
	  i=$$((i+1)); [ $$i -lt 900 ] || { echo "decider not up after 30 minutes; check the logs above"; exit 0; }; sleep 2; done
	@echo
	@echo "  ================================================"
	@echo "  Ready. Open:  http://localhost:$(WEB_PORT)/"
	@echo "  ================================================"
	@echo

test: ## Run agent tests
	cd agent && uv run pytest
