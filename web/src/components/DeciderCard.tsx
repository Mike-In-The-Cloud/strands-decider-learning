import type { Answer } from "../types";

export function DeciderCard({
  answers,
  latencyMs,
}: {
  answers: Record<string, Answer>;
  latencyMs: number;
}) {
  return (
    <div className="decider">
      <div className="meta">decider {Math.round(latencyMs)}ms</div>
      {Object.entries(answers).map(([name, answer]) => (
        <div key={name} className="decider-q">
          <div className="decider-name">{name}</div>
          {answer.type === "noul" && <Meter label="true" value={answer.noul} />}
          {answer.type === "choice" && (
            <>
              <div className="pick">
                {answer.choice} <span>{answer.confidence.toFixed(2)}</span>
              </div>
              {ranked(answer.probabilities).map(([label, value]) => (
                <Meter key={label} label={label} value={value} />
              ))}
            </>
          )}
          {answer.type === "score" && (
            <>
              <div className="pick">
                {answer.score.toFixed(2)} <span>conf {answer.confidence.toFixed(2)}</span>
              </div>
              {ranked(answer.probabilities).map(([index, value]) => (
                <Meter key={index} label={answer.legend?.[index] ?? index} value={value} stacked />
              ))}
            </>
          )}
        </div>
      ))}
    </div>
  );
}

function ranked(probabilities: Record<string, number>) {
  return Object.entries(probabilities).sort((a, b) => b[1] - a[1]);
}

function Meter({
  label,
  value,
  stacked = false,
}: {
  label: string;
  value: number;
  stacked?: boolean;
}) {
  const width = `${Math.max(0, Math.min(1, value)) * 100}%`;
  const bar = (
    <>
      <span className="track">
        <span className="fill" style={{ width }} />
      </span>
      <span className="num">{value.toFixed(2)}</span>
    </>
  );
  if (stacked) {
    return (
      <div className="meter meter-stacked">
        <div className="meter-label">{label}</div>
        <div className="meter-bar">{bar}</div>
      </div>
    );
  }
  return (
    <div className="meter">
      <span>{label}</span>
      {bar}
    </div>
  );
}
