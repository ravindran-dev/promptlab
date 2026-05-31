import json
import re
import logging
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from .llm import get_llm
from ..config import settings

logger = logging.getLogger(__name__)

class LLMJudge:
    SCORE_KEYS = ["coverage", "hallucination", "design", "engineering", "qa", "prototype", "repetition", "format"]
    SCORE_ALIASES = {
        "factuality": "hallucination",
        "accuracy": "hallucination",
        "quality": "coverage",
    }

    def __init__(self):
        self.model_names = self._model_fallbacks()
        self._llms: Dict[str, Any] = {}

    @staticmethod
    def _model_fallbacks() -> List[str]:
        models: List[str] = []
        for model_name in (settings.JUDGE_MODEL, settings.GEMINI_MODEL):
            if model_name and model_name not in models:
                models.append(model_name)
        return models

    def _get_llm(self, model_name: str) -> Any:
        if model_name not in self._llms:
            self._llms[model_name] = get_llm(
                model_name,
                max_tokens=settings.JUDGE_MAX_TOKENS,
                temperature=0.0,
                response_mime_type="application/json",
            )
        return self._llms[model_name]

    @staticmethod
    def _summarize_error(error: Exception) -> str:
        message = str(error).replace("\n", " ").strip()
        if len(message) > 500:
            return f"{message[:500]}..."
        return message

    @staticmethod
    def _content_to_text(content: Any) -> str:
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    parts.append(str(part.get("text", "")))
                elif isinstance(part, str):
                    parts.append(part)
            return "\n".join(parts).strip()
        return str(content).strip()

    @staticmethod
    def _extract_json(raw_content: str) -> Dict[str, Any]:
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_content, re.DOTALL | re.IGNORECASE)
        if fenced_match:
            return json.loads(fenced_match.group(1))

        decoder = json.JSONDecoder()
        start = raw_content.find("{")
        while start != -1:
            try:
                parsed, _ = decoder.raw_decode(raw_content[start:])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                start = raw_content.find("{", start + 1)
                continue
            break

        raise ValueError("Judge response did not contain a valid JSON object.")

    @classmethod
    def _extract_scores_fuzzy(cls, raw_content: str) -> Dict[str, Any]:
        scores: Dict[str, Any] = {}
        for key in cls.SCORE_KEYS:
            match = re.search(rf"\b{re.escape(key)}\b\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", raw_content, re.IGNORECASE)
            if match:
                scores[key] = match.group(1)

        for alias, target in cls.SCORE_ALIASES.items():
            if target in scores:
                continue
            match = re.search(rf"\b{re.escape(alias)}\b\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", raw_content, re.IGNORECASE)
            if match:
                scores[target] = match.group(1)

        reasoning_match = re.search(r"\breasoning\b\s*[:=]\s*(.+)$", raw_content, re.IGNORECASE | re.MULTILINE)
        if reasoning_match:
            scores["reasoning"] = reasoning_match.group(1).strip()

        return scores

    @classmethod
    def _normalize_scores(cls, scores: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        for key in cls.SCORE_KEYS:
            val = scores.get(key, 0.0)
            try:
                numeric = float(val)
            except (TypeError, ValueError):
                numeric = 0.0
            normalized[key] = max(0.0, min(100.0, numeric))

        normalized["reasoning"] = str(scores.get("reasoning", "")).strip()
        return normalized

    def evaluate(self, problem: str, solution: str, goals: str, template: str, prd: str) -> Dict[str, Any]:
        """
        Runs LLM-as-a-Judge evaluation on the generated PRD against original inputs and templates.
        Returns individual metric scores and calculates the overall weighted score.
        """
        judge_system_prompt = """
You are an expert product and engineering judge. Score the generated PRD against the inputs.

Metrics are 0-100:
- coverage: addresses problem, solution, and goals
- hallucination: avoids unsupported scope or invented systems
- design: includes UX flows, states, and layout details
- engineering: includes data models, APIs, and implementation details
- qa: includes positive, negative, and edge test cases
- prototype: clear MVP scope
- repetition: avoids duplicate content
- format: follows the requested markdown template

Return raw JSON only. No prose before or after:
{
  "coverage": 80.0,
  "hallucination": 95.0,
  "design": 85.0,
  "engineering": 75.0,
  "qa": 70.0,
  "prototype": 80.0,
  "repetition": 90.0,
  "format": 100.0,
  "reasoning": "One short sentence."
}
"""

        judge_user_content = f"""
### INITIAL INPUTS:
- Problem: {problem}
- Solution: {solution}
- Goals: {goals}
- Template: {template}

### GENERATED PRD:
{prd}
"""

        messages = [
            SystemMessage(content=judge_system_prompt),
            HumanMessage(content=judge_user_content)
        ]

        logger.info("Calling LLM Judge for evaluation...")

        errors: List[str] = []
        for model_name in self.model_names:
            try:
                response = self._get_llm(model_name).invoke(messages)
                raw_content = self._content_to_text(response.content)

                try:
                    parsed = self._extract_json(raw_content)
                except ValueError:
                    parsed = self._extract_scores_fuzzy(raw_content)
                    if not parsed:
                        raise

                scores = self._normalize_scores(parsed)

                # Calculate weighted final score
                final_score = (
                    scores["coverage"] * 0.20 +
                    scores["hallucination"] * 0.20 +
                    scores["design"] * 0.15 +
                    scores["engineering"] * 0.15 +
                    scores["qa"] * 0.10 +
                    scores["prototype"] * 0.10 +
                    scores["repetition"] * 0.05 +
                    scores["format"] * 0.05
                )
                scores["final_score"] = round(final_score, 2)

                logger.info(f"LLM Judge completed with {model_name}. Final Score: {scores['final_score']}")
                return scores

            except Exception as e:
                error_message = f"{model_name}: {self._summarize_error(e)}"
                errors.append(error_message)
                logger.warning(f"LLM Judge attempt failed with {error_message}")

        joined_errors = " | ".join(errors) if errors else "No judge models configured."
        logger.error(f"Error executing LLM Judge: {joined_errors}")
        # Return safe default fallback only after all configured judge models fail.
        return {
            "coverage": 50.0,
            "hallucination": 50.0,
            "design": 50.0,
            "engineering": 50.0,
            "qa": 50.0,
            "prototype": 50.0,
            "repetition": 50.0,
            "format": 50.0,
            "final_score": 50.0,
            "reasoning": f"Judge failed with error(s): {joined_errors}. Fallback default scores returned."
        }
