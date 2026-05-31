from typing import TypedDict, Optional, Dict, Any

class PromptBenchState(TypedDict):
    # Inputs
    problem: str
    solution: str
    goals: str
    template: str
    prompt_version: str
    
    # Process variables
    prompt_content: Optional[str]
    prd: Optional[str]
    tokens: Optional[int]
    latency_ms: Optional[int]
    model: Optional[str]
    
    # Evaluation
    scores: Optional[Dict[str, Any]]
    final_score: Optional[float]
    
    # Execution Tracking
    error: Optional[str]
