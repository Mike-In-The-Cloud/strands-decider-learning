export type NoulAnswer = { type: "noul"; noul: number };
export type ChoiceAnswer = {
  type: "choice";
  choice: string;
  probabilities: Record<string, number>;
  confidence: number;
};
export type ScoreAnswer = {
  type: "score";
  score: number;
  legend?: Record<string, string>;
  probabilities: Record<string, number>;
  confidence: number;
};
export type Answer = NoulAnswer | ChoiceAnswer | ScoreAnswer;

export type FaultLabel = "none" | "ignores_task" | "invents_facts" | "unfinished" | "wrong_format";
export type EvalAction = "ask" | "revise" | "explain";

export type Verdict = {
  action: EvalAction;
  passed: boolean;
  fulfils: number;
  grounded: number;
  premature: number;
  quality: number;
  quality_confidence: number;
  quality_breakdown?: { label: string; probability: number }[];
  reason: { fault: FaultLabel; confidence: number; breakdown: { label: string; probability: number }[] };
};

export type AgentEvent = {
  type?: string;
  node?: string;
  run_id?: string;
  ms?: number;
  answers?: Record<string, Answer>;
  latency_ms?: number;
  model?: string;
  output?: string;
  verdict?: Verdict | null;
  workflow?: string | null;
  explanation?: string | null;
  error?: string;
  message?: string;
};

export type TraceNode = {
  runId: string;
  node: string;
  ms?: number;
  model?: string;
  decider?: { latencyMs: number; answers: Record<string, Answer> };
};

export type ChatMessage = {
  role: "user" | "assistant";
  text: string;
  workflow?: string | null;
  verdict?: Verdict | null;
  explanation?: string | null;
  explaining?: boolean;
};
