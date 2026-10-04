import pytest
from langchain_core.messages import AIMessage

from decider.client import DeciderResult
from graph import deps
from graph.builder import build_graph
from graph.stream import initial_state, iter_graph_events


class FakeLLM:
    def __init__(self):
        self.calls = 0
        self.messages = []

    async def ainvoke(self, messages):
        self.calls += 1
        self.messages.append(messages)
        return AIMessage(content=f"output-{self.calls}")


class ScriptedDecider:
    def __init__(self, results):
        self.results = list(results)

    async def ask(self, state, questions):
        if not self.results:
            raise AssertionError(f"unexpected ask: {questions}")
        return self.results.pop(0)


def _choice(name: str, confidence: float) -> DeciderResult:
    return DeciderResult(
        answers={
            "workflow": {
                "type": "choice",
                "choice": name,
                "probabilities": {name: confidence},
                "confidence": confidence,
            }
        },
        latency_ms=5.0,
        model="fake",
    )


def _grade(
    fulfils: float, grounded: float = 0.9, premature: float = 0.1, fault: str = "none"
) -> DeciderResult:
    return DeciderResult(
        answers={
            "fulfils": {"type": "noul", "noul": fulfils},
            "grounded": {"type": "noul", "noul": grounded},
            "quality": {
                "type": "score",
                "score": 2.0,
                "confidence": 0.8,
                "legend": {"0": "poor", "1": "ok", "2": "good"},
                "probabilities": {"2": 0.8},
            },
            "premature": {"type": "noul", "noul": premature},
            "fault": {
                "type": "choice",
                "choice": fault,
                "confidence": 0.9,
                "probabilities": {fault: 0.9, **({"none": 0.1} if fault != "none" else {"invents_facts": 0.1})},
            },
        },
        latency_ms=7.0,
        model="fake",
    )


def _patch_decider(monkeypatch, results):
    scripted = ScriptedDecider(results)
    monkeypatch.setattr(deps, "get_decider", lambda: scripted)
    return scripted


@pytest.fixture
def llm(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr(deps, "get_llm", lambda: fake)
    return fake


@pytest.mark.asyncio
async def test_confident_route_runs_workflow_and_passes(monkeypatch, llm):
    _patch_decider(monkeypatch, [_choice("summarize", 0.9), _grade(0.91)])
    result = await build_graph().ainvoke(initial_state("Summarise this note."))
    assert result["workflow"] == "summarize"
    assert result["output"] == "output-1"
    assert result["verdict"]["passed"] is True
    assert result["verdict"]["quality_breakdown"] == [{"label": "good", "probability": 0.8}]
    # Second LLM call is the explanation of the grades.
    assert result["explanation"] == "output-2"
    assert llm.calls == 2
    assert "fulfils: 0.91" in llm.messages[1][1].content


@pytest.mark.asyncio
async def test_low_confidence_clarifies_without_llm(monkeypatch, llm):
    _patch_decider(monkeypatch, [_choice("summarize", 0.2)])
    result = await build_graph().ainvoke(initial_state("hello"))
    assert result["verdict"] is None
    assert result["explanation"] is None
    assert "summarise" in result["output"]
    assert llm.calls == 0


@pytest.mark.asyncio
async def test_failed_grade_retries_the_same_workflow_once(monkeypatch, llm):
    _patch_decider(monkeypatch, [_choice("create", 0.95), _grade(0.1), _grade(0.95)])
    result = await build_graph().ainvoke(initial_state("Write a haiku about rain."))
    assert result["output"] == "output-2"
    assert result["verdict"]["passed"] is True
    assert result["retries"] == 1
    assert result["explanation"] == "output-3"
    assert llm.calls == 3
    assert any("does not do what the user asked" in m.content for m in llm.messages[1])


@pytest.mark.asyncio
async def test_stream_emits_node_timing_and_decider_detail(monkeypatch, llm):
    _patch_decider(monkeypatch, [_choice("extract", 0.88), _grade(0.7, 0.2), _grade(0.7, 0.2)])
    # Second grade still fails; retries is then 1 so the graph stops.
    events = [event async for event in iter_graph_events("Pull the amounts out.")]
    types = [event["type"] for event in events]
    assert types[0] == "node_start"
    assert "decider" in types
    assert types[-1] == "done"
    ends = [event for event in events if event["type"] == "node_end"]
    assert [event["node"] for event in ends] == [
        "route",
        "extract",
        "evaluate",
        "extract",
        "evaluate",
        "explain",
        "finalize",
    ]
    assert all(event["ms"] >= 0 for event in ends)
    done = events[-1]
    assert done["verdict"]["passed"] is False
    assert done["workflow"] == "extract"
    assert done["explanation"] == "output-3"
    # The answer is sent before the explanation call starts.
    result = next(event for event in events if event["type"] == "result")
    assert result["output"] == "output-2"
    assert result["verdict"]["passed"] is False
    explain_end = next(e for e in ends if e["node"] == "explain")
    assert events.index(result) < events.index(explain_end)
    assert llm.calls == 3
    decider = [event for event in events if event["type"] == "decider"]
    assert decider[0]["node"] == "route"
    assert decider[1]["answers"]["fulfils"]["noul"] == 0.7
