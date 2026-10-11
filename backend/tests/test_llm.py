import json
import httpx
import pytest
from langchain_ollama import ChatOllama
from backend.app.config import Settings
from backend.app.services import llm


def test_defaults_use_ollama(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    config = Settings(_env_file=None)
    assert config.provider == "ollama"
    assert config.generator_model == config.OLLAMA_MODEL
    assert config.judge_model == config.OLLAMA_JUDGE_MODEL


def test_ollama_request_format_and_timeout(monkeypatch):
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(llm.settings, "GOOGLE_API_KEY", "")
    monkeypatch.setattr(llm.settings, "OLLAMA_TIMEOUT_SECONDS", 42)
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={
            "model": "local-judge", "message": {"role": "assistant", "content": '{"coverage": 90}'},
            "done": True, "prompt_eval_count": 12, "eval_count": 5,
        })

    model = llm.get_llm("local-judge", max_tokens=123, temperature=0, response_mime_type="application/json")
    assert isinstance(model, ChatOllama)
    assert model.client_kwargs["timeout"] == 42
    model._client._client = httpx.Client(base_url=llm.settings.OLLAMA_BASE_URL, transport=httpx.MockTransport(handle))
    response = model.invoke("Return JSON scores")
    assert response.usage_metadata["total_tokens"] == 17
    assert requests[0]["model"] == "local-judge"
    assert requests[0]["format"] == "json"
    assert requests[0]["think"] is False
    assert requests[0]["options"]["num_predict"] == 123
    assert requests[0]["options"]["temperature"] == 0


def test_unknown_provider_does_not_fall_back_to_gemini(monkeypatch):
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "olama")
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        llm.get_llm()
