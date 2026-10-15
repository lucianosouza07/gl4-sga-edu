from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from professores import router as professores_router
except ImportError:
    from .professores import router as professores_router

try:
    from modulo_30_autenticacao_rbac.auth import router as auth_router
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from modulo_30_autenticacao_rbac.auth import router as auth_router

app = FastAPI(title="SGA-Edu | API Integrada", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(professores_router)
app.include_router(auth_router)


@app.get("/")
def raiz():
    return {"status": "API SGA-Edu rodando", "docs": "/docs"}

