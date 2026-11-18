"""Roteador FastAPI e aplicação standalone para funcionários administrativos (SGA-19)."""

from typing import Optional
from fastapi import APIRouter, Depends, FastAPI, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware

try:
    from .audit_service import extrair_ip_cliente
    from .repository import FuncionarioAdminRepository, get_repository
    from .schemas import (
        AuditoriaEventoResponse,
        FuncionarioAdminCreate,
        FuncionarioAdminResponse,
        FuncionarioAdminStatusUpdate,
        FuncionarioAdminUpdate,
        MensagemResponse,
        PerfilAdminEnum,
    )
    from .security import OperadorAutenticado, require_admin
    from .service import (
        alterar_status,
        atualizar_funcionario,
        cadastrar_funcionario,
        consultar_auditoria,
        detalhar_funcionario,
        excluir_funcionario,
        listar_funcionarios,
    )
except ImportError:
    from audit_service import extrair_ip_cliente
    from repository import FuncionarioAdminRepository, get_repository
    from schemas import (
        AuditoriaEventoResponse,
        FuncionarioAdminCreate,
        FuncionarioAdminResponse,
        FuncionarioAdminStatusUpdate,
        FuncionarioAdminUpdate,
        MensagemResponse,
        PerfilAdminEnum,
    )
    from security import OperadorAutenticado, require_admin
    from service import (
        alterar_status,
        atualizar_funcionario,
        cadastrar_funcionario,
        consultar_auditoria,
        detalhar_funcionario,
        excluir_funcionario,
        listar_funcionarios,
    )


router = APIRouter(
    prefix="/api/funcionarios-administrativos",
    tags=["Funcionários Administrativos"],
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=FuncionarioAdminResponse)
def criar_funcionario_administrativo(
    payload: FuncionarioAdminCreate,
    request: Request,
    operador: OperadorAutenticado = Depends(require_admin),
    repo: FuncionarioAdminRepository = Depends(get_repository),
) -> FuncionarioAdminResponse:
    """Cadastra conjuntamente um funcionário administrativo e sua conta de acesso RBAC."""
    return cadastrar_funcionario(
        repo=repo,
        dados=payload,
        operador=operador,
        ip_origem=extrair_ip_cliente(request),
    )


@router.get("", response_model=list[FuncionarioAdminResponse])
def listar_funcionarios_administrativos(
    perfil: Optional[PerfilAdminEnum] = Query(default=None),
    setor: Optional[str] = Query(default=None),
    ativo: Optional[bool] = Query(default=None),
    _operador: OperadorAutenticado = Depends(require_admin),
    repo: FuncionarioAdminRepository = Depends(get_repository),
) -> list[FuncionarioAdminResponse]:
    """Lista funcionários administrativos ordenados alfabeticamente com filtros opcionais."""
    return listar_funcionarios(repo=repo, perfil=perfil, setor=setor, ativo=ativo)


@router.get("/auditoria", response_model=list[AuditoriaEventoResponse])
def listar_auditoria_funcionarios(
    id_registro_afetado: Optional[str] = Query(default=None),
    _operador: OperadorAutenticado = Depends(require_admin),
    repo: FuncionarioAdminRepository = Depends(get_repository),
) -> list[AuditoriaEventoResponse]:
    """Retorna os eventos da trilha de auditoria do módulo administrativo."""
    return consultar_auditoria(repo=repo, id_registro_afetado=id_registro_afetado)


@router.get("/{funcionario_id}", response_model=FuncionarioAdminResponse)
def detalhar_funcionario_administrativo(
    funcionario_id: int,
    _operador: OperadorAutenticado = Depends(require_admin),
    repo: FuncionarioAdminRepository = Depends(get_repository),
) -> FuncionarioAdminResponse:
    """Retorna os detalhes cadastrais de um funcionário administrativo."""
    return detalhar_funcionario(repo=repo, funcionario_id=funcionario_id)


@router.put("/{funcionario_id}", response_model=FuncionarioAdminResponse)
def atualizar_funcionario_administrativo(
    funcionario_id: int,
    payload: FuncionarioAdminUpdate,
    request: Request,
    operador: OperadorAutenticado = Depends(require_admin),
    repo: FuncionarioAdminRepository = Depends(get_repository),
) -> FuncionarioAdminResponse:
    """Atualiza dados funcionais, login e perfil administrativo de um servidor."""
    return atualizar_funcionario(
        repo=repo,
        funcionario_id=funcionario_id,
        dados=payload,
        operador=operador,
        ip_origem=extrair_ip_cliente(request),
    )


@router.patch("/{funcionario_id}/status", response_model=FuncionarioAdminResponse)
def alterar_status_funcionario_administrativo(
    funcionario_id: int,
    payload: FuncionarioAdminStatusUpdate,
    request: Request,
    operador: OperadorAutenticado = Depends(require_admin),
    repo: FuncionarioAdminRepository = Depends(get_repository),
) -> FuncionarioAdminResponse:
    """Ativa ou inativa a conta do funcionário administrativo."""
    return alterar_status(
        repo=repo,
        funcionario_id=funcionario_id,
        dados=payload,
        operador=operador,
        ip_origem=extrair_ip_cliente(request),
    )


@router.delete("/{funcionario_id}", response_model=MensagemResponse)
def excluir_funcionario_administrativo(
    funcionario_id: int,
    request: Request,
    operador: OperadorAutenticado = Depends(require_admin),
    repo: FuncionarioAdminRepository = Depends(get_repository),
) -> MensagemResponse:
    """Exclui o funcionário administrativo e sua conta de usuário associada."""
    return excluir_funcionario(
        repo=repo,
        funcionario_id=funcionario_id,
        operador=operador,
        ip_origem=extrair_ip_cliente(request),
    )


app = FastAPI(
    title="SGA-Edu — Módulo Funcionários Administrativos",
    description="API REST para gestão cadastral de funcionários administrativos (Secretaria, Financeiro e Admin).",
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
