import json
import os
import pytest

os.environ["GOOGLE_API_KEY"] = ""

from backend.app.services import evaluator


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FailingLLM:
    def invoke(self, messages):
        raise RuntimeError("quota exhausted")


class ScoringLLM:
    def invoke(self, messages):
        return FakeResponse(json.dumps({
            "coverage": 90,
            "hallucination": 80,
            "design": 70,
            "engineering": 60,
            "qa": 50,
            "prototype": 40,
            "repetition": 100,
            "format": 100,
            "reasoning": "Fallback judge model scored successfully."
        }))


def test_judge_uses_only_configured_judge_model(monkeypatch):
    monkeypatch.setattr(evaluator.settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(evaluator.settings, "JUDGE_MODEL", "gemini-2.5-pro")
    monkeypatch.setattr(evaluator.settings, "GEMINI_MODEL", "gemini-2.5-flash")

    requested_models = []

    def fake_get_llm(model_name, **kwargs):
        requested_models.append(model_name)
        return ScoringLLM()

    monkeypatch.setattr(evaluator, "get_llm", fake_get_llm)

    scores = evaluator.LLMJudge().evaluate(
        problem="Problem",
        solution="Solution",
        goals="Goals",
        template="## Template",
        prd="Generated PRD",
    )

    assert requested_models == ["gemini-2.5-pro"]
    assert scores["coverage"] == 90.0
    assert scores["final_score"] == 72.5
    assert "Fallback judge model scored successfully" in scores["reasoning"]


def test_judge_raises_when_all_models_fail(monkeypatch):
    monkeypatch.setattr(evaluator.settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(evaluator.settings, "JUDGE_MODEL", "gemini-2.5-pro")
    monkeypatch.setattr(evaluator.settings, "GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setattr(evaluator, "get_llm", lambda model_name, **kwargs: FailingLLM())
    monkeypatch.setattr(evaluator, "invoke_with_retry", lambda llm, messages: llm.invoke(messages))

    with pytest.raises(RuntimeError) as exc_info:
        evaluator.LLMJudge().evaluate(
            problem="Problem",
            solution="Solution",
            goals="Goals",
            template="## Template",
            prd="Generated PRD",
        )

    message = str(exc_info.value)
    assert "gemini-2.5-pro" in message
    assert "gemini-2.5-flash" not in message


def test_ollama_judge_uses_local_model_and_json(monkeypatch):
    monkeypatch.setattr(evaluator.settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(evaluator.settings, "OLLAMA_JUDGE_MODEL", "local-judge")
    requested = []

    def fake_get_llm(model_name, **kwargs):
        requested.append((model_name, kwargs))
        return ScoringLLM()

    monkeypatch.setattr(evaluator, "get_llm", fake_get_llm)
    scores = evaluator.LLMJudge().evaluate("Problem", "Solution", "Goals", "Template", "PRD")
    assert scores["final_score"] == 72.5
    assert requested == [("local-judge", {
        "max_tokens": evaluator.settings.JUDGE_MAX_TOKENS,
        "temperature": 0.0,
        "response_mime_type": "application/json",
    })]
