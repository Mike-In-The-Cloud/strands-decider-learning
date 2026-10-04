import type { TraceNode } from "../types";
import { DeciderCard } from "./DeciderCard";

export function TraceTimeline({ trace, running }: { trace: TraceNode[]; running: boolean }) {
  const finished = trace.filter((item) => item.ms !== undefined);
  const max = Math.max(1, ...finished.map((item) => item.ms ?? 0));
  const total = finished.reduce((sum, item) => sum + (item.ms ?? 0), 0);

  if (trace.length === 0) {
    return <p className="empty">{running ? "Starting…" : "No run yet."}</p>;
  }

  return (
    <ol className="timeline">
      {trace.map((item) => (
        <li key={item.runId}>
          <div className="node-row">
            <span className="node-name">{item.node}</span>
            <span className="node-ms">{item.ms === undefined ? "…" : `${Math.round(item.ms)}ms`}</span>
          </div>
          <div className="bar">
            <span style={{ width: item.ms === undefined ? "8%" : `${(item.ms / max) * 100}%` }} />
          </div>
          {item.model && <div className="meta">{shortModel(item.model)}</div>}
          {item.decider && <DeciderCard answers={item.decider.answers} latencyMs={item.decider.latencyMs} />}
        </li>
      ))}
      <li className="total">
        <span>total</span>
        <span>{finished.length === 0 ? "…" : `${Math.round(total)}ms`}</span>
      </li>
    </ol>
  );
}

function shortModel(model: string) {
  const parts = model.split(".");
  return parts[parts.length - 1] ?? model;
}
