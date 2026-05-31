import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .config import settings
from .models import BenchmarkCase
from .routes import prompts, generate, benchmark, metrics, judge
from .seed_benchmarks import BENCHMARK_CASES

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize database tables
logger.info("Initializing database tables...")
Base.metadata.create_all(bind=engine)

# Seed database benchmark cases
logger.info("Checking database benchmark cases...")
db = SessionLocal()
try:
    existing_count = db.query(BenchmarkCase).count()
    if existing_count == 0:
        logger.info(f"Database benchmark table empty. Seeding {len(BENCHMARK_CASES)} cases...")
        for case in BENCHMARK_CASES:
            db_case = BenchmarkCase(
                id=case["id"],
                category=case["category"],
                problem=case["problem"],
                solution=case["solution"],
                goals=case["goals"],
                template=case["template"]
            )
            db.add(db_case)
        db.commit()
        logger.info("Successfully seeded database benchmark cases.")
    else:
        logger.info(f"Database benchmark table already populated with {existing_count} cases.")
except Exception as e:
    logger.error(f"Error seeding database benchmark cases: {e}")
finally:
    db.close()

# Initialize FastAPI App
app = FastAPI(
    title="ProductOS PromptLab API",
    description="Backend AI benchmarking service tracking prompt performance and automated scoring metrics.",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to dashboard origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(prompts.router)
app.include_router(generate.router)
app.include_router(benchmark.router)
app.include_router(metrics.router)
app.include_router(judge.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "ProductOS PromptLab API Engine",
        "models": {
            "generator": settings.GEMINI_MODEL,
            "judge": settings.JUDGE_MODEL
        }
    }
