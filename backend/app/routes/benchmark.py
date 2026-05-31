from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import BenchmarkCase
from ..schemas import BenchmarkCaseResponse, BenchmarkSuiteResponse, BenchmarkPromptSummary, BenchmarkCaseRunResult, ScoreDetail, BenchmarkRunRequest
from ..workflow.graph import promptbench_graph

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])

@router.get("/cases", response_model=List[BenchmarkCaseResponse])
def get_benchmark_cases(db: Session = Depends(get_db)):
    """
    List all loaded benchmark cases.
    """
    return db.query(BenchmarkCase).all()

@router.post("/run", response_model=BenchmarkSuiteResponse)
def run_benchmark_suite(
    payload: BenchmarkRunRequest,
    db: Session = Depends(get_db)
):
    """
    Executes a benchmark suite comparing multiple prompt versions against selected test cases.
    Outputs comparison reports including average scores, token counts, and latency.
    """
    prompt_versions = payload.prompt_versions
    if not prompt_versions:
        raise HTTPException(status_code=422, detail="At least one prompt version is required.")

    query = db.query(BenchmarkCase)
    if payload.categories:
        query = query.filter(BenchmarkCase.category.in_(payload.categories))
    if payload.case_ids:
        query = query.filter(BenchmarkCase.id.in_(payload.case_ids))
        
    cases = query.all()
    
    if not cases:
        raise HTTPException(status_code=404, detail="No benchmark cases found matching search criteria.")
        
    if payload.limit and payload.limit > 0:
        cases = cases[:payload.limit]

    logger_results = {}
    
    # Initialize summary dictionaries
    for version in prompt_versions:
        logger_results[version] = {
            "prompt_version": version,
            "total_score": 0.0,
            "total_latency": 0,
            "total_tokens": 0,
            "total_coverage": 0.0,
            "total_hallucination": 0.0,
            "cases_run": 0,
            "results": []
        }

    # Execute combinations
    for case in cases:
        for version in prompt_versions:
            initial_state = {
                "problem": case.problem,
                "solution": case.solution,
                "goals": case.goals,
                "template": case.template,
                "prompt_version": version,
                "prompt_content": None,
                "prd": None,
                "tokens": None,
                "latency_ms": None,
                "model": None,
                "scores": None,
                "final_score": None,
                "error": None
            }
            
            config = {
                "configurable": {
                    "db": db,
                    "benchmark_case_id": case.id
                }
            }
            
            try:
                # Invoke LangGraph
                result = promptbench_graph.invoke(initial_state, config)
                
                if result.get("error"):
                    continue
                    
                scores = result.get("scores", {})
                case_result = BenchmarkCaseRunResult(
                    case_id=case.id,
                    category=case.category,
                    tokens=result.get("tokens", 0),
                    latency_ms=result.get("latency_ms", 0),
                    scores=ScoreDetail(
                        coverage=scores.get("coverage", 0.0),
                        hallucination=scores.get("hallucination", 0.0),
                        design=scores.get("design", 0.0),
                        engineering=scores.get("engineering", 0.0),
                        qa=scores.get("qa", 0.0),
                        prototype=scores.get("prototype", 0.0),
                        repetition=scores.get("repetition", 0.0),
                        format=scores.get("format", 0.0),
                        final_score=result.get("final_score", 0.0)
                    )
                )
                
                sum_tracker = logger_results[version]
                sum_tracker["total_score"] += result.get("final_score", 0.0)
                sum_tracker["total_latency"] += result.get("latency_ms", 0)
                sum_tracker["total_tokens"] += result.get("tokens", 0)
                sum_tracker["total_coverage"] += scores.get("coverage", 0.0)
                sum_tracker["total_hallucination"] += scores.get("hallucination", 0.0)
                sum_tracker["cases_run"] += 1
                sum_tracker["results"].append(case_result)
                
            except Exception as e:
                # Log error and continue to avoid crashing suite
                import logging
                logging.getLogger(__name__).error(f"Error running benchmark for {version} on {case.id}: {e}")

    # Compile summaries
    summaries = {}
    winner_version = ""
    max_avg_score = -1.0
    
    for version, data in logger_results.items():
        count = data["cases_run"]
        if count == 0:
            continue
            
        avg_score = round(data["total_score"] / count, 2)
        
        summaries[version] = BenchmarkPromptSummary(
            prompt_version=version,
            average_score=avg_score,
            average_latency=round(data["total_latency"] / count, 1),
            average_tokens=round(data["total_tokens"] / count, 1),
            coverage=round(data["total_coverage"] / count, 2),
            hallucination=round(data["total_hallucination"] / count, 2),
            cases_run=count,
            results=data["results"]
        )
        
        if avg_score > max_avg_score:
            max_avg_score = avg_score
            winner_version = version

    return BenchmarkSuiteResponse(
        summaries=summaries,
        winner=winner_version
    )
