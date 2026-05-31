from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class PromptBase(BaseModel):
    version: str
    content: str
    description: Optional[str] = None
    is_active: Optional[bool] = True

class PromptCreate(PromptBase):
    pass

class PromptUpdate(BaseModel):
    content: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class PromptResponse(PromptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BenchmarkCaseResponse(BaseModel):
    id: str
    category: str
    problem: str
    solution: str
    goals: str
    template: str

    class Config:
        from_attributes = True

class GenerateRequest(BaseModel):
    problem: str
    solution: str
    goals: str
    template: str
    prompt_version: str

class ScoreDetail(BaseModel):
    coverage: float
    hallucination: float
    design: float
    engineering: float
    qa: float
    prototype: float
    repetition: float
    format: float
    final_score: float

class GenerateResponse(BaseModel):
    prd: str
    tokens: int
    latency_ms: int
    model: str
    scores: Optional[ScoreDetail] = None

class JudgeRequest(BaseModel):
    problem: str
    solution: str
    goals: str
    template: str
    prd: str

class JudgeResponse(ScoreDetail):
    reasoning: str = ""

class BenchmarkRunRequest(BaseModel):
    prompt_versions: List[str]
    categories: Optional[List[str]] = None
    case_ids: Optional[List[str]] = None
    limit: Optional[int] = None

class MetricRunResponse(BaseModel):
    id: int
    prompt_version: str
    benchmark_case_id: Optional[str]
    problem: str
    solution: str
    goals: str
    template: str
    prd: str
    tokens: int
    latency_ms: int
    coverage_score: float
    hallucination_score: float
    design_score: float
    engineering_score: float
    qa_score: float
    prototype_score: float
    repetition_score: float
    format_score: float
    final_score: float
    created_at: datetime

    class Config:
        from_attributes = True

# Benchmark Runner Schema
class BenchmarkCaseRunResult(BaseModel):
    case_id: str
    category: str
    tokens: int
    latency_ms: int
    scores: ScoreDetail

class BenchmarkPromptSummary(BaseModel):
    prompt_version: str
    average_score: float
    average_latency: float
    average_tokens: float
    coverage: float
    hallucination: float
    cases_run: int
    results: List[BenchmarkCaseRunResult]

class BenchmarkSuiteResponse(BaseModel):
    summaries: Dict[str, BenchmarkPromptSummary] # Key is prompt_version
    winner: str

# Dashboard Schemas
class LeaderboardEntry(BaseModel):
    version: str
    average_score: float
    average_latency: float
    average_tokens: float
    coverage_score: float
    hallucination_score: float
    runs_count: int

class TrendPoint(BaseModel):
    timestamp: str
    avg_score: float
    avg_coverage: float
    avg_hallucination: float
    avg_latency: float
    avg_tokens: float

class DashboardStats(BaseModel):
    leaderboard: List[LeaderboardEntry]
    trends: Dict[str, List[TrendPoint]] # Key is prompt_version
    total_runs: int
    avg_latency: float
    avg_tokens: float
