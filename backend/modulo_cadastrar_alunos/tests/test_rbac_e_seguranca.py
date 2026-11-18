"""Testes da User Story 3: Governança de acesso por perfil (RBAC) e trilha de auditoria LGPD (SGA-15)."""

import pytest
from fastapi.testclient import TestClient
from modulo_cadastrar_alunos.repository import AlunoRepository
from modulo_cadastrar_alunos.security import criar_token_sessao, hash_password
from .conftest import gerar_cpf_valido


@pytest.mark.parametrize(
    ("perfil_id", "login_operador"),
    [
        (1, "aluno.sem.permissao@uneb.br"),
        (2, "professor.sem.permissao@uneb.br"),
        (4, "financeiro.sem.permissao@uneb.br"),
    ],
)
def test_perfis_nao_autorizados_recebem_403_forbidden(
    client: TestClient,
    repo: AlunoRepository,
    perfil_id: int,
    login_operador: str,
) -> None:
    uid = repo.inserir_usuario_seed(
        login=login_operador,
        senha_hash=hash_password("Senha@2026", rounds=4),
        perfil_id=perfil_id,
        status_conta=1,
    )
    token = criar_token_sessao(usuario_id=uid, perfil_id=perfil_id)
    headers = {"Authorization": f"Bearer {token}"}

    r_get = client.get("/api/alunos", headers=headers)
    assert r_get.status_code == 403

    r_post = client.post(
        "/api/alunos",
        json={
            "nome": "Tentativa Indevida",
            "cpf": gerar_cpf_valido("701702703"),
            "email": "indevido@uneb.br",
            "login": "indevido.login",
            "senha_inicial": "SenhaForte@2026",
        },
        headers=headers,
    )
    assert r_post.status_code == 403


def test_requisicoes_sem_token_token_invalido_ou_operador_inativo_sao_bloqueadas(
    client: TestClient,
    repo: AlunoRepository,
) -> None:
    # Sem cabeçalho Authorization
    assert client.get("/api/alunos").status_code == 401

    # Token malformado / assinatura inválida
    assert client.get("/api/alunos", headers={"Authorization": "Bearer token.invalido"}).status_code == 401

    # Token expirado
    uid_ativo = repo.inserir_usuario_seed(
        login="sec.expirado@uneb.br",
        senha_hash=hash_password("Senha@2026", rounds=4),
        perfil_id=3,
        status_conta=1,
    )
    token_expirado = criar_token_sessao(usuario_id=uid_ativo, perfil_id=3, ttl_segundos=-10)
    assert (
        client.get("/api/alunos", headers={"Authorization": f"Bearer {token_expirado}"}).status_code
        == 401
    )

    # Operador Secretaria com conta inativa (statusCONTA = 0)
    uid_inativo = repo.inserir_usuario_seed(
        login="sec.inativa@uneb.br",
        senha_hash=hash_password("Senha@2026", rounds=4),
        perfil_id=3,
        status_conta=0,
    )
    token_inativo = criar_token_sessao(usuario_id=uid_inativo, perfil_id=3)
    assert (
        client.get("/api/alunos", headers={"Authorization": f"Bearer {token_inativo}"}).status_code
        == 403
    )


def test_trilha_de_auditoria_registra_operacoes_e_higieniza_segredos_lgpd(
    client: TestClient,
    secretaria_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    cpf_valido = gerar_cpf_valido("801802803")
    senha_plana = "SegredoSuperConfidencial@2026"

    # 1. CRIAR por Secretaria
    r_criar = client.post(
        "/api/alunos",
        json={
            "nome": "Helena Martins",
            "cpf": cpf_valido,
            "email": "helena.martins@uneb.br",
            "curso_id": 1,
            "login": "helena.martins",
            "senha_inicial": senha_plana,
        },
        headers=secretaria_headers,
    )
    assert r_criar.status_code == 201
    matricula = r_criar.json()["matricula"]

    # 2. ATUALIZAR por Admin
    r_atualizar = client.put(
        f"/api/alunos/{matricula}",
        json={
            "nome": "Helena Martins Silva",
            "cpf": cpf_valido,
            "email": "helena.silva@uneb.br",
            "curso_id": 1,
            "login": "helena.silva",
            "status_academico": "ATIVO",
        },
        headers=admin_headers,
    )
    assert r_atualizar.status_code == 200

    # 3. ALTERAR_STATUS por Secretaria
    r_status = client.patch(
        f"/api/alunos/{matricula}/status",
        json={"ativo": False},
        headers=secretaria_headers,
    )
    assert r_status.status_code == 200

    # Consulta da trilha de auditoria filtrada pela matrícula
    r_audit = client.get(
        f"/api/alunos/auditoria?id_registro_afetado={matricula}",
        headers=secretaria_headers,
    )
    assert r_audit.status_code == 200
    eventos = r_audit.json()
    assert len(eventos) == 3

    acoes = [e["acao"] for e in eventos]
    assert acoes == ["ALTERAR_STATUS", "ATUALIZAR", "CRIAR"]

    for ev in eventos:
        assert ev["entidade_afetada"] == "Aluno"
        assert ev["id_registro_afetado"] == str(matricula)
        texto_serializado = f"{ev['dados_anteriores'] or ''} {ev['dados_novos'] or ''}"
        assert senha_plana not in texto_serializado
        assert "senha_hash" not in texto_serializado
        assert "senha_inicial" not in texto_serializado
