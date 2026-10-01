from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.alunos import router as alunos_router

__all__ = ["auth_router", "alunos_router"]
