"""Roteador FastAPI e aplicação standalone para cadastro e gestão de alunos (SGA-15)."""

from typing import Optional
from fastapi import APIRouter, Depends, FastAPI, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware

try:
    from .audit_service import extrair_ip_cliente
    from .repository import AlunoRepository, get_repository
    from .schemas import (
        AlunoCreate,
        AlunoResponse,
        AlunoStatusUpdate,
        AlunoUpdate,
        AuditoriaEventoResponse,
        StatusAcademicoEnum,
    )
    from .security import OperadorAutenticado, require_secretaria_ou_admin
    from .service import (
        alterar_status,
        atualizar_aluno,
        cadastrar_aluno,
        consultar_auditoria,
        detalhar_aluno,
        listar_alunos,
    )
except ImportError:
    from audit_service import extrair_ip_cliente
    from repository import AlunoRepository, get_repository
    from schemas import (
        AlunoCreate,
        AlunoResponse,
        AlunoStatusUpdate,
        AlunoUpdate,
        AuditoriaEventoResponse,
        StatusAcademicoEnum,
    )
    from security import OperadorAutenticado, require_secretaria_ou_admin
    from service import (
        alterar_status,
        atualizar_aluno,
        cadastrar_aluno,
        consultar_auditoria,
        detalhar_aluno,
        listar_alunos,
    )


router = APIRouter(
    prefix="/api/alunos",
    tags=["Alunos"],
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AlunoResponse)
def criar_aluno(
    payload: AlunoCreate,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    repo: AlunoRepository = Depends(get_repository),
) -> AlunoResponse:
    """Cadastra conjuntamente um novo aluno, sua matrícula e sua conta de acesso com perfil Aluno."""
    return cadastrar_aluno(
        repo=repo,
        dados=payload,
        operador=operador,
        ip_origem=extrair_ip_cliente(request),
    )


@router.get("", response_model=list[AlunoResponse])
def listar_alunos_endpoint(
    status_academico: Optional[StatusAcademicoEnum] = Query(default=None),
    curso_id: Optional[int] = Query(default=None),
    ativo: Optional[bool] = Query(default=None),
    busca: Optional[str] = Query(default=None),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    repo: AlunoRepository = Depends(get_repository),
) -> list[AlunoResponse]:
    """Lista alunos ordenados alfabeticamente por nome com filtros opcionais."""
    return listar_alunos(
        repo=repo,
        status_academico=status_academico,
        curso_id=curso_id,
        ativo=ativo,
        busca=busca,
    )


@router.get("/auditoria", response_model=list[AuditoriaEventoResponse])
def listar_auditoria_alunos(
    id_registro_afetado: Optional[str] = Query(default=None),
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    repo: AlunoRepository = Depends(get_repository),
) -> list[AuditoriaEventoResponse]:
    """Retorna os eventos da trilha de auditoria do módulo de alunos."""
    return consultar_auditoria(repo=repo, id_registro_afetado=id_registro_afetado)


@router.get("/{matricula}", response_model=AlunoResponse)
def detalhar_aluno_endpoint(
    matricula: int,
    _operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    repo: AlunoRepository = Depends(get_repository),
) -> AlunoResponse:
    """Retorna os detalhes cadastrais, acadêmicos e de conta de um aluno pela matrícula."""
    return detalhar_aluno(repo=repo, matricula=matricula)


@router.put("/{matricula}", response_model=AlunoResponse)
def atualizar_aluno_endpoint(
    matricula: int,
    payload: AlunoUpdate,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    repo: AlunoRepository = Depends(get_repository),
) -> AlunoResponse:
    """Atualiza dados pessoais, de contato, curso, login e situação acadêmica de um aluno."""
    return atualizar_aluno(
        repo=repo,
        matricula=matricula,
        dados=payload,
        operador=operador,
        ip_origem=extrair_ip_cliente(request),
    )


@router.patch("/{matricula}/status", response_model=AlunoResponse)
def alterar_status_aluno_endpoint(
    matricula: int,
    payload: AlunoStatusUpdate,
    request: Request,
    operador: OperadorAutenticado = Depends(require_secretaria_ou_admin),
    repo: AlunoRepository = Depends(get_repository),
) -> AlunoResponse:
    """Ativa ou inativa a conta de acesso do aluno preservando seu histórico acadêmico."""
    return alterar_status(
        repo=repo,
        matricula=matricula,
        dados=payload,
        operador=operador,
        ip_origem=extrair_ip_cliente(request),
    )


app = FastAPI(
    title="SGA-Edu — Módulo Cadastrar Alunos",
    description="API REST para cadastro e gestão de alunos pela Secretaria Acadêmica e Administração (SGA-15).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def raiz() -> dict[str, str]:
    """Healthcheck da aplicação standalone do módulo de alunos."""
    return {"status": "API Módulo Cadastrar Alunos rodando", "docs": "/docs"}
