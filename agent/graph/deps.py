from decider.client import DeciderClient
from config import settings
from graph.llm import build_llm

_decider: DeciderClient | None = None
_llm = None


def get_decider() -> DeciderClient:
    global _decider
    if _decider is None or _decider.base_url != settings.decider_url.rstrip("/"):
        _decider = DeciderClient(settings.decider_url)
    return _decider


def get_llm():
    global _llm
    if _llm is None:
        _llm = build_llm()
    return _llm


def model_name() -> str:
    return settings.llm_model_id


async def emit(name: str, data: dict) -> None:
    from langchain_core.callbacks import adispatch_custom_event

    await adispatch_custom_event(name, data)
