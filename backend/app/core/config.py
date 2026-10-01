import os
from pathlib import Path
from dotenv import load_dotenv

# Localiza e carrega o arquivo .env a partir da raiz do repositório ou da pasta backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
ROOT_DIR = BASE_DIR.parent  # raiz do repositório

env_path_root = ROOT_DIR / ".env"
env_path_backend = BASE_DIR / ".env"

if env_path_root.exists():
    load_dotenv(dotenv_path=env_path_root)
elif env_path_backend.exists():
    load_dotenv(dotenv_path=env_path_backend)
else:
    load_dotenv()


class Settings:
    """Configurações centralizadas da aplicação GL4 SGA-EDU lidas de variáveis de ambiente."""

    # Ambiente de Execução
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Servidor Backend
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))

    # Banco de Dados (SQLAlchemy)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sga_edu.db")
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "False").lower() in ("true", "1")

    # Autenticação e Segurança (JWT)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "chave_secreta_padrao_para_dev_gl4_sga_edu_2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Administrador Padrão (Seed)
    DEFAULT_ADMIN_NAME: str = os.getenv("DEFAULT_ADMIN_NAME", "Administrador do Sistema")
    DEFAULT_ADMIN_EMAIL: str = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@gl4.edu")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

    # CORS
    @property
    def CORS_ORIGINS(self) -> list[str]:
        origens_raw = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,https://gl4-sga-edu.luis-carvalho.online"
        )
        return [origem.strip() for origem in origens_raw.split(",") if origem.strip()]

    @property
    def CORS_ORIGIN_REGEX(self) -> str | None:
        regex = os.getenv(
            "CORS_ORIGIN_REGEX",
            r"^https?://(localhost|127\.0\.0\.1|.*\.luis-carvalho\.online)(:\d+)?$"
        )
        return regex.strip() if regex and regex.strip() else None


settings = Settings()
