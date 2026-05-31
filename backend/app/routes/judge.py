from fastapi import APIRouter
from ..schemas import JudgeRequest, JudgeResponse
from ..services.evaluator import LLMJudge

router = APIRouter(prefix="/api/judge", tags=["judge"])

@router.post("", response_model=JudgeResponse)
def judge_prd(payload: JudgeRequest):
    """
    Score an existing PRD with the same LLM-as-a-Judge rubric used by generation
    and benchmark runs.
    """
    scores = LLMJudge().evaluate(
        problem=payload.problem,
        solution=payload.solution,
        goals=payload.goals,
        template=payload.template,
        prd=payload.prd,
    )
    return JudgeResponse(**scores)
