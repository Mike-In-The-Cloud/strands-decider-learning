from graph.edges import after_evaluate, after_route


def _state(**overrides):
    base = {
        "input": "hello",
        "workflow": "summarize",
        "route_confidence": 0.9,
        "output": "",
        "feedback": None,
        "retries": 0,
        "verdict": None,
    }
    base.update(overrides)
    return base


def test_after_route_picks_workflow_when_confident():
    assert after_route(_state(workflow="extract", route_confidence=0.61)) == "extract"


def test_after_route_clarifies_when_unsure_or_unknown():
    assert after_route(_state(route_confidence=0.59)) == "clarify"
    assert after_route(_state(workflow="nope", route_confidence=0.99)) == "clarify"


def test_after_evaluate_explains_or_retries_once():
    assert after_evaluate(_state(verdict={"passed": True}, retries=0)) == "explain"
    assert after_evaluate(_state(verdict={"passed": False}, retries=0)) == "summarize"
    assert after_evaluate(_state(verdict={"passed": False}, retries=1, workflow="create")) == "explain"
