from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Lê a URL do banco das configurações centralizadas
DATABASE_URL = settings.DATABASE_URL

# Ajuste específico de concorrência para SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=settings.SQL_ECHO
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI para fornecer uma sessão de banco e garantir seu fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Cria todas as tabelas registradas no metadata da Base."""
    import app.models  # Garante o registro de todos os modelos
    Base.metadata.create_all(bind=engine)
