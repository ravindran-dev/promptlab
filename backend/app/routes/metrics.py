import json
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from ..database import get_db
from ..models import MetricRun
from ..schemas import DashboardStats, LeaderboardEntry, TrendPoint, MetricRunResponse
from ..services.registry import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_statistics(db: Session = Depends(get_db)):
    """
    Returns dashboard statistics containing the Prompt Leaderboard, quality score trends,
    latency, and token counts. Caches the response in Redis for fast access.
    """
    cache_key = "dashboard:stats"
    
    # 1. Try to load from Redis cache
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info("Serving dashboard stats from Redis cache.")
                return DashboardStats(**json.loads(cached_data))
        except Exception as e:
            logger.warning(f"Failed to read from Redis cache: {e}")

    logger.info("Computing dashboard stats from PostgreSQL...")

    # 2. Query Postgres
    # Total stats
    total_runs_query = db.query(func.count(MetricRun.id), func.avg(MetricRun.latency_ms), func.avg(MetricRun.tokens)).first()
    total_runs = total_runs_query[0] or 0
    avg_latency = float(total_runs_query[1] or 0.0)
    avg_tokens = float(total_runs_query[2] or 0.0)

    # Leaderboard (Aggregated by version)
    leaderboard_results = db.query(
        MetricRun.prompt_version,
        func.avg(MetricRun.final_score).label("avg_score"),
        func.avg(MetricRun.latency_ms).label("avg_latency"),
        func.avg(MetricRun.tokens).label("avg_tokens"),
        func.avg(MetricRun.coverage_score).label("avg_coverage"),
        func.avg(MetricRun.hallucination_score).label("avg_hallucination"),
        func.count(MetricRun.id).label("runs_count")
    ).group_by(MetricRun.prompt_version).order_by(func.avg(MetricRun.final_score).desc()).all()

    leaderboard = []
    for row in leaderboard_results:
        leaderboard.append(
            LeaderboardEntry(
                version=row.prompt_version,
                average_score=round(float(row.avg_score), 2),
                average_latency=round(float(row.avg_latency), 1),
                average_tokens=round(float(row.avg_tokens), 1),
                coverage_score=round(float(row.avg_coverage), 2),
                hallucination_score=round(float(row.avg_hallucination), 2),
                runs_count=row.runs_count
            )
        )

    # Trends over time (grouped by version and date)
    # Cast date for aggregation
    date_trunc = func.to_char(MetricRun.created_at, "YYYY-MM-DD HH24:MI")
    # For SQLite compatibility during unit testing:
    try:
        # Try to test with simple string format first or fallback
        trend_query = db.query(
            MetricRun.prompt_version,
            func.strftime("%Y-%m-%d %H:00", MetricRun.created_at).label("time_bucket") if db.bind.dialect.name == "sqlite" 
            else func.date_trunc("hour", MetricRun.created_at).label("time_bucket"),
            func.avg(MetricRun.final_score).label("avg_score"),
            func.avg(MetricRun.coverage_score).label("avg_coverage"),
            func.avg(MetricRun.hallucination_score).label("avg_hallucination"),
            func.avg(MetricRun.latency_ms).label("avg_latency"),
            func.avg(MetricRun.tokens).label("avg_tokens")
        ).group_by(
            MetricRun.prompt_version, 
            func.strftime("%Y-%m-%d %H:00", MetricRun.created_at) if db.bind.dialect.name == "sqlite" 
            else func.date_trunc("hour", MetricRun.created_at)
        ).order_by("time_bucket").all()
    except Exception as e:
        # Absolute fallback if date functions fail
        logger.warning(f"Detailed trend aggregation failed: {e}. Falling back to day-level query.")
        trend_query = db.query(
            MetricRun.prompt_version,
            func.strval(MetricRun.created_at).label("time_bucket") if db.bind.dialect.name == "sqlite"
            else func.cast(MetricRun.created_at, func.Date).label("time_bucket"),
            func.avg(MetricRun.final_score).label("avg_score"),
            func.avg(MetricRun.coverage_score).label("avg_coverage"),
            func.avg(MetricRun.hallucination_score).label("avg_hallucination"),
            func.avg(MetricRun.latency_ms).label("avg_latency"),
            func.avg(MetricRun.tokens).label("avg_tokens")
        ).group_by(
            MetricRun.prompt_version,
            func.strval(MetricRun.created_at) if db.bind.dialect.name == "sqlite"
            else func.cast(MetricRun.created_at, func.Date)
        ).order_by("time_bucket").all()

    trends = {}
    for row in trend_query:
        version = row.prompt_version
        if version not in trends:
            trends[version] = []
            
        time_str = str(row.time_bucket)
        # Parse timestamp string cleanly
        trends[version].append(
            TrendPoint(
                timestamp=time_str,
                avg_score=round(float(row.avg_score), 2),
                avg_coverage=round(float(row.avg_coverage), 2),
                avg_hallucination=round(float(row.avg_hallucination), 2),
                avg_latency=round(float(row.avg_latency), 1),
                avg_tokens=round(float(row.avg_tokens), 1)
            )
        )

    stats = DashboardStats(
        leaderboard=leaderboard,
        trends=trends,
        total_runs=total_runs,
        avg_latency=round(avg_latency, 1),
        avg_tokens=round(avg_tokens, 1)
    )

    # 3. Cache to Redis for 60 seconds
    if redis_client:
        try:
            redis_client.setex(cache_key, 60, json.dumps(stats.model_dump()))
            logger.info("Saved computed dashboard stats to Redis.")
        except Exception as e:
            logger.warning(f"Failed to cache dashboard stats in Redis: {e}")

    return stats

@router.get("/history", response_model=List[MetricRunResponse])
def get_run_history(limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns the complete linear history of individual metric evaluations.
    """
    return db.query(MetricRun).order_by(MetricRun.created_at.desc()).limit(limit).all()
