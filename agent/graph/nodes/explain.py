from langchain_core.messages import HumanMessage, SystemMessage

from graph import deps
from graph.nodes._llm_turn import message_text
from graph.state import AgentState
from prompts.loader import load_prompt


async def explain(state: AgentState) -> dict:
    verdict = state.get("verdict")
    if not verdict:
        return {"explanation": None}

    # The answer is final here. Send it now so the UI does not wait on the explanation.
    await deps.emit(
        "result",
        {"output": state["output"], "verdict": verdict, "workflow": state.get("workflow")},
    )

    messages = [
        SystemMessage(content=load_prompt("explain")),
        HumanMessage(content=_evaluation_text(state, verdict)),
    ]
    await deps.emit("llm", {"node": "explain", "model": deps.model_name()})
    result = await deps.get_llm().ainvoke(messages)
    return {"explanation": message_text(result.content).strip()}


def _evaluation_text(state: AgentState, verdict: dict) -> str:
    breakdown = "\n".join(
        f"  - {row['label']}: {row['probability']:.2f}"
        for row in verdict.get("quality_breakdown", [])
    )
    return (
        f"User request:\n{state['input']}\n\n"
        f"Output:\n{state['output']}\n\n"
        "Evaluator results:\n"
        f"- fulfils: {verdict['fulfils']:.2f}\n"
        f"- grounded: {verdict['grounded']:.2f}\n"
        f"- quality: {verdict['quality']:.2f} "
        f"(confidence {verdict.get('quality_confidence', 0.0):.2f})\n"
        f"{breakdown}"
    )
