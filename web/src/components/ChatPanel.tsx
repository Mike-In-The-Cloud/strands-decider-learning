import { useState } from "react";
import type { ChatMessage } from "../types";

const EXAMPLES = [
  {
    label: "Summarise",
    prompt:
      "Summarise this: The warehouse on Pier 4 missed two shipments on Monday. Client Northwind is waiting on invoice 1842 for £4,200, due 3 March.",
  },
  {
    label: "Classify",
    prompt: "What is the sentiment and intent? I have been waiting three days and nobody has answered my payout ticket.",
  },
  {
    label: "Create",
    prompt: "Write a four-line poem about a late train and a paper cup of coffee.",
  },
  {
    label: "Extract",
    prompt:
      "Extract the structured fields: Ada Lovelace met Charles Babbage on 5 June 1833. The grant was £1,500 and the report was due 12 August.",
  },
];

export function ChatPanel({
  messages,
  running,
  error,
  onSend,
}: {
  messages: ChatMessage[];
  running: boolean;
  error: string | null;
  onSend: (prompt: string) => void;
}) {
  const [draft, setDraft] = useState("");

  return (
    <main className="chat">
      <header>
        <p className="kicker">Decision agent</p>
        <h1>Four workflows, one small decider.</h1>
      </header>
      <div className="examples">
        {EXAMPLES.map((example) => (
          <button key={example.label} type="button" disabled={running} onClick={() => onSend(example.prompt)}>
            {example.label}
          </button>
        ))}
      </div>
      <div className="transcript">
        {messages.length === 0 && <p className="empty">Send a request. The decider picks the workflow, Haiku writes it, then the decider grades it.</p>}
        {messages.map((message, index) => (
          <article key={`${message.role}-${index}`} className={message.role}>
            <div className="who">{message.role === "user" ? "You" : message.workflow ?? "Agent"}</div>
            <pre>{message.text}</pre>
            {message.verdict && (
              <div className={message.verdict.passed ? "verdict pass" : "verdict fail"}>
                {message.verdict.passed ? "passed" : "returned after review"} · fulfils {message.verdict.fulfils.toFixed(2)} · grounded{" "}
                {message.verdict.grounded.toFixed(2)} · quality {message.verdict.quality.toFixed(2)}
              </div>
            )}
            {message.explaining && <div className="explanation pending">explaining the grades…</div>}
            {message.explanation && (
              <div className="explanation">
                <div className="who">why these grades · Haiku's reading of the decider</div>
                <pre>{message.explanation}</pre>
              </div>
            )}
          </article>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSend(draft);
          setDraft("");
        }}
      >
        <textarea
          value={draft}
          disabled={running}
          placeholder="Ask for a summary, a classification, a short piece of writing, or an extraction."
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              onSend(draft);
              setDraft("");
            }
          }}
        />
        <button type="submit" disabled={running || draft.trim().length === 0}>
          {running ? "Running" : "Send"}
        </button>
      </form>
    </main>
  );
}
