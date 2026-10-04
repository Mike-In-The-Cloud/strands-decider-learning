from config import settings
from graph import deps
from graph.state import AgentState
from prompts.loader import Question, load_question, question_payload

_EVALS = (
    ("fulfils", "eval_fulfils"),
    ("grounded", "eval_grounded"),
    ("quality", "eval_quality"),
    ("premature", "eval_premature"),
    ("fault", "eval_fault"),
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
    premature = float(result.answers["premature"]["noul"])
    quality = result.answers["quality"]
    reason = _reason(result.answers["fault"])
    action = _decision(fulfils, grounded, premature, state.get("retries", 0))
    passed = fulfils >= settings.eval_noul_min and grounded >= settings.eval_noul_min
    return {
        "verdict": {
            "action": action,
            "passed": passed,
            "fulfils": fulfils,
            "grounded": grounded,
            "premature": premature,
            "quality": float(quality["score"]),
            "quality_confidence": float(quality.get("confidence", 0.0)),
            "quality_breakdown": _breakdown(quality),
            "reason": reason,
        },
        "feedback": (
            None
            if action == "explain"
            else _feedback(loaded, fulfils, grounded, premature, reason["fault"])
        ),
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


def _decision(fulfils: float, grounded: float, premature: float, retries: int) -> str:
    """The only place the next step is decided; the decider just classifies."""
    minimum = settings.eval_noul_min
    if grounded < minimum or premature >= minimum:
        return "ask"
    if fulfils < minimum and retries < settings.max_retries:
        return "revise"
    return "explain"


def _reason(fault: dict) -> dict:
    # A choice answer keys `probabilities` by label, so `_breakdown` needs no legend.
    return {
        "fault": str(fault["choice"]),
        "confidence": float(fault.get("confidence", 0.0)),
        "breakdown": _breakdown(fault),
    }


def _feedback(
    loaded: dict[str, Question],
    fulfils: float,
    grounded: float,
    premature: float,
    fault: str,
) -> str:
    minimum = settings.eval_noul_min
    failing = (
        ("fulfils", fulfils < minimum),
        ("grounded", grounded < minimum),
        ("premature", premature >= minimum),
    )
    notes = [loaded[key].fail for key, failed in failing if failed and loaded[key].fail]
    if fault != "none":
        notes.append(loaded["fault"].criteria[fault])
    return " ".join(notes)
