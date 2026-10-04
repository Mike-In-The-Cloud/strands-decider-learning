import { useState, type Dispatch, type SetStateAction } from "react";
import type { AgentEvent, ChatMessage, TraceNode } from "../types";

const SESSION_HEADER = "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id";
const sessionId = `decision-agent-${crypto.randomUUID()}`;

export function useAgentStream() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [trace, setTrace] = useState<TraceNode[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send(prompt: string) {
    const text = prompt.trim();
    if (!text || running) return;
    setRunning(true);
    setError(null);
    setTrace([]);
    setMessages((current) => [...current, { role: "user", text }]);

    try {
      const response = await fetch("/invocations", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          [SESSION_HEADER]: sessionId,
        },
        body: JSON.stringify({ prompt: text }),
      });
      if (!response.ok || !response.body) {
        throw new Error(`Request failed (${response.status})`);
      }
      for await (const event of readSSE(response.body)) {
        applyEvent(event, setTrace, setMessages, setError);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setRunning(false);
    }
  }

  return { messages, trace, running, error, send };
}

function applyEvent(
  event: AgentEvent,
  setTrace: Dispatch<SetStateAction<TraceNode[]>>,
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>,
  setError: Dispatch<SetStateAction<string | null>>,
) {
  if (event.error && event.type !== "done") {
    setError(event.error);
  }
  if (event.type === "error") return;

  if (event.type === "node_start" && event.node && event.run_id) {
    const runId = event.run_id;
    const node = event.node;
    setTrace((current) => [...current, { runId, node }]);
    return;
  }

  if (event.type === "node_end" && event.run_id) {
    const runId = event.run_id;
    const ms = event.ms;
    setTrace((current) =>
      current.map((item) => (item.runId === runId ? { ...item, ms } : item)),
    );
    return;
  }

  if (event.type === "decider" && event.node && event.answers) {
    const node = event.node;
    const answers = event.answers;
    const latencyMs = event.latency_ms ?? 0;
    setTrace((current) => attach(current, node, (item) => ({ ...item, decider: { latencyMs, answers } })));
    return;
  }

  if (event.type === "llm" && event.node) {
    const node = event.node;
    const model = event.model;
    setTrace((current) => attach(current, node, (item) => ({ ...item, model })));
    return;
  }

  if (event.type === "result") {
    // The answer is final; the explanation is still being written.
    setMessages((current) => [
      ...current,
      {
        role: "assistant",
        text: event.output ?? "",
        workflow: event.workflow,
        verdict: event.verdict,
        explaining: true,
      },
    ]);
    return;
  }

  if (event.type === "done") {
    setMessages((current) => {
      const last = current[current.length - 1];
      if (last?.role === "assistant" && last.explaining) {
        const updated = { ...last, explaining: false, explanation: event.explanation };
        return [...current.slice(0, -1), updated];
      }
      return [
        ...current,
        {
          role: "assistant",
          text: event.output ?? "",
          workflow: event.workflow,
          verdict: event.verdict,
          explanation: event.explanation,
        },
      ];
    });
  }
}

function attach(current: TraceNode[], node: string, update: (item: TraceNode) => TraceNode) {
  let target = -1;
  for (let i = current.length - 1; i >= 0; i -= 1) {
    if (current[i].node === node && current[i].ms === undefined) {
      target = i;
      break;
    }
  }
  if (target === -1) {
    for (let i = current.length - 1; i >= 0; i -= 1) {
      if (current[i].node === node) {
        target = i;
        break;
      }
    }
  }
  if (target < 0) return current;
  return current.map((item, i) => (i === target ? update(item) : item));
}

async function* readSSE(body: ReadableStream<Uint8Array>) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const data = chunk
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim())
        .join("\n");
      if (!data) continue;
      yield parseEvent(data);
    }
  }
}

function parseEvent(data: string): AgentEvent {
  let value: unknown = JSON.parse(data);
  if (typeof value === "string") {
    value = JSON.parse(value);
  }
  return value as AgentEvent;
}
