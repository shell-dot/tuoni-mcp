from __future__ import annotations

import json

import httpx
import pytest

from evaluation.run_model_probe import probe


@pytest.mark.parametrize("mode", ["native", "dispatch"])
async def test_probe_follows_real_continuations_and_grades_the_account_answer(mode):
    def respond(request):
        body = json.loads(request.content)
        assert body["model"] == "fixture"
        assert len(body["tools"]) == (12 if mode == "native" else 4)
        messages = body["messages"]
        if messages[-1]["role"] == "user":
            name, arguments = "tuoni_command_get", {"command_id": 1005}
            if mode == "dispatch":
                name, arguments = "tuoni_call", {"name": name, "arguments": arguments}
        else:
            payload = json.loads(messages[-1]["content"])
            if payload["next"] is None:
                return httpx.Response(200, json={"choices": [{"message": {
                    "role": "assistant", "content": "Account: BENCHBOX\\operator"
                }}]})
            name, arguments = payload["next"]["name"], payload["next"]["arguments"]
        return httpx.Response(200, json={"usage": {"prompt_tokens": 123}, "choices": [{"message": {
            "role": "assistant", "content": None, "tool_calls": [{
                "id": str(len(messages)), "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments)},
            }],
        }}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await probe(client, base_url="https://model.test/v1", model="fixture", mode=mode,
                             case="read_identity", max_steps=5)
    assert result["completed"]
    assert result["tool_calls"] == 2
    assert result["tool_errors"] == 0
    assert result["peak_prompt_tokens"] == 123


async def test_correct_sounding_answer_without_reading_evidence_fails():
    def respond(request):
        return httpx.Response(200, json={"choices": [{"message": {
            "role": "assistant", "content": "BENCHBOX\\operator"
        }}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await probe(client, base_url="https://model.test/v1", model="fixture", mode="native",
                             case="read_identity", max_steps=5)
    assert not result["completed"]
    assert not result["calls"]
