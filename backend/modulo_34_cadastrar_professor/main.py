from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from professores import router as professores_router
except ImportError:
    from .professores import router as professores_router

app = FastAPI(title="SGA-Edu | Cadastro de professor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(professores_router)


@app.get("/")
def raiz():
    return {"status": "API de professores rodando", "docs": "/docs"}
