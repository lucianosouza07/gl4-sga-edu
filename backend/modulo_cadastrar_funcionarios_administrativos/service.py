"""Regras de negócio para gestão de funcionários administrativos (SGA-19)."""

import sqlite3
from typing import Any, Optional
from fastapi import HTTPException, status

try:
    from .audit_service import sanitizar_snapshot
    from .repository import FuncionarioAdminRepository
    from .schemas import (
        PERFIL_ADMIN_ID,
        PERFIL_NOME_PARA_ID,
        AuditoriaEventoResponse,
        FuncionarioAdminCreate,
        FuncionarioAdminResponse,
        FuncionarioAdminStatusUpdate,
        FuncionarioAdminUpdate,
        MensagemResponse,
        PerfilAdminEnum,
    )
    from .security import OperadorAutenticado, hash_password
except ImportError:
    from audit_service import sanitizar_snapshot
    from repository import FuncionarioAdminRepository
    from schemas import (
        PERFIL_ADMIN_ID,
        PERFIL_NOME_PARA_ID,
        AuditoriaEventoResponse,
        FuncionarioAdminCreate,
        FuncionarioAdminResponse,
        FuncionarioAdminStatusUpdate,
        FuncionarioAdminUpdate,
        MensagemResponse,
        PerfilAdminEnum,
    )
    from security import OperadorAutenticado, hash_password


def _traduzir_conflito_integridade(exc: sqlite3.IntegrityError) -> HTTPException:
    texto = str(exc).lower()
    if "cpf" in texto:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um funcionário administrativo com esse CPF.",
        )
    if "login" in texto:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta de usuário com esse login.",
        )
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Conflito de integridade cadastral.",
    )


def _checar_duplicidades(
    repo: FuncionarioAdminRepository,
    cpf: str,
    login: str,
    ignorar_funcionario_id: Optional[int] = None,
    ignorar_usuario_id: Optional[int] = None,
) -> None:
    existente_cpf = repo.buscar_por_cpf(cpf)
    if existente_cpf and existente_cpf["id_funcionario"] != ignorar_funcionario_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um funcionário administrativo com esse CPF.",
        )

    existente_login = repo.buscar_usuario_por_login(login)
    if existente_login and existente_login["id_usuario"] != ignorar_usuario_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta de usuário com esse login.",
        )


def _garantir_protecao_admin(
    repo: FuncionarioAdminRepository,
    alvo: dict[str, Any],
    operador: OperadorAutenticado,
    alteracao_critica: bool,
) -> None:
    """Impede autoalteração destrutiva/rebaixamento ou perda do último Admin ativo."""
    if not alteracao_critica:
        return

    if int(alvo["usuario_id"]) == operador.usuario_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é permitido inativar, rebaixar ou excluir a própria conta administrativa.",
        )

    if int(alvo["perfil_id"]) == PERFIL_ADMIN_ID and bool(alvo["ativo"]):
        if repo.contar_admins_ativos() <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Operação bloqueada: é obrigatório manter ao menos um administrador ativo.",
            )


def _snapshot_publico(registro: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_funcionario": registro["id_funcionario"],
        "usuario_id": registro["usuario_id"],
        "nome": registro["nome"],
        "cpf": registro["cpf"],
        "login": registro["login"],
        "setor": registro["setor"],
        "cargo": registro["cargo"],
        "perfil": registro["perfil"],
        "perfil_id": registro["perfil_id"],
        "ativo": registro["ativo"],
        "senha_provisoria": registro["senha_provisoria"],
    }


def _obter_ou_404(repo: FuncionarioAdminRepository, funcionario_id: int) -> dict[str, Any]:
    registro = repo.buscar_por_id(funcionario_id)
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Funcionário administrativo não encontrado.",
        )
    return registro


def cadastrar_funcionario(
    repo: FuncionarioAdminRepository,
    dados: FuncionarioAdminCreate,
    operador: OperadorAutenticado,
    ip_origem: str,
) -> FuncionarioAdminResponse:
    """Cria conjuntamente Usuario e FuncionarioAdministrativo com registro de auditoria."""
    _checar_duplicidades(repo, cpf=dados.cpf, login=dados.login)

    perfil_id = PERFIL_NOME_PARA_ID[dados.perfil.value]
    senha_hash = hash_password(dados.senha_inicial)
    snapshot_novo = sanitizar_snapshot(
        {
            "nome": dados.nome,
            "cpf": dados.cpf,
            "login": dados.login,
            "setor": dados.setor,
            "cargo": dados.cargo,
            "perfil": dados.perfil.value,
            "perfil_id": perfil_id,
            "ativo": True,
            "senha_provisoria": True,
        }
    )

    try:
        registro = repo.criar_funcionario_e_usuario(
            nome=dados.nome,
            cpf=dados.cpf,
            login=dados.login,
            senha_hash=senha_hash,
            setor=dados.setor,
            cargo=dados.cargo,
            perfil_id=perfil_id,
            operador_usuario_id=operador.usuario_id,
            ip_origem=ip_origem,
            dados_novos_json=snapshot_novo,
        )
    except sqlite3.IntegrityError as exc:
        raise _traduzir_conflito_integridade(exc) from exc

    return FuncionarioAdminResponse(**registro)


def listar_funcionarios(
    repo: FuncionarioAdminRepository,
    perfil: Optional[PerfilAdminEnum] = None,
    setor: Optional[str] = None,
    ativo: Optional[bool] = None,
) -> list[FuncionarioAdminResponse]:
    """Lista funcionários administrativos ordenados por nome e filtrados conforme parâmetros."""
    perfil_id = PERFIL_NOME_PARA_ID[perfil.value] if perfil is not None else None
    registros = repo.listar_funcionarios(perfil_id=perfil_id, setor=setor, ativo=ativo)
    return [FuncionarioAdminResponse(**item) for item in registros]


def detalhar_funcionario(repo: FuncionarioAdminRepository, funcionario_id: int) -> FuncionarioAdminResponse:
    """Retorna os detalhes de um funcionário administrativo por ID ou HTTP 404."""
    return FuncionarioAdminResponse(**_obter_ou_404(repo, funcionario_id))


def consultar_auditoria(
    repo: FuncionarioAdminRepository,
    id_registro_afetado: Optional[str] = None,
) -> list[AuditoriaEventoResponse]:
    """Consulta eventos registrados em LogAuditoriaSistema para funcionários administrativos."""
    eventos = repo.listar_auditoria(id_registro_afetado=id_registro_afetado)
    return [AuditoriaEventoResponse(**ev) for ev in eventos]


def atualizar_funcionario(
    repo: FuncionarioAdminRepository,
    funcionario_id: int,
    dados: FuncionarioAdminUpdate,
    operador: OperadorAutenticado,
    ip_origem: str,
) -> FuncionarioAdminResponse:
    """Atualiza dados cadastrais e perfil RBAC administrativo preservando invariantes."""
    atual = _obter_ou_404(repo, funcionario_id)
    novo_perfil_id = PERFIL_NOME_PARA_ID[dados.perfil.value]

    rebaixando_admin = int(atual["perfil_id"]) == PERFIL_ADMIN_ID and novo_perfil_id != PERFIL_ADMIN_ID
    _garantir_protecao_admin(repo, alvo=atual, operador=operador, alteracao_critica=rebaixando_admin)

    _checar_duplicidades(
        repo,
        cpf=dados.cpf,
        login=dados.login,
        ignorar_funcionario_id=funcionario_id,
        ignorar_usuario_id=int(atual["usuario_id"]),
    )

    snapshot_antes = sanitizar_snapshot(_snapshot_publico(atual))
    snapshot_depois = sanitizar_snapshot(
        {
            **_snapshot_publico(atual),
            "nome": dados.nome,
            "cpf": dados.cpf,
            "login": dados.login,
            "setor": dados.setor,
            "cargo": dados.cargo,
            "perfil": dados.perfil.value,
            "perfil_id": novo_perfil_id,
        }
    )

    try:
        atualizado = repo.atualizar_funcionario(
            funcionario_id=funcionario_id,
            usuario_id=int(atual["usuario_id"]),
            nome=dados.nome,
            cpf=dados.cpf,
            login=dados.login,
            setor=dados.setor,
            cargo=dados.cargo,
            perfil_id=novo_perfil_id,
            operador_usuario_id=operador.usuario_id,
            ip_origem=ip_origem,
            dados_anteriores_json=snapshot_antes,
            dados_novos_json=snapshot_depois,
        )
    except sqlite3.IntegrityError as exc:
        raise _traduzir_conflito_integridade(exc) from exc

    return FuncionarioAdminResponse(**atualizado)


def alterar_status(
    repo: FuncionarioAdminRepository,
    funcionario_id: int,
    dados: FuncionarioAdminStatusUpdate,
    operador: OperadorAutenticado,
    ip_origem: str,
) -> FuncionarioAdminResponse:
    """Ativa ou inativa conta administrativa respeitando autoproteção e mínimo de Admin ativo."""
    atual = _obter_ou_404(repo, funcionario_id)
    desativando = bool(atual["ativo"]) and not dados.ativo
    _garantir_protecao_admin(repo, alvo=atual, operador=operador, alteracao_critica=desativando)

    snapshot_antes = sanitizar_snapshot(_snapshot_publico(atual))
    snapshot_depois = sanitizar_snapshot({**_snapshot_publico(atual), "ativo": dados.ativo})

    atualizado = repo.alterar_status_funcionario(
        funcionario_id=funcionario_id,
        usuario_id=int(atual["usuario_id"]),
        ativo=dados.ativo,
        operador_usuario_id=operador.usuario_id,
        ip_origem=ip_origem,
        dados_anteriores_json=snapshot_antes,
        dados_novos_json=snapshot_depois,
    )
    return FuncionarioAdminResponse(**atualizado)


def excluir_funcionario(
    repo: FuncionarioAdminRepository,
    funcionario_id: int,
    operador: OperadorAutenticado,
    ip_origem: str,
) -> MensagemResponse:
    """Remove funcionário administrativo e usuário em cascata mantendo histórico de auditoria."""
    atual = _obter_ou_404(repo, funcionario_id)
    _garantir_protecao_admin(repo, alvo=atual, operador=operador, alteracao_critica=True)

    snapshot_antes = sanitizar_snapshot(_snapshot_publico(atual))
    repo.excluir_funcionario(
        funcionario_id=funcionario_id,
        usuario_id=int(atual["usuario_id"]),
        operador_usuario_id=operador.usuario_id,
        ip_origem=ip_origem,
        dados_anteriores_json=snapshot_antes,
    )
    return MensagemResponse(mensagem="Funcionário administrativo removido.")
