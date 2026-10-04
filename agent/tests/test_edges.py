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


def test_after_evaluate_maps_action_to_next_node():
    assert after_evaluate(_state(verdict={"action": "explain"})) == "explain"
    assert after_evaluate(_state(verdict={"action": "revise"})) == "summarize"
    assert after_evaluate(_state(verdict={"action": "revise"}, workflow="nope")) == "explain"
    assert after_evaluate(_state(verdict={"action": "ask"})) == "ask"
    assert after_evaluate(_state(verdict=None)) == "explain"
