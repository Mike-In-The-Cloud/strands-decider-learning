from langchain_core.messages import HumanMessage, SystemMessage

from graph import deps
from graph.state import AgentState
from prompts.loader import load_prompt


async def run_llm_workflow(state: AgentState, name: str) -> dict:
    messages = [
        SystemMessage(content=load_prompt(name)),
        HumanMessage(content=state["input"]),
    ]
    feedback = state.get("feedback")
    if feedback:
        messages.append(HumanMessage(content=feedback))

    await deps.emit("llm", {"node": name, "model": deps.model_name()})
    result = await deps.get_llm().ainvoke(messages)
    # A failed verdict means this run is a revision, even if feedback text is empty.
    revising = bool(feedback) or (state.get("verdict") or {}).get("passed") is False
    return {
        "output": message_text(result.content),
        "workflow": name,
        "retries": state["retries"] + (1 if revising else 0),
    }


def message_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(str(block.get("text", "")))
            else:
                text = getattr(block, "text", None)
                parts.append(str(text if text is not None else block))
        return "".join(parts)
    return str(content)
