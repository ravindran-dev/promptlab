import os
import sys

# Add backend directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
print("GOOGLE_API_KEY:", settings.GOOGLE_API_KEY)
print("JUDGE_MODEL:", settings.JUDGE_MODEL)

# Ensure env variables from the active environment are loaded
print("CWD:", os.getcwd())

from app.services.evaluator import LLMJudge
judge = LLMJudge()
try:
    scores = judge.evaluate(
        problem="Test problem",
        solution="Test solution",
        goals="Test goals",
        template="## 1. Test",
        prd="This is a test generated PRD content that needs evaluation."
    )
    print("SCORES RESULTS:", scores)
except Exception as e:
    import traceback
    traceback.print_exc()
