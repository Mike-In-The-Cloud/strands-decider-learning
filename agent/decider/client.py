import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class DeciderResult:
    answers: dict[str, dict[str, Any]]
    latency_ms: float
    model: str


class DeciderClient:
    """HTTP client for `POST /v1/systemone` on a `strands-decider serve` process."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 60.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = client

    async def ask(self, state: str, questions: dict[str, dict[str, Any]]) -> DeciderResult:
        if not state.strip():
            raise ValueError("decider state must not be empty")
        if not questions:
            raise ValueError("decider questions must not be empty")

        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self.timeout)
        started = time.perf_counter()
        try:
            response = await client.post(
                f"{self.base_url}/v1/systemone",
                json={"state": state, "questions": questions},
            )
            response.raise_for_status()
            body = response.json()
        finally:
            if owns_client:
                await client.aclose()

        elapsed_ms = (time.perf_counter() - started) * 1000
        return DeciderResult(
            answers=body["answers"],
            latency_ms=float(body.get("latency_ms", elapsed_ms)),
            model=str(body.get("model", "")),
        )
