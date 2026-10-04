import type { TraceNode } from "../types";
import { TraceTimeline } from "./TraceTimeline";

export function Sidebar({ trace, running }: { trace: TraceNode[]; running: boolean }) {
  return (
    <aside className="sidebar">
      <header>
        <p className="kicker">Run</p>
        <h2>What the agent did</h2>
      </header>
      <TraceTimeline trace={trace} running={running} />
    </aside>
  );
}
