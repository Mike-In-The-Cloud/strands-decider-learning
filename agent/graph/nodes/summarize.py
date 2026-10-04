from graph.nodes._llm_turn import run_llm_workflow
from graph.state import AgentState


async def summarize(state: AgentState) -> dict:
    return await run_llm_workflow(state, "summarize")
