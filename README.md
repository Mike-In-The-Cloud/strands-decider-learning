# Decision agent

A [LangGraph](https://langchain-ai.github.io/langgraph/) agent hosted with [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/using-any-agent-framework.html). [Strands Decider 2B](https://strandsagents.com/blog/introducing-strands-decider/) picks one of four workflows. Claude Haiku writes the answer. The same decider grades it before it is returned.

Workflows: `summarize`, `classify`, `create`, `extract`. Prompts live in [`agent/prompts/`](agent/prompts). Graph nodes do not contain prompt text. Each node is its own file under [`agent/graph/nodes/`](agent/graph/nodes).

```
route --choice--> summarize | classify | create | extract ----+
         |                                   ^ same workflow  |
         +-- low confidence --> clarify      | revise         v
                                             +--------------- evaluate
                                                              |      |
                                                      explain |      | ask
                                                              v      v
                                                           explain  ask (one question, then END)
                                                              v
                                                           finalize
```

`evaluate` asks the decider five questions about the output in one call. Three are yes/no: does the output fulfil the request (fulfils), is it grounded in the user's text (grounded), and is it premature to answer before asking the user for something they did not provide (premature). One is a score: how good is the output (quality: poor, ok, good). One is a choice: what is the main fault, over `none`, `ignores_task`, `invents_facts`, `unfinished`, `wrong_format`. Python code then decides the action. The rules run in this order and the first match wins:

1. `ask` when grounded is below `EVAL_NOUL_MIN` or premature is at or above it. The `ask` node writes one question for the user from the request, the unsent draft, and the evaluator's feedback. The draft is not returned.
2. `revise` when fulfils is below `EVAL_NOUL_MIN` and fewer than `MAX_RETRIES` revisions have run. The same workflow runs again with the feedback.
3. `explain` otherwise.

The fault never changes the action. The shape follows the upstream [`tool_call_intervention.py`](https://github.com/strands-labs/strands-decider/blob/main/examples/strands/tool_call_intervention.py) example: the model classifies, the code decides.

The decider cannot write a reason. It names the main fault as a probability over fixed options. `explain` asks Haiku to read the output against each criterion, starting from that fault, and say what most plausibly drove each grade. The UI shows this under the agent's reply, labelled as Haiku's reading.

## Run locally

Prerequisites: [uv](https://docs.astral.sh/uv/), [pnpm](https://pnpm.io/), and the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) with an SSO profile that can call Bedrock. `make check` tells you which one is missing and how to install it.

```bash
cp .env.example .env   # set AWS_PROFILE; set HF_TOKEN for a faster model download
make install           # uv sync in decider/ and agent/, pnpm install in web/
make aws-login         # once per SSO session
make dev               # decider + agent + web in one terminal; prints the Web UI URL once it is serving
```

Open http://localhost:5173. The first `make dev` downloads `Qwen/Qwen3.5-2B-Base` (about 4.5 GB).

Each process also runs on its own:

| Target | Port | What it is |
|---|---|---|
| `make decider` | 8099 | `strands-decider serve`. Pins in [`decider/pyproject.toml`](decider/pyproject.toml). `GET /health` returns the model once loaded. |
| `make agent` | 8080 | `BedrockAgentCoreApp` in [`agent/main.py`](agent/main.py) via `agentcore dev --port 8080`. Standalone it shows the AgentCore TUI (`--no-browser`); under `make dev` it uses `--logs` so all three processes log to the one terminal. Waits up to 10 s for a just-stopped agent to release the port, then fails if 8080 is taken (without `--port` the CLI would silently move to 8081 and the UI proxy would 500). `POST /invocations` streams `node_start`, `node_end` (with `ms`), `decider`, `llm`, `result` (the answer, before the explanation is written), `done`. On the ask path there is no `result`; `done` carries the question. |
| `make web` | 5173 | Vite UI. Proxies `/invocations` to `AGENT_PORT` (default 8080). The sidebar lists each graph node, how long it took, and the decider probabilities. |

`make agent` and `make dev` run `make aws-check` first. It fails with a hint if `AWS_PROFILE` is unset, not in `~/.aws/config`, or has no live session.

## Configuration

All variables live in `.env`. Make exports them to every process.

| Variable | Default | |
|---|---|---|
| `AWS_PROFILE` | unset | Required. SSO profile from `~/.aws/config` with Bedrock access |
| `HF_TOKEN` | unset | Optional. Hugging Face token; avoids anonymous rate limits on the model download |
| `AWS_REGION` | `us-east-1` | Bedrock region |
| `LLM_MODEL_ID` | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Bedrock Converse model id |
| `DECIDER_URL` | `http://127.0.0.1:8099` | `strands-decider serve` base URL |
| `DECIDER_DEVICE` | `mps` on Apple silicon, else `cpu` | `mps`, `cuda`, or `cpu` |
| `ROUTE_CONFIDENCE_MIN` | `0.6` | Below this, the agent asks the user to pick a workflow |
| `EVAL_NOUL_MIN` | `0.6` | Threshold for fulfils, grounded, and premature |
| `MAX_RETRIES` | `1` | Revisions after a failed fulfils grade |

## Tests

```bash
make test
```

The graph tests stub the decider and Haiku. They do not call AWS or download the model.

## Deploy

[`agentcore/agentcore.json`](agentcore/agentcore.json) is an AgentCore CodeZip runtime (`PYTHON_3_12`, HTTP, entrypoint `agent/main.py`).

```bash
pnpm dlx @aws/agentcore deploy
```

`agentcore/cdk` stays on npm. The AgentCore scaffold scripts call `npm` directly.

The deployed runtime cannot reach a decider on your laptop. Set `DECIDER_URL` to a host the runtime can call before you rely on the cloud endpoint. Hosting the decider is out of scope. The execution role still needs `bedrock:InvokeModel` for Haiku.
