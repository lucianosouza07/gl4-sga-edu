import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.usuario import Usuario, PerfilUsuario
from app.schemas.aluno import AlunoCreate, AlunoUpdate, AlunoResponse
from app.services.aluno_service import AlunoService
from app.core.exceptions import RegistroJaExisteError, EntidadeNaoEncontradaError
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/alunos", tags=["Alunos"])


@router.post(
    "",
    response_model=AlunoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo aluno (Conjunto com Usuário)"
)
def criar_aluno(
    dados: AlunoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([PerfilUsuario.SECRETARIA, PerfilUsuario.ADMIN]))
) -> AlunoResponse:
    """
    Cadastra um novo Aluno no sistema e gera suas credenciais de acesso como Usuário.
    Acesso restrito para perfis SECRETARIA e ADMIN.
    """
    aluno_service = AlunoService(db)
    try:
        novo_aluno = aluno_service.criar_aluno(dados)
        return AlunoResponse.model_validate(novo_aluno)
    except RegistroJaExisteError as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=erro.mensagem
        )


@router.get(
    "",
    response_model=list[AlunoResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar alunos com filtros e busca"
)
def listar_alunos(
    busca: Optional[str] = Query(None, description="Filtro por nome ou matrícula"),
    apenas_ativos: bool = Query(True, description="Filtrar apenas alunos com status ATIVO"),
    skip: int = Query(0, ge=0, description="Offset de paginação"),
    limit: int = Query(100, ge=1, le=200, description="Limite por página"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([PerfilUsuario.SECRETARIA, PerfilUsuario.ADMIN, PerfilUsuario.PROFESSOR]))
) -> list[AlunoResponse]:
    """
    Retorna a listagem de alunos cadastrados com suporte a busca dinâmica por texto.
    """
    aluno_service = AlunoService(db)
    alunos = aluno_service.listar_alunos(
        busca=busca,
        apenas_ativos=apenas_ativos,
        skip=skip,
        limit=limit
    )
    return [AlunoResponse.model_validate(a) for a in alunos]


@router.get(
    "/{aluno_id}",
    response_model=AlunoResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes de um aluno por ID"
)
def obter_aluno(
    aluno_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
) -> AlunoResponse:
    """
    Retorna os detalhes completos de um aluno específico pelo seu UUID.
    """
    aluno_service = AlunoService(db)
    try:
        aluno = aluno_service.obter_aluno_por_id(aluno_id)
        return AlunoResponse.model_validate(aluno)
    except EntidadeNaoEncontradaError as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=erro.mensagem
        )


@router.put(
    "/{aluno_id}",
    response_model=AlunoResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar dados cadastrais do aluno"
)
def atualizar_aluno(
    aluno_id: uuid.UUID,
    dados: AlunoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([PerfilUsuario.SECRETARIA, PerfilUsuario.ADMIN]))
) -> AlunoResponse:
    """
    Atualiza informações cadastrais do aluno (nome, telefone, data de nascimento, status).
    Acesso restrito para SECRETARIA e ADMIN.
    """
    aluno_service = AlunoService(db)
    try:
        aluno_atualizado = aluno_service.atualizar_aluno(aluno_id, dados)
        return AlunoResponse.model_validate(aluno_atualizado)
    except EntidadeNaoEncontradaError as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=erro.mensagem
        )


@router.patch(
    "/{aluno_id}/inativar",
    response_model=AlunoResponse,
    status_code=status.HTTP_200_OK,
    summary="Inativar aluno (Soft Delete)"
)
def inativar_aluno(
    aluno_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([PerfilUsuario.SECRETARIA, PerfilUsuario.ADMIN]))
) -> AlunoResponse:
    """
    Realiza o Soft Delete do aluno: altera seu status para INATIVO e bloqueia o acesso do usuário.
    Acesso restrito para SECRETARIA e ADMIN.
    """
    aluno_service = AlunoService(db)
    try:
        aluno_inativado = aluno_service.inativar_aluno(aluno_id)
        return AlunoResponse.model_validate(aluno_inativado)
    except EntidadeNaoEncontradaError as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=erro.mensagem
        )
