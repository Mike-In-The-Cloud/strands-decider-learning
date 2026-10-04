from config import settings
from graph.state import AgentState
from graph.workflows import WORKFLOWS


def after_route(state: AgentState) -> str:
    workflow = state.get("workflow")
    confident = state.get("route_confidence", 0.0) >= settings.route_confidence_min
    if not confident or workflow not in WORKFLOWS:
        return "clarify"
    return str(workflow)


def after_evaluate(state: AgentState) -> str:
    """Retry the chosen workflow while retries remain, else explain the grades.

    `retries` counts completed revision attempts. It is 0 on the first
    evaluation, then incremented by the workflow node when it runs with
    feedback. `max_retries` is how many revisions are allowed.
    """
    verdict = state.get("verdict") or {}
    workflow = state.get("workflow")
    if verdict.get("passed"):
        return "explain"
    if state.get("retries", 0) >= settings.max_retries or workflow not in WORKFLOWS:
        return "explain"
    return str(workflow)
