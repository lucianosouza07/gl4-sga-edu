import os
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Lê a URL do banco da variável de ambiente ou usa SQLite local por padrão
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sga_edu.db")

# Ajuste específico de concorrência para SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=os.getenv("SQL_ECHO", "False").lower() in ("true", "1")
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
