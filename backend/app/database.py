import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import Engine

# Resolve paths relative to backend directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
DB_DIR = os.path.join(DATA_DIR, "db")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
EXTRACTED_DIR = os.path.join(DATA_DIR, "extracted_text")
HOSPITAL_DIR = os.path.join(DATA_DIR, "hospital_lists")

for directory in [DB_DIR, UPLOADS_DIR, EXTRACTED_DIR, HOSPITAL_DIR]:
    os.makedirs(directory, exist_ok=True)

DB_PATH = os.path.abspath(os.path.join(DB_DIR, "policylens.db")).replace("\\", "/")
env_url = os.getenv("DATABASE_URL", "")
if not env_url or "./data/db" in env_url or env_url == "sqlite:///./data/db/policylens.db":
    DATABASE_URL = f"sqlite:///{DB_PATH}"
else:
    DATABASE_URL = env_url

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Enable foreign keys for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.models.models import User, Policy, PolicyPage, PolicyClause, PolicyField, Comparison, ComparisonPolicy, ChatSession, ChatMessage, HospitalImport, HospitalEntry
    Base.metadata.create_all(bind=engine)
    
    # Initialize SQLite FTS5 table for fast keyword & clause search
    with engine.connect() as conn:
        try:
            conn.execute(
                __import__("sqlalchemy").text(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS policy_fts USING fts5(policy_id UNINDEXED, page_number UNINDEXED, content);"
                )
            )
            conn.commit()
        except Exception as e:
            print(f"FTS5 init note: {e}")
