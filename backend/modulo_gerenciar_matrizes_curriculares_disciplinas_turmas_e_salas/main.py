from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from router import router
except ImportError:
    from .router import router

app = FastAPI(
    title="SGA-Edu | Gestão de Matrizes Curriculares, Disciplinas, Turmas e Salas",
    version="0.1.0",
    description="API do módulo acadêmico para gerenciamento de matrizes curriculares, componentes disciplinares, ofertas de turmas e controle de alocação de salas com prevenção de conflitos temporais.",
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
        "status": "API de Gestão de Matrizes Curriculares, Disciplinas, Turmas e Salas rodando",
        "modulo": "SGA-23",
        "docs": "/docs",
    }
