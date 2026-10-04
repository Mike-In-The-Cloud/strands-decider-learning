import time
from typing import Any

from graph.builder import get_graph
from graph.state import AgentState


def initial_state(prompt: str) -> AgentState:
    return {
        "input": prompt,
        "workflow": None,
        "route_confidence": 0.0,
        "output": "",
        "feedback": None,
        "retries": 0,
        "verdict": None,
        "explanation": None,
    }


async def iter_graph_events(prompt: str):
    started: dict[str, float] = {}
    final: dict[str, Any] | None = None
    graph = get_graph()

    async for event in graph.astream_events(initial_state(prompt), version="v2"):
        kind = event.get("event")
        name = event.get("name")
        meta = event.get("metadata") or {}
        node = meta.get("langgraph_node")
        run_id = str(event.get("run_id", ""))
        data = event.get("data") or {}

        if kind == "on_custom_event":
            payload = dict(data)
            payload["type"] = name
            yield payload
            continue

        if node and name == node and kind == "on_chain_start":
            started[run_id] = time.perf_counter()
            yield {"type": "node_start", "node": node, "run_id": run_id}
            continue

        if node and name == node and kind == "on_chain_end":
            t0 = started.pop(run_id, None)
            ms = 0.0 if t0 is None else (time.perf_counter() - t0) * 1000
            yield {
                "type": "node_end",
                "node": node,
                "run_id": run_id,
                "ms": round(ms, 1),
            }
            continue

        output = data.get("output") if kind == "on_chain_end" else None
        if isinstance(output, dict) and "input" in output and "output" in output:
            final = output

    yield {
        "type": "done",
        "output": "" if final is None else final.get("output", ""),
        "verdict": None if final is None else final.get("verdict"),
        "workflow": None if final is None else final.get("workflow"),
        "explanation": None if final is None else final.get("explanation"),
    }
