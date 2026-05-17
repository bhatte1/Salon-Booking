from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Engine = the connection pool + DB dialect config
engine = create_engine(settings.database_url, pool_pre_ping=True)

# Session factory (we create a Session per request)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI dependency:
    - Creates a Session for the request
    - Yields it to your endpoint
    - Closes it after the request ends
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()