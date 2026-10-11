import json
import re
import logging
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from .llm import get_llm, invoke_with_retry
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
        return [settings.judge_model] if settings.judge_model else []

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

    def _reformat_to_json(self, model_name: str, raw_content: str, *, strict: bool = False) -> Dict[str, Any]:
        reformat_system_prompt = (
            "You are a formatter. Return only valid JSON for the judge schema. "
            "No prose, no markdown."
        )
        strict_note = "All keys are required. Use 0-100 numbers only." if strict else ""
        reformat_user_content = f"""
Convert this content into JSON that matches the required schema.
{strict_note}

Schema:
{{
  "coverage": 0,
  "hallucination": 0,
  "design": 0,
  "engineering": 0,
  "qa": 0,
  "prototype": 0,
  "repetition": 0,
  "format": 0,
  "reasoning": ""
}}

CONTENT:
{raw_content}
"""
        messages = [
            SystemMessage(content=reformat_system_prompt),
            HumanMessage(content=reformat_user_content),
        ]
        response = invoke_with_retry(self._get_llm(model_name), messages)
        reformatted = self._content_to_text(response.content)
        return self._extract_json(reformatted)

    @classmethod
    def _missing_score_keys(cls, scores: Dict[str, Any]) -> List[str]:
        return [key for key in cls.SCORE_KEYS if key not in scores]

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

    @classmethod
    def _fill_missing_scores(cls, scores: Dict[str, Any]) -> Dict[str, Any]:
        completed = dict(scores)
        numeric_values: List[float] = []
        for key in cls.SCORE_KEYS:
            try:
                if key in completed:
                    numeric_values.append(float(completed[key]))
            except (TypeError, ValueError):
                continue

        fallback_value = 50.0
        if numeric_values:
            fallback_value = sum(numeric_values) / len(numeric_values)

        for key in cls.SCORE_KEYS:
            if key not in completed:
                completed[key] = fallback_value

        if not completed.get("reasoning"):
            completed["reasoning"] = "Judge response missing some fields; scores inferred from available values."

        return completed

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

Return raw JSON only. No prose before or after. Do not include chain-of-thought:
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
        if not self.model_names:
            raise RuntimeError("Judge model is not configured. Set OLLAMA_JUDGE_MODEL for Ollama or JUDGE_MODEL for Gemini.")
        for model_name in self.model_names:
            try:
                response = invoke_with_retry(self._get_llm(model_name), messages)
                raw_content = self._content_to_text(response.content)

                try:
                    parsed = self._extract_json(raw_content)
                except ValueError:
                    try:
                        parsed = self._reformat_to_json(model_name, raw_content)
                    except Exception:
                        parsed = self._extract_scores_fuzzy(raw_content)

                if not parsed:
                    if settings.provider == "ollama":
                        parsed = {
                            "reasoning": "Judge response was not valid JSON; scores defaulted for Ollama output."
                        }
                    else:
                        raise ValueError("Judge response did not contain a valid JSON object.")

                missing = self._missing_score_keys(parsed)
                if missing:
                    try:
                        parsed = self._reformat_to_json(model_name, raw_content, strict=True)
                    except Exception:
                        pass
                    parsed = self._fill_missing_scores(parsed)

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
        raise RuntimeError(f"LLM Judge failed for all configured models: {joined_errors}")
