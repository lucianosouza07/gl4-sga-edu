from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database.session import init_db, SessionLocal
from app.seeds.admin_seed import seed_admin_padrao
from app.api.v1.api import api_router
from app.core.exceptions import (
    DominioError,
    RegistroJaExisteError,
    EntidadeNaoEncontradaError,
    CredenciaisInvalidasError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida da aplicação: inicializa tabelas e garante o seed do administrador."""
    init_db()
    db = SessionLocal()
    try:
        seed_admin_padrao(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="GL4 SGA-EDU — API de Gestão Acadêmica",
    description="API RESTful com JWT Bearer Token, RBAC e gestão de alunos e usuários.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configuração de CORS para permitir requisições do frontend React / Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Handlers de Padronização de Mensagens de Erro em Português
# ------------------------------------------------------------------------------
@app.exception_handler(DominioError)
async def dominio_exception_handler(request: Request, exc: DominioError):
    """Padroniza exceções do domínio (regras de negócio) para status HTTP correspondente."""
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, RegistroJaExisteError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, EntidadeNaoEncontradaError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, CredenciaisInvalidasError):
        status_code = status.HTTP_401_UNAUTHORIZED

    return JSONResponse(status_code=status_code, content={"detail": exc.mensagem})


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Traduz mensagens padrão do framework (Starlette/FastAPI) para português brasileiro."""
    detail = exc.detail
    if exc.status_code == status.HTTP_404_NOT_FOUND and detail == "Not Found":
        detail = "Recurso ou rota não encontrada no sistema."
    elif exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED and detail == "Method Not Allowed":
        detail = "Método HTTP não permitido para este endpoint."
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED and detail == "Not authenticated":
        detail = "Não autenticado. Token de acesso Bearer não informado."

    headers = getattr(exc, "headers", None)
    return JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Traduz e estrutura mensagens de validação do Pydantic em português claro."""
    erros = []
    for erro in exc.errors():
        campo = " -> ".join(str(loc) for loc in erro.get("loc", []) if loc != "body")
        msg = erro.get("msg", "")
        tipo = erro.get("type", "")

        if tipo == "missing":
            msg = "Campo obrigatório não informado."
        elif tipo.startswith("string_too_short"):
            msg = "Texto menor que o comprimento mínimo exigido."
        elif tipo.startswith("string_too_long"):
            msg = "Texto maior que o comprimento máximo permitido."
        elif "email" in tipo or "email" in msg.lower():
            msg = "Formato de e-mail inválido."

        erros.append({"campo": campo or "payload", "mensagem": msg})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": "Erro de validação nos dados enviados.",
            "erros": erros
        }
    )


# Inclusão das rotas da API v1
app.add_api_route("/health", lambda: {"status": "ok", "service": "GL4 SGA-EDU API"}, tags=["Health"])
app.include_router(api_router, prefix="/api/v1")
