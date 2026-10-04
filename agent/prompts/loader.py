from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROMPTS_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Question:
    type: str
    instructions: str
    criteria: dict[str, str] | list[str] | None
    fail: str | None


def load_prompt(name: str) -> str:
    return _body(_read(PROMPTS_DIR / f"{name}.md"))


def load_question(name: str) -> Question:
    raw = _read(PROMPTS_DIR / "decider" / f"{name}.md")
    meta, instructions = _split_frontmatter(raw)
    if not meta:
        raise ValueError(f"{name}.md is missing YAML frontmatter")
    qtype = meta.get("type")
    if qtype not in {"noul", "choice", "score"}:
        raise ValueError(f"{name}.md has unsupported question type {qtype!r}")
    criteria = _normalize_criteria(meta.get("criteria"))
    fail = meta.get("fail")
    return Question(
        type=qtype,
        instructions=instructions,
        criteria=criteria,
        fail=str(fail) if fail else None,
    )


def question_payload(question: Question) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": question.type,
        "instructions": question.instructions,
    }
    if question.criteria is not None:
        payload["criteria"] = question.criteria
    return payload


def _normalize_criteria(criteria: Any) -> dict[str, str] | list[str] | None:
    if criteria is None:
        return None
    if isinstance(criteria, dict):
        return {_yaml_key(key): str(value) for key, value in criteria.items()}
    if isinstance(criteria, list):
        return [str(item) for item in criteria]
    raise ValueError("question criteria must be a mapping or a list")


def _yaml_key(key: object) -> str:
    # YAML 1.1 reads bare true/false as booleans. The decider API wants strings.
    if key is True:
        return "true"
    if key is False:
        return "false"
    return str(key)


def _read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def _body(text: str) -> str:
    _, body = _split_frontmatter(text)
    return body


def _split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    stripped = text.lstrip("\ufeff")
    if not stripped.startswith("---"):
        return None, stripped.strip()
    parts = stripped.split("---", 2)
    if len(parts) < 3:
        raise ValueError("prompt frontmatter was not closed")
    meta = yaml.safe_load(parts[1]) or {}
    if not isinstance(meta, dict):
        raise ValueError("prompt frontmatter must be a mapping")
    return meta, parts[2].strip()
