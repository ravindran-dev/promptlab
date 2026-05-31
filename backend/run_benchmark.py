import os
import sys
import json
import logging


# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal, Base, engine
from backend.app.models import BenchmarkCase, MetricRun
from backend.app.services.registry import PromptRegistry
from backend.app.workflow.graph import promptbench_graph

# Configure basic logging to file or silent, so console output is clean
logging.basicConfig(level=logging.ERROR)

def run_offline_benchmarks():
    global engine, SessionLocal
    
    # Verify connection to configured database (Postgres)
    try:
        conn = engine.connect()
        conn.close()
    except Exception as e:
        print(f"[-] Configured database connection failed ({e})")
        print("[*] Falling back to local SQLite database: promptbench_local.db")
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine("sqlite:///promptbench_local.db", connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
    db = SessionLocal()
    
    # 1. Initialize tables and make sure database is ready
    Base.metadata.create_all(bind=engine)
    
    # 2. Get all cases. If fallback SQLite database was just created, seed cases.
    cases = db.query(BenchmarkCase).all()
    if not cases:
        print("[*] Seeding benchmark cases in fallback SQLite database...")
        from backend.app.seed_benchmarks import BENCHMARK_CASES
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
        cases = db.query(BenchmarkCase).all()
        
    if not cases:
        print("[-] Error: No benchmark cases found.")
        sys.exit(1)
        
    print(f"[*] Starting PromptBench Offline Benchmark Suite...")
    print(f"[*] Loaded {len(cases)} benchmark test cases.")
    
    # 3. Check what prompt versions exist on filesystem
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_dir = os.path.join(base_dir, "prompts")
    versions = ["v1", "v2", "v3"] # Core versions required
    
    # Make sure they are loaded in DB
    for version in versions:
        try:
            PromptRegistry.get_prompt_content(version, db)
        except Exception as e:
            print(f"[-] Warning: Failed to pre-load prompt version {version}: {e}")

    results = {v: {"score": 0.0, "coverage": 0.0, "hallucination_resistance": 0.0, "latency": 0.0, "tokens": 0.0, "runs": 0} for v in versions}

    print("\n" + "="*50)
    print(" RUNNING BENCHMARK MATRIX (Prompt Version x Case ID)")
    print("="*50)

    # Let's run a representative subset if running offline to keep it fast, or all 30 if requested.
    # To be extremely thorough but fast, we will run the first 2 cases of each of the 5 categories (10 cases total).
    # If the user wants to run all 30, they can do so. Let's make it run 10 cases to balance speed and accuracy during console execution.
    categories_tracker = {}
    selected_cases = []
    for case in cases:
        if case.category not in categories_tracker:
            categories_tracker[case.category] = 0
        if categories_tracker[case.category] < 2: # Max 2 cases per category = 10 cases total
            selected_cases.append(case)
            categories_tracker[case.category] += 1
            
    print(f"[*] Selected {len(selected_cases)} representative test cases for benchmarking.")
    
    for case in selected_cases:
        print(f"\nEvaluating Case: [{case.id}] ({case.category})")
        print(f"  Problem: {case.problem[:60]}...")
        
        for version in versions:
            print(f"  -> Running {version.upper()}... ", end="", flush=True)
            
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
                # Execute LangGraph
                output = promptbench_graph.invoke(initial_state, config)
                
                if output.get("error"):
                    print(f"FAILED ({output['error']})")
                    continue
                    
                scores = output.get("scores", {})
                final_score = output.get("final_score", 0.0)
                
                results[version]["score"] += final_score
                results[version]["coverage"] += scores.get("coverage", 0.0)
                results[version]["hallucination_resistance"] += scores.get("hallucination", 0.0)
                results[version]["latency"] += output.get("latency_ms", 0)
                results[version]["tokens"] += output.get("tokens", 0)
                results[version]["runs"] += 1
                
                print(f"Done (Score: {final_score:.1f}, Latency: {output.get('latency_ms')}ms)")
                
            except Exception as e:
                print(f"CRASHED ({e})")
                
    # Calculate Averages
    averages = {}
    for version in versions:
        data = results[version]
        runs = data["runs"]
        if runs > 0:
            averages[version] = {
                "score": round(data["score"] / runs, 1),
                "coverage": round(data["coverage"] / runs, 1),
                # Let's count "hallucinations" as 100 - resistance score.
                # A resistance of 86% implies a hallucination rate/metric of 14.
                "hallucinations": round(100.0 - (data["hallucination_resistance"] / runs), 1),
                "latency_ms": int(data["latency"] / runs),
                "tokens": int(data["tokens"] / runs)
            }
        else:
            averages[version] = {"score": 0.0, "coverage": 0.0, "hallucinations": 0.0, "latency_ms": 0, "tokens": 0}

    # Find the winner
    winner = max(averages.keys(), key=lambda v: averages[v]["score"])

    # Output report
    print("\n" + "="*50)
    print(" BENCHMARK COMPILATION REPORT")
    print("="*50)
    
    for version in versions:
        print(f"Prompt {version.upper()} Score: {averages[version]['score']}")
        
    print("\nCoverage:")
    for version in versions:
        print(f"  {version.upper()} = {averages[version]['coverage']}%")
        
    print("\nHallucinations (100 - Resistance):")
    for version in versions:
        print(f"  {version.upper()} = {averages[version]['hallucinations']}")
        
    print("\nLatency:")
    for version in versions:
        print(f"  {version.upper()} = {averages[version]['latency_ms']} ms")

    print("\nToken Usage:")
    for version in versions:
        print(f"  {version.upper()} = {averages[version]['tokens']} tokens")

    print("\n" + "-"*50)
    print(f"Winner: {winner.upper()}")
    print("-"*50)
    
    db.close()

if __name__ == "__main__":
    run_offline_benchmarks()
