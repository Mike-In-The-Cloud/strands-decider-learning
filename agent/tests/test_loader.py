from graph.workflows import WORKFLOWS
from prompts.loader import load_prompt, load_question, question_payload


def test_workflow_prompts_are_nonempty():
    for name in (*WORKFLOWS, "clarify", "ask"):
        body = load_prompt(name)
        assert body
        assert "---" not in body.splitlines()[0]


def test_route_options_match_workflows():
    question = load_question("route")
    assert question.type == "choice"
    assert set(question.criteria) == set(WORKFLOWS)
    payload = question_payload(question)
    assert payload["instructions"]
    assert "fail" not in payload


def test_eval_questions():
    fulfils = load_question("eval_fulfils")
    grounded = load_question("eval_grounded")
    quality = load_question("eval_quality")
    assert fulfils.type == "noul" and fulfils.fail
    assert grounded.type == "noul" and set(grounded.criteria) == {"true", "false"}
    assert quality.type == "score" and quality.criteria == [
        "poor: misses the task, is empty, or is unusable",
        "ok: does the task with clear gaps",
        "good: does the task clearly and completely",
    ]
    assert question_payload(quality)["criteria"][0].startswith("poor")

    premature = load_question("eval_premature")
    fault = load_question("eval_fault")
    assert premature.type == "noul" and premature.fail
    assert set(premature.criteria) == {"true", "false"}
    assert fault.type == "choice"
    assert set(fault.criteria) == {"none", "ignores_task", "invents_facts", "unfinished", "wrong_format"}
    assert "fail" not in question_payload(fault)


def test_graph_code_has_no_prompt_prose():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "graph"
    banned = ("You condense", "You classify", "You write", "You extract", "Which single workflow")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for phrase in banned:
            assert phrase not in text, f"{path.name} contains prompt prose"
