import { ChatPanel } from "./components/ChatPanel";
import { Sidebar } from "./components/Sidebar";
import { useAgentStream } from "./hooks/useAgentStream";

export function App() {
  const { messages, trace, running, error, send } = useAgentStream();
  return (
    <div className="app">
      <ChatPanel messages={messages} running={running} error={error} onSend={send} />
      <Sidebar trace={trace} running={running} />
    </div>
  );
}
