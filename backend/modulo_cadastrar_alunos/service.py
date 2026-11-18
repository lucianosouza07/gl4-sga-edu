"""Regras de negócio para cadastro e gestão de alunos do SGA-Edu (SGA-15)."""

import sqlite3
from typing import Any, Optional
from fastapi import HTTPException, status

try:
    from .audit_service import sanitizar_snapshot
    from .repository import AlunoRepository
    from .schemas import (
        PERFIL_ALUNO_ID,
        PERFIL_ALUNO_NOME,
        AlunoCreate,
        AlunoResponse,
        AlunoStatusUpdate,
        AlunoUpdate,
        AuditoriaEventoResponse,
        StatusAcademicoEnum,
    )
    from .security import OperadorAutenticado, hash_password
except ImportError:
    from audit_service import sanitizar_snapshot
    from repository import AlunoRepository
    from schemas import (
        PERFIL_ALUNO_ID,
        PERFIL_ALUNO_NOME,
        AlunoCreate,
        AlunoResponse,
        AlunoStatusUpdate,
        AlunoUpdate,
        AuditoriaEventoResponse,
        StatusAcademicoEnum,
    )
    from security import OperadorAutenticado, hash_password


def _traduzir_conflito_integridade(exc: sqlite3.IntegrityError) -> HTTPException:
    texto = str(exc).lower()
    if "matricula" in texto:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um aluno cadastrado com esse número de matrícula.",
        )
    if "cpf" in texto:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um aluno cadastrado com esse CPF.",
        )
    if "email" in texto:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um aluno cadastrado com esse e-mail.",
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


def _validar_curso_se_informado(repo: AlunoRepository, curso_id: Optional[int]) -> Optional[dict[str, Any]]:
    if curso_id is None:
        return None
    curso = repo.buscar_curso_por_id(curso_id)
    if curso is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso informado não encontrado.",
        )
    return curso


def _checar_duplicidades(
    repo: AlunoRepository,
    cpf: str,
    email: str,
    login: str,
    matricula: Optional[int] = None,
    ignorar_matricula: Optional[int] = None,
    ignorar_usuario_id: Optional[int] = None,
) -> None:
    if matricula is not None:
        existente_matricula = repo.buscar_por_matricula(matricula)
        if existente_matricula and existente_matricula["matricula"] != ignorar_matricula:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um aluno cadastrado com esse número de matrícula.",
            )

    existente_cpf = repo.buscar_por_cpf(cpf)
    if existente_cpf and existente_cpf["matricula"] != ignorar_matricula:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um aluno cadastrado com esse CPF.",
        )

    existente_email = repo.buscar_por_email(email)
    if existente_email and existente_email["matricula"] != ignorar_matricula:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um aluno cadastrado com esse e-mail.",
        )

    existente_login = repo.buscar_usuario_por_login(login)
    if existente_login and existente_login["id_usuario"] != ignorar_usuario_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta de usuário com esse login.",
        )


def _snapshot_publico(registro: dict[str, Any]) -> dict[str, Any]:
    return {
        "matricula": registro["matricula"],
        "usuario_id": registro["usuario_id"],
        "nome": registro["nome"],
        "cpf": registro["cpf"],
        "email": registro["email"],
        "telefone": registro["telefone"],
        "data_nascimento": registro["data_nascimento"],
        "curso_id": registro["curso_id"],
        "status_academico": registro["status_academico"],
        "ira": registro["ira"],
        "login": registro["login"],
        "perfil": registro["perfil"],
        "perfil_id": registro["perfil_id"],
        "ativo": registro["ativo"],
        "senha_provisoria": registro["senha_provisoria"],
    }


def _obter_ou_404(repo: AlunoRepository, matricula: int) -> dict[str, Any]:
    registro = repo.buscar_por_matricula(matricula)
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado.",
        )
    return registro


def cadastrar_aluno(
    repo: AlunoRepository,
    dados: AlunoCreate,
    operador: OperadorAutenticado,
    ip_origem: str,
) -> AlunoResponse:
    """Cria atomicamente Usuario (perfil Aluno), Aluno e registro de auditoria CRIAR."""
    _validar_curso_se_informado(repo, dados.curso_id)
    _checar_duplicidades(
        repo=repo,
        cpf=dados.cpf,
        email=dados.email,
        login=dados.login,
        matricula=dados.matricula,
    )

    senha_hash = hash_password(dados.senha_inicial)
    snapshot_base = {
        "nome": dados.nome,
        "cpf": dados.cpf,
        "email": dados.email,
        "telefone": dados.telefone,
        "data_nascimento": dados.data_nascimento,
        "curso_id": dados.curso_id,
        "status_academico": StatusAcademicoEnum.ATIVO.value,
        "ira": 0.0,
        "login": dados.login,
        "perfil": PERFIL_ALUNO_NOME,
        "perfil_id": PERFIL_ALUNO_ID,
        "ativo": True,
        "senha_provisoria": True,
    }

    try:
        registro = repo.criar_aluno_e_usuario(
            nome=dados.nome,
            cpf=dados.cpf,
            email=dados.email,
            telefone=dados.telefone,
            data_nascimento=dados.data_nascimento,
            curso_id=dados.curso_id,
            matricula=dados.matricula,
            login=dados.login,
            senha_hash=senha_hash,
            operador_usuario_id=operador.usuario_id,
            ip_origem=ip_origem,
            snapshot_base=snapshot_base,
        )
    except sqlite3.IntegrityError as exc:
        raise _traduzir_conflito_integridade(exc) from exc

    return AlunoResponse(**registro)


def listar_alunos(
    repo: AlunoRepository,
    status_academico: Optional[StatusAcademicoEnum] = None,
    curso_id: Optional[int] = None,
    ativo: Optional[bool] = None,
    busca: Optional[str] = None,
) -> list[AlunoResponse]:
    """Lista alunos ordenados alfabeticamente por nome e filtrados pelos parâmetros opcionais."""
    status_val = status_academico.value if status_academico is not None else None
    registros = repo.listar_alunos(
        status_academico=status_val,
        curso_id=curso_id,
        ativo=ativo,
        busca=busca,
    )
    return [AlunoResponse(**item) for item in registros]


def detalhar_aluno(repo: AlunoRepository, matricula: int) -> AlunoResponse:
    """Retorna os detalhes de um aluno pelo número de matrícula ou HTTP 404."""
    return AlunoResponse(**_obter_ou_404(repo, matricula))


def atualizar_aluno(
    repo: AlunoRepository,
    matricula: int,
    dados: AlunoUpdate,
    operador: OperadorAutenticado,
    ip_origem: str,
) -> AlunoResponse:
    """Atualiza dados pessoais, de contato, curso, login e situação acadêmica de um aluno."""
    atual = _obter_ou_404(repo, matricula)
    _validar_curso_se_informado(repo, dados.curso_id)
    _checar_duplicidades(
        repo=repo,
        cpf=dados.cpf,
        email=dados.email,
        login=dados.login,
        ignorar_matricula=matricula,
        ignorar_usuario_id=int(atual["usuario_id"]),
    )

    snapshot_antes = sanitizar_snapshot(_snapshot_publico(atual))
    snapshot_depois = sanitizar_snapshot(
        {
            **_snapshot_publico(atual),
            "nome": dados.nome,
            "cpf": dados.cpf,
            "email": dados.email,
            "telefone": dados.telefone,
            "data_nascimento": dados.data_nascimento,
            "curso_id": dados.curso_id,
            "login": dados.login,
            "status_academico": dados.status_academico.value,
        }
    )

    try:
        atualizado = repo.atualizar_aluno(
            matricula=matricula,
            usuario_id=int(atual["usuario_id"]),
            nome=dados.nome,
            cpf=dados.cpf,
            email=dados.email,
            telefone=dados.telefone,
            data_nascimento=dados.data_nascimento,
            curso_id=dados.curso_id,
            login=dados.login,
            status_academico=dados.status_academico.value,
            operador_usuario_id=operador.usuario_id,
            ip_origem=ip_origem,
            dados_anteriores_json=snapshot_antes,
            dados_novos_json=snapshot_depois,
        )
    except sqlite3.IntegrityError as exc:
        raise _traduzir_conflito_integridade(exc) from exc

    return AlunoResponse(**atualizado)


def alterar_status(
    repo: AlunoRepository,
    matricula: int,
    dados: AlunoStatusUpdate,
    operador: OperadorAutenticado,
    ip_origem: str,
) -> AlunoResponse:
    """Ativa ou inativa a conta de acesso do aluno preservando seu histórico acadêmico."""
    atual = _obter_ou_404(repo, matricula)
    snapshot_antes = sanitizar_snapshot(_snapshot_publico(atual))
    snapshot_depois = sanitizar_snapshot({**_snapshot_publico(atual), "ativo": dados.ativo})

    atualizado = repo.alterar_status_aluno(
        matricula=matricula,
        usuario_id=int(atual["usuario_id"]),
        ativo=dados.ativo,
        operador_usuario_id=operador.usuario_id,
        ip_origem=ip_origem,
        dados_anteriores_json=snapshot_antes,
        dados_novos_json=snapshot_depois,
    )
    return AlunoResponse(**atualizado)


def consultar_auditoria(
    repo: AlunoRepository,
    id_registro_afetado: Optional[str] = None,
) -> list[AuditoriaEventoResponse]:
    """Consulta eventos registrados em LogAuditoriaSistema para a entidade Aluno."""
    eventos = repo.listar_auditoria(id_registro_afetado=id_registro_afetado)
    return [AuditoriaEventoResponse(**ev) for ev in eventos]
