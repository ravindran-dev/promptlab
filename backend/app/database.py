from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

# For SQLite fallback during testing or local development without Postgres
database_url = settings.DATABASE_URL
if database_url.startswith("sqlite"):
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
else:
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        # Test connection
        conn = engine.connect()
        conn.close()
    except Exception as e:
        print(f"[-] Configured database connection failed ({e})")
        print("[*] Falling back to local SQLite database: promptbench_local.db")
        database_url = "sqlite:///promptbench_local.db"
        engine = create_engine(database_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
