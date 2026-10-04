from config import settings
from graph import deps
from graph.state import AgentState
from prompts.loader import Question, load_question, question_payload

_EVALS = (
    ("fulfils", "eval_fulfils"),
    ("grounded", "eval_grounded"),
    ("quality", "eval_quality"),
)


async def evaluate(state: AgentState) -> dict:
    loaded = {key: load_question(name) for key, name in _EVALS}
    result = await deps.get_decider().ask(
        _state_text(state),
        {key: question_payload(question) for key, question in loaded.items()},
    )
    await deps.emit(
        "decider",
        {"node": "evaluate", "latency_ms": result.latency_ms, "answers": result.answers},
    )

    fulfils = float(result.answers["fulfils"]["noul"])
    grounded = float(result.answers["grounded"]["noul"])
    quality = result.answers["quality"]
    passed = fulfils >= settings.eval_noul_min and grounded >= settings.eval_noul_min
    return {
        "verdict": {
            "passed": passed,
            "fulfils": fulfils,
            "grounded": grounded,
            "quality": float(quality["score"]),
            "quality_confidence": float(quality.get("confidence", 0.0)),
            "quality_breakdown": _breakdown(quality),
        },
        "feedback": None if passed else _feedback(loaded, fulfils, grounded),
    }


def _state_text(state: AgentState) -> str:
    return f"User request:\n{state['input']}\n\nWorkflow output:\n{state['output']}"


def _breakdown(quality: dict) -> list[dict[str, float | str]]:
    legend = quality.get("legend") or {}
    probabilities = quality.get("probabilities") or {}
    rows = [
        {"label": str(legend.get(index, index)), "probability": float(p)}
        for index, p in probabilities.items()
    ]
    return sorted(rows, key=lambda row: row["probability"], reverse=True)


def _feedback(loaded: dict[str, Question], fulfils: float, grounded: float) -> str:
    notes: list[str] = []
    if fulfils < settings.eval_noul_min and loaded["fulfils"].fail:
        notes.append(loaded["fulfils"].fail)
    if grounded < settings.eval_noul_min and loaded["grounded"].fail:
        notes.append(loaded["grounded"].fail)
    return " ".join(notes)
