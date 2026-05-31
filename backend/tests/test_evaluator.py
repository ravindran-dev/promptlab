import json
import os

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


def test_judge_uses_generation_model_when_primary_judge_model_fails(monkeypatch):
    monkeypatch.setattr(evaluator.settings, "JUDGE_MODEL", "gemini-2.5-pro")
    monkeypatch.setattr(evaluator.settings, "GEMINI_MODEL", "gemini-2.5-flash")

    requested_models = []

    def fake_get_llm(model_name, **kwargs):
        requested_models.append(model_name)
        if model_name == "gemini-2.5-pro":
            return FailingLLM()
        return ScoringLLM()

    monkeypatch.setattr(evaluator, "get_llm", fake_get_llm)

    scores = evaluator.LLMJudge().evaluate(
        problem="Problem",
        solution="Solution",
        goals="Goals",
        template="## Template",
        prd="Generated PRD",
    )

    assert requested_models == ["gemini-2.5-pro", "gemini-2.5-flash"]
    assert scores["coverage"] == 90.0
    assert scores["final_score"] == 72.5
    assert "Fallback judge model scored successfully" in scores["reasoning"]


def test_judge_returns_fallback_only_after_all_models_fail(monkeypatch):
    monkeypatch.setattr(evaluator.settings, "JUDGE_MODEL", "gemini-2.5-pro")
    monkeypatch.setattr(evaluator.settings, "GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setattr(evaluator, "get_llm", lambda model_name: FailingLLM())

    scores = evaluator.LLMJudge().evaluate(
        problem="Problem",
        solution="Solution",
        goals="Goals",
        template="## Template",
        prd="Generated PRD",
    )

    assert scores["final_score"] == 50.0
    assert "gemini-2.5-pro" in scores["reasoning"]
    assert "gemini-2.5-flash" in scores["reasoning"]
