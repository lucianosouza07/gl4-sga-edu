from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from router import router
except ImportError:
    from .router import router

app = FastAPI(
    title="SGA-Edu | Controle de Movimentação Acadêmica",
    version="0.1.0",
    description="API para gestão de trancamento, transferência, cancelamento, jubilamento e auditoria de matrícula discente no SGA-Edu.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def raiz():
    return {
        "status": "API de Controle de Movimentação Acadêmica rodando",
        "modulo": "SGA-24",
        "docs": "/docs",
    }
