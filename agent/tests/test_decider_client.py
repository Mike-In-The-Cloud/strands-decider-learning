import json

import httpx
import pytest

from decider.client import DeciderClient


def _client(handler) -> DeciderClient:
    return DeciderClient(
        "http://decider.test",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


@pytest.mark.asyncio
async def test_ask_posts_systemone_and_parses_answers():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "model": "strands-decider-2B-hobson-v19",
                "answers": {
                    "workflow": {
                        "type": "choice",
                        "choice": "billing",
                        "probabilities": {"billing": 0.8, "sales": 0.2},
                        "confidence": 0.6,
                    },
                    "is_urgent": {"type": "noul", "noul": 0.83},
                    "mood": {
                        "type": "score",
                        "score": 1.1,
                        "legend": {"0": "calm", "1": "frustrated"},
                        "probabilities": {"0": 0.4, "1": 0.6},
                        "confidence": 0.5,
                    },
                },
                "usage": {"input_tokens": 10, "output_tokens": 1},
                "latency_ms": 42.5,
            },
        )

    result = await _client(handler).ask(
        "Help",
        {
            "workflow": {
                "type": "choice",
                "instructions": "Which team?",
                "criteria": {"billing": "money", "sales": "pricing"},
            },
            "is_urgent": {"type": "noul", "instructions": "Urgent?"},
        },
    )

    assert seen["path"] == "/v1/systemone"
    assert seen["body"]["state"] == "Help"
    assert result.model.endswith("v19")
    assert result.latency_ms == 42.5
    assert result.answers["workflow"]["choice"] == "billing"
    assert result.answers["is_urgent"]["noul"] == 0.83
    assert result.answers["mood"]["score"] == 1.1


@pytest.mark.asyncio
async def test_ask_rejects_empty_state():
    with pytest.raises(ValueError):
        await _client(lambda request: httpx.Response(500)).ask("  ", {"q": {"type": "noul", "instructions": "x"}})
