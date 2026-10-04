from graph import deps
from graph.state import AgentState
from prompts.loader import load_question, question_payload


async def route(state: AgentState) -> dict:
    question = load_question("route")
    result = await deps.get_decider().ask(
        state["input"],
        {"workflow": question_payload(question)},
    )
    answer = result.answers["workflow"]
    await deps.emit(
        "decider",
        {"node": "route", "latency_ms": result.latency_ms, "answers": result.answers},
    )
    return {
        "workflow": answer["choice"],
        "route_confidence": float(answer["confidence"]),
        "retries": 0,
        "feedback": None,
    }
