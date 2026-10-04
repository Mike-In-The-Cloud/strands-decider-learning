import pytest

from graph import deps
from graph.nodes.evaluate import evaluate
from graph.stream import initial_state
from prompts.loader import load_question
from test_graph import _grade

FAULT_LABELS = {"none", "ignores_task", "invents_facts", "unfinished", "wrong_format"}


class RecordingDecider:
    def __init__(self, result):
        self.result = result
        self.questions = None

    async def ask(self, state, questions):
        self.questions = questions
        return self.result


@pytest.fixture(autouse=True)
def emitted(monkeypatch):
    events = []

    async def record(name, data):
        events.append((name, data))

    monkeypatch.setattr(deps, "emit", record)
    return events


async def _evaluate(monkeypatch, result, retries=0):
    decider = RecordingDecider(result)
    monkeypatch.setattr(deps, "get_decider", lambda: decider)
    state = initial_state("Write a haiku about rain.")
    state["output"] = "Rain taps the window / the kettle answers softly / morning finds its tea"
    state["retries"] = retries
    return await evaluate(state), decider


@pytest.mark.asyncio
async def test_passing_output_explains_and_asks_all_five_questions(monkeypatch, emitted):
    update, decider = await _evaluate(monkeypatch, _grade(0.9, 0.9, premature=0.1, fault="none"))
    verdict = update["verdict"]
    assert set(verdict) == {
        "action",
        "passed",
        "fulfils",
        "grounded",
        "premature",
        "quality",
        "quality_confidence",
        "quality_breakdown",
        "reason",
    }
    assert verdict["action"] == "explain"
    assert verdict["passed"] is True
    assert verdict["premature"] == 0.1
    assert set(verdict["reason"]) == {"fault", "confidence", "breakdown"}
    assert verdict["reason"]["fault"] == "none"
    assert update["feedback"] is None

    assert set(decider.questions) == {"fulfils", "grounded", "quality", "premature", "fault"}
    assert decider.questions["fault"]["type"] == "choice"
    assert set(decider.questions["fault"]["criteria"]) == FAULT_LABELS
    assert decider.questions["premature"]["type"] == "noul"

    assert [name for name, _ in emitted] == ["decider"]
    assert emitted[0][1]["node"] == "evaluate"
    assert set(emitted[0][1]["answers"]) == set(decider.questions)


@pytest.mark.asyncio
async def test_ungrounded_output_asks_and_names_the_fault(monkeypatch):
    update, _ = await _evaluate(monkeypatch, _grade(0.9, 0.2, fault="invents_facts"))
    verdict = update["verdict"]
    assert verdict["action"] == "ask"
    assert verdict["passed"] is False
    grounded = load_question("eval_grounded")
    fault = load_question("eval_fault")
    assert update["feedback"] == f"{grounded.fail} {fault.criteria['invents_facts']}"
    assert verdict["reason"] == {
        "fault": "invents_facts",
        "confidence": 0.9,
        "breakdown": [
            {"label": "invents_facts", "probability": 0.9},
            {"label": "none", "probability": 0.1},
        ],
    }


@pytest.mark.asyncio
async def test_premature_output_asks_even_when_passed(monkeypatch):
    update, _ = await _evaluate(monkeypatch, _grade(0.9, 0.9, premature=0.8))
    verdict = update["verdict"]
    assert verdict["action"] == "ask"
    assert verdict["passed"] is True
    premature = load_question("eval_premature")
    assert update["feedback"] == premature.fail
    assert load_question("eval_fulfils").fail not in update["feedback"]
    assert load_question("eval_grounded").fail not in update["feedback"]


@pytest.mark.asyncio
async def test_unfulfilled_output_revises_while_retries_remain(monkeypatch):
    update, _ = await _evaluate(monkeypatch, _grade(0.2, 0.9, premature=0.1), retries=0)
    verdict = update["verdict"]
    assert verdict["action"] == "revise"
    assert verdict["passed"] is False
    assert update["feedback"] == load_question("eval_fulfils").fail


@pytest.mark.asyncio
async def test_unfulfilled_output_explains_when_retries_exhausted(monkeypatch):
    update, _ = await _evaluate(monkeypatch, _grade(0.2, 0.9, premature=0.1), retries=1)
    verdict = update["verdict"]
    assert verdict["action"] == "explain"
    assert verdict["passed"] is False
    assert update["feedback"] is None


@pytest.mark.asyncio
async def test_ask_wins_over_revise_and_feedback_lists_failures_in_order(monkeypatch):
    update, _ = await _evaluate(monkeypatch, _grade(0.2, 0.2, premature=0.1, fault="ignores_task"))
    assert update["verdict"]["action"] == "ask"
    fulfils = load_question("eval_fulfils")
    grounded = load_question("eval_grounded")
    fault = load_question("eval_fault")
    assert update["feedback"] == f"{fulfils.fail} {grounded.fail} {fault.criteria['ignores_task']}"
