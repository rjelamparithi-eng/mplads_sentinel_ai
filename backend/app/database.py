import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

load_dotenv()

# Absolute path resolution anchored to backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent
CANONICAL_DB_PATH = BACKEND_DIR / "mplads_sentinel.db"

env_db_url = os.getenv("DATABASE_URL", "").strip()

if not env_db_url or env_db_url == "sqlite:///./mplads_sentinel.db" or env_db_url.startswith("sqlite:///./"):
    DATABASE_URL = f"sqlite:///{CANONICAL_DB_PATH.resolve().as_posix()}"
elif env_db_url.startswith("sqlite:///") and not os.path.isabs(env_db_url.replace("sqlite:///", "")):
    rel_path = env_db_url.replace("sqlite:///", "")
    abs_path = (BACKEND_DIR / rel_path).resolve()
    DATABASE_URL = f"sqlite:///{abs_path.as_posix()}"
else:
    DATABASE_URL = env_db_url

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        DATABASE_URL, 
        connect_args=connect_args,
        poolclass=NullPool
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=30
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
