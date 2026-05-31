import os
import sys
import traceback

# Ensure Cwd in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environmental variables from .env
from dotenv import load_dotenv
load_dotenv()

# We want to test with the actual configured database and api key to see the exact runtime error
from backend.app.database import SessionLocal, Base, engine
from backend.app.workflow.graph import promptbench_graph

db = SessionLocal()

state = {
    "problem": "Unorganized files",
    "solution": "Automated script",
    "goals": "Sort, reduce search latency",
    "template": "## 1. Description",
    "prompt_version": "v1",
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
        "db": db
    }
}

print("[*] Invoking LangGraph workflow with live settings...")
try:
    res = promptbench_graph.invoke(state, config)
    print("\n[+] Run finished.")
    print(f"Graph Output Error: {res.get('error')}")
    print(f"Graph Output Scores: {res.get('scores')}")
    print(f"Graph Output PRD Snippet: {res.get('prd')[:200] if res.get('prd') else None}")
except Exception as e:
    print("\n[-] Graph Execution Crashed!")
    traceback.print_exc()
finally:
    db.close()
