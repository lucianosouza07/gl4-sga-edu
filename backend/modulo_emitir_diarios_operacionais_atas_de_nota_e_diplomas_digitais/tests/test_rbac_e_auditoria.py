"""Testes da US4: Governança de Acesso RBAC e Trilha de Auditoria LGPD (SGA-25)."""

from typing import Any
from fastapi.testclient import TestClient

from .conftest import auth_header


def test_rbac_bloqueia_anonimos_e_tokens_invalidos_em_rotas_administrativas(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    rotas_admin = [
        ("POST", "/api/documentos/diarios-operacionais", {"turma_id": dados_base["turma_consolidada_id"]}),
        ("POST", "/api/documentos/atas-notas", {"turma_id": dados_base["turma_consolidada_id"]}),
        (
            "POST",
            "/api/documentos/diplomas",
            {
                "aluno_matricula": dados_base["mat_formado"],
                "data_conclusao": "2026-11-10",
                "data_colacao_grau": "2026-11-20",
            },
        ),
        ("GET", "/api/documentos", None),
        ("GET", "/api/documentos/auditoria", None),
        ("GET", "/api/documentos/1", None),
        ("POST", "/api/documentos/1/verificar-integridade", None),
        ("PATCH", "/api/documentos/1/revogar", {"motivo": "Motivo válido de teste"}),
        ("DELETE", "/api/documentos/1", None),
    ]

    for metodo, url, payload in rotas_admin:
        # Sem autenticação -> 401
        r_anon = client.request(metodo, url, json=payload)
        assert r_anon.status_code == 401, f"{metodo} {url} deveria retornar 401 sem token"

        # Token expirado -> 401
        r_exp = client.request(metodo, url, json=payload, headers=auth_header(dados_base["tokens"]["expirado"]))
        assert r_exp.status_code == 401, f"{metodo} {url} deveria retornar 401 com token expirado"

        # Token adulterado -> 401
        r_bad = client.request(metodo, url, json=payload, headers=auth_header("token.invalido"))
        assert r_bad.status_code == 401, f"{metodo} {url} deveria retornar 401 com token inválido"


def test_rbac_bloqueia_perfis_nao_autorizados_e_conta_inativa(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    perfis_negados = ("aluno", "professor", "financeiro", "inativo")
    for perfil in perfis_negados:
        headers = auth_header(dados_base["tokens"][perfil])

        assert (
            client.post(
                "/api/documentos/diarios-operacionais",
                json={"turma_id": dados_base["turma_consolidada_id"]},
                headers=headers,
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/documentos/atas-notas",
                json={"turma_id": dados_base["turma_consolidada_id"]},
                headers=headers,
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/documentos/diplomas",
                json={
                    "aluno_matricula": dados_base["mat_formado"],
                    "data_conclusao": "2026-11-10",
                    "data_colacao_grau": "2026-11-20",
                },
                headers=headers,
            ).status_code
            == 403
        )
        assert client.get("/api/documentos", headers=headers).status_code == 403
        assert client.get("/api/documentos/auditoria", headers=headers).status_code == 403


def test_trilha_auditoria_registra_emissao_integridade_revogacao_com_higienizacao_lgpd(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    headers_sec = {
        **auth_header(dados_base["tokens"]["secretaria"]),
        "X-Forwarded-For": "203.0.113.45, 10.0.0.1",
    }
    headers_admin = {
        **auth_header(dados_base["tokens"]["admin"]),
        "X-Forwarded-For": "198.51.100.22",
    }

    # 1. Emitir diploma (Secretaria)
    doc = client.post(
        "/api/documentos/diplomas",
        json={
            "aluno_matricula": dados_base["mat_formado"],
            "data_conclusao": "2026-11-10",
            "data_colacao_grau": "2026-11-20",
        },
        headers=headers_sec,
    ).json()

    # 2. Verificar integridade (Admin)
    r_int = client.post(
        f"/api/documentos/{doc['id_documento']}/verificar-integridade",
        headers=headers_admin,
    )
    assert r_int.status_code == 200

    # 3. Revogar documento (Secretaria)
    r_rev = client.patch(
        f"/api/documentos/{doc['id_documento']}/revogar",
        json={"motivo": "Correção administrativa de número de livro"},
        headers=headers_sec,
    )
    assert r_rev.status_code == 200

    # Consultar trilha filtrada pelo documento
    r_aud = client.get(
        "/api/documentos/auditoria",
        params={"id_documento": str(doc["id_documento"])},
        headers=headers_admin,
    )
    assert r_aud.status_code == 200
    eventos = r_aud.json()
    assert len(eventos) == 3

    # Ordenado do mais recente para o mais antigo: REVOGAR, VERIFICAR_INTEGRIDADE, EMITIR
    assert [e["acao"] for e in eventos] == ["REVOGAR", "VERIFICAR_INTEGRIDADE", "EMITIR"]
    assert eventos[0]["usuario_id"] == dados_base["usuarios"]["secretaria"]
    assert eventos[0]["ip_origem"] == "203.0.113.45"
    assert eventos[1]["usuario_id"] == dados_base["usuarios"]["admin"]
    assert eventos[1]["ip_origem"] == "198.51.100.22"
    assert eventos[2]["usuario_id"] == dados_base["usuarios"]["secretaria"]
    assert eventos[2]["entidade_afetada"] == "DocumentoAcademico"
    assert eventos[2]["id_registro_afetado"] == str(doc["id_documento"])

    # Nenhum dado pessoal sensível LGPD nos registros de auditoria
    aud_texto = r_aud.text.lower()
    for sensivel in ("52998224725", "ana.clara@sga.edu.br", "71999990000", "hash_fake", "senha"):
        assert sensivel not in aud_texto
