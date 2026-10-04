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
    """Branch on the evaluator's decision. The policy lives in evaluate.py."""
    verdict = state.get("verdict") or {}
    action = verdict.get("action")
    workflow = state.get("workflow")
    if action == "ask":
        return "ask"
    if action == "revise" and workflow in WORKFLOWS:
        return str(workflow)
    return "explain"
