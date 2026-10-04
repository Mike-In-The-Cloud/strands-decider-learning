from typing import Any, TypedDict


class AgentState(TypedDict):
    input: str
    workflow: str | None
    route_confidence: float
    output: str
    feedback: str | None
    retries: int
    verdict: dict[str, Any] | None
    explanation: str | None
