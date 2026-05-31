from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import GenerateRequest, GenerateResponse, ScoreDetail
from ..workflow.graph import promptbench_graph

router = APIRouter(prefix="/api/generate", tags=["generate"])

@router.post("", response_model=GenerateResponse)
def generate_prd(payload: GenerateRequest, db: Session = Depends(get_db)):
    """
    Generate a Product Requirement Document (PRD) from inputs using LangGraph workflow.
    Also executes LLM-as-a-Judge evaluation and logs results in PostgreSQL database.
    """
    initial_state = {
        "problem": payload.problem,
        "solution": payload.solution,
        "goals": payload.goals,
        "template": payload.template,
        "prompt_version": payload.prompt_version,
        "prompt_content": None,
        "prd": None,
        "tokens": None,
        "latency_ms": None,
        "model": None,
        "scores": None,
        "final_score": None,
        "error": None
    }
    
    # Execute LangGraph passing database session in config
    config = {
        "configurable": {
            "db": db
        }
    }
    
    result_state = promptbench_graph.invoke(initial_state, config)
    
    if result_state.get("error"):
        raise HTTPException(
            status_code=500,
            detail=f"LangGraph execution encountered an error: {result_state['error']}"
        )
        
    scores = result_state.get("scores", {})
    score_detail = None
    if scores:
        score_detail = ScoreDetail(
            coverage=scores.get("coverage", 0.0),
            hallucination=scores.get("hallucination", 0.0),
            design=scores.get("design", 0.0),
            engineering=scores.get("engineering", 0.0),
            qa=scores.get("qa", 0.0),
            prototype=scores.get("prototype", 0.0),
            repetition=scores.get("repetition", 0.0),
            format=scores.get("format", 0.0),
            final_score=result_state.get("final_score", 0.0)
        )
        
    return GenerateResponse(
        prd=result_state.get("prd", ""),
        tokens=result_state.get("tokens", 0),
        latency_ms=result_state.get("latency_ms", 0),
        model=result_state.get("model", "unknown-model"),
        scores=score_detail
    )
