import os

# Set these before any application imports so tests never touch the local database.
os.environ["DATABASE_URL"] = "sqlite:///test_promptbench.db"
os.environ["REDIS_URL"] = "redis://mock"
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["GOOGLE_API_KEY"] = ""
