from graph.state import AgentState
from prompts.loader import load_prompt


async def clarify(state: AgentState) -> dict:
    return {"output": load_prompt("clarify"), "verdict": None}
