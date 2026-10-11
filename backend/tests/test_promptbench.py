import os
import sys
import pytest
import json
from langchain_core.messages import AIMessage
from fastapi.testclient import TestClient

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set env to use sqlite file-based db for testing to prevent pooling issues
os.environ["DATABASE_URL"] = "sqlite:///test_promptbench.db"
os.environ["REDIS_URL"] = "redis://mock" # Bypass Redis for unit tests
os.environ["GOOGLE_API_KEY"] = ""

from backend.app.main import app
from backend.app.database import Base, engine, SessionLocal
from backend.app.models import BenchmarkCase, Prompt, MetricRun
from backend.app.services.registry import PromptRegistry

client = TestClient(app)

@pytest.fixture(autouse=True)
def local_llm(monkeypatch):
    from backend.app.workflow import graph
    from backend.app.services import evaluator

    class TestLLM:
        def __init__(self, json_output):
            self.json_output = json_output

        def invoke(self, messages):
            if self.json_output:
                return AIMessage(content=json.dumps({
                    **{key: 80 for key in evaluator.LLMJudge.SCORE_KEYS},
                    "reasoning": "Test judge response",
                }))
            return AIMessage(content="## 1. Description\nGenerated test PRD", usage_metadata={
                "input_tokens": 20, "output_tokens": 10, "total_tokens": 30,
            })

    def fake_get_llm(model_name, **kwargs):
        return TestLLM(kwargs.get("response_mime_type") == "application/json")

    monkeypatch.setattr(graph, "get_llm", fake_get_llm)
    monkeypatch.setattr(evaluator, "get_llm", fake_get_llm)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Register v1 prompt for testing
    PromptRegistry.set_prompt_content(
        version="v1",
        content="Test System Prompt: Problem: {problem}, Solution: {solution}, Goals: {goals}, Template: {template}",
        db=db,
        description="V1 test prompt"
    )
    
    # Register a test case
    test_case = BenchmarkCase(
        id="small_test_case",
        category="small_features",
        problem="Test Problem",
        solution="Test Solution",
        goals="Test Goals",
        template="Test Template"
    )
    db.add(test_case)
    db.commit()
    db.close()
    
    yield
    
    # Drop tables and close connections
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    
    # Clean up file
    if os.path.exists("test_promptbench.db"):
        try:
            os.remove("test_promptbench.db")
        except Exception:
            pass

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
    from backend.app.config import settings
    assert response.json()["provider"] == "ollama"
    assert response.json()["models"] == {
        "generator": settings.OLLAMA_MODEL,
        "judge": settings.OLLAMA_JUDGE_MODEL,
    }

def test_list_prompts():
    response = client.get("/api/prompts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(p["version"] == "v1" for p in data)

def test_get_prompt_v1():
    response = client.get("/api/prompts/v1")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v1"
    assert "Test System Prompt" in data["content"]

def test_generate_prd():
    payload = {
        "problem": "Unorganized workspace files",
        "solution": "Create automated tagging script",
        "goals": "Sort files, reduce search latency",
        "template": "## 1. Description\n## 2. API Schema",
        "prompt_version": "v1"
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prd" in data
    assert "tokens" in data
    assert "latency_ms" in data
    from backend.app.config import settings
    assert data["model"] == settings.OLLAMA_MODEL
    assert data["tokens"] == 30
    assert data["scores"] is not None
    assert data["scores"]["final_score"] > 0

def test_run_benchmark():
    payload = {
        "prompt_versions": ["v1"],
        "case_ids": ["small_test_case"]
    }
    response = client.post("/api/benchmark/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "summaries" in data
    assert "v1" in data["summaries"]
    assert data["summaries"]["v1"]["cases_run"] == 1
    assert data["summaries"]["v1"]["average_score"] > 0
    assert data["winner"] == "v1"

def test_metrics_dashboard():
    # Make sure we have run evaluations logged in DB
    response = client.get("/api/metrics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "leaderboard" in data
    assert "trends" in data
    assert "total_runs" in data
