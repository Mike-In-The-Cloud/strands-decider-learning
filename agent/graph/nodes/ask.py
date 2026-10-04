from langchain_core.messages import HumanMessage, SystemMessage

from graph.nodes._llm_turn import stream_llm
from graph.state import AgentState
from prompts.loader import load_prompt


async def ask(state: AgentState) -> dict:
    messages = [
        SystemMessage(content=load_prompt("ask")),
        HumanMessage(content=_ask_text(state)),
    ]
    text = await stream_llm(messages, "ask")
    return {"output": text.strip()}


def _ask_text(state: AgentState) -> str:
    return (
        f"User request:\n{state['input']}\n\n"
        f"Draft answer (not sent to the user):\n{state['output']}\n\n"
        f"What went wrong:\n{state.get('feedback') or ''}"
    )
