"""Testes da US4: Governança de Acesso RBAC e Trilha de Auditoria LGPD (SGA-27)."""

from typing import Any
from fastapi.testclient import TestClient

from .conftest import auth_header


def test_rbac_bloqueia_anonimos_tokens_invalidos_perfis_sem_permissao_e_conta_inativa(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    p_atual = dados_base["periodo_atual"]
    req_id = dados_base["requerimentos"]["aberto"]
    rotas = [
        ("GET", "/api/coordenacao/painel/resumo", None),
        ("GET", "/api/coordenacao/relatorios/evasao", None),
        ("GET", "/api/coordenacao/oferta/turmas", None),
        ("GET", f"/api/coordenacao/oferta/conflitos?periodo_letivo_id={p_atual}", None),
        ("GET", "/api/coordenacao/requerimentos", None),
        ("GET", f"/api/coordenacao/requerimentos/{req_id}", None),
        (
            "PATCH",
            f"/api/coordenacao/requerimentos/{req_id}/despachar",
            {"novo_status": "EM_ANALISE", "parecer": "Parecer de validação RBAC."},
        ),
        ("DELETE", f"/api/coordenacao/requerimentos/{req_id}", None),
        ("GET", "/api/coordenacao/docentes/alocacao", None),
        ("GET", "/api/coordenacao/auditoria", None),
    ]

    for metodo, url, payload in rotas:
        assert client.request(metodo, url, json=payload).status_code == 401
        assert client.request(metodo, url, json=payload, headers=auth_header("token.invalido")).status_code == 401
        assert (
            client.request(metodo, url, json=payload, headers=auth_header(dados_base["tokens"]["expirado"])).status_code
            == 401
        )
        for perfil in ("aluno", "professor", "financeiro", "inativo"):
            resp = client.request(metodo, url, json=payload, headers=auth_header(dados_base["tokens"][perfil]))
            assert resp.status_code == 403, f"{metodo} {url} deveria retornar 403 para {perfil}"


def test_trilha_auditoria_registra_despachos_com_ip_e_higienizacao_lgpd(
    client: TestClient, dados_base: dict[str, Any]
) -> None:
    req_id = dados_base["requerimentos"]["aberto"]
    headers_sec = {
        **auth_header(dados_base["tokens"]["secretaria"]),
        "X-Forwarded-For": "203.0.113.77, 10.0.0.5",
    }
    headers_admin = auth_header(dados_base["tokens"]["admin"])

    r_desp = client.patch(
        f"/api/coordenacao/requerimentos/{req_id}/despachar",
        json={"novo_status": "DEFERIDO", "parecer": "Deferido pela coordenação do curso."},
        headers=headers_sec,
    )
    assert r_desp.status_code == 200

    r_aud = client.get(
        "/api/coordenacao/auditoria",
        params={"id_registro_afetado": "REQ-2026-0001"},
        headers=headers_admin,
    )
    assert r_aud.status_code == 200
    eventos = r_aud.json()
    assert len(eventos) == 1
    ev = eventos[0]
    assert ev["usuario_id"] == dados_base["usuarios"]["secretaria"]
    assert ev["entidade_afetada"] == "RequerimentoAcademico"
    assert ev["id_registro_afetado"] == "REQ-2026-0001"
    assert ev["acao"] == "DESPACHAR"
    assert ev["ip_origem"] == "203.0.113.77"
    assert "ABERTO" in (ev["dados_anteriores"] or "")
    assert "DEFERIDO" in (ev["dados_novos"] or "")

    # Nenhum dado pessoal sensível LGPD nos registros de auditoria
    aud_texto = r_aud.text.lower()
    for sensivel in ("52998224725", "beatriz@sga.edu.br", "71999998888", "hash_fake", "senha"):
        assert sensivel not in aud_texto
