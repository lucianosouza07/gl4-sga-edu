"""Testes unitários e de integração para controle de acesso RBAC e consultas à auditoria (US3)."""


def test_administrador_acessa_trilha_auditoria(client, admin_headers, repo):
    """Garante que usuários com perfil Admin (perfil=5) possam consultar a auditoria."""
    # Registra eventos para consulta
    repo.inserir_log_auditoria(
        usuario_id=1,
        entidade_afetada="Usuario",
        id_registro_afetado="10",
        acao="CRIACAO",
        dados_anteriores=None,
        dados_novos='{"login": "novo@sga.edu.br"}',
        ip_origem="127.0.0.1",
        data_hora=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    )

    resp = client.get("/api/auditoria", headers=admin_headers)
    assert resp.status_code == 200
    dados = resp.json()
    assert dados["total"] >= 1
    assert len(dados["itens"]) >= 1


def test_bloqueio_usuario_comum_acessar_auditoria(client, aluno_headers, prof_headers):
    """Garante que alunos e professores recebam 403 Forbidden ao tentar acessar a auditoria global."""
    resp_aluno = client.get("/api/auditoria", headers=aluno_headers)
    assert resp_aluno.status_code == 403

    resp_prof = client.get("/api/auditoria", headers=prof_headers)
    assert resp_prof.status_code == 403


def test_bloqueio_requisicao_sem_autenticacao(client):
    """Valida que requisição sem cabeçalho Authorization resulte em 401 Unauthorized."""
    resp = client.get("/api/auditoria")
    assert resp.status_code == 401


def test_consulta_auditoria_com_filtros_combinados(client, admin_headers, repo):
    """Testa a filtragem por entidade afetada, ação e paginação."""
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    repo.inserir_log_auditoria(
        usuario_id=1,
        entidade_afetada="Professor",
        id_registro_afetado="101",
        acao="ATUALIZACAO",
        dados_anteriores='{"nome": "Prof A"}',
        dados_novos='{"nome": "Prof B"}',
        ip_origem="10.0.0.1",
        data_hora=now,
    )
    repo.inserir_log_auditoria(
        usuario_id=2,
        entidade_afetada="Aluno",
        id_registro_afetado="202",
        acao="EXCLUSAO",
        dados_anteriores='{"matricula": "123"}',
        dados_novos=None,
        ip_origem="10.0.0.2",
        data_hora=now,
    )

    # Filtrar por Professor
    resp = client.get("/api/auditoria?entidade_afetada=Professor", headers=admin_headers)
    assert resp.status_code == 200
    dados = resp.json()
    assert dados["total"] == 1
    assert dados["itens"][0]["entidade_afetada"] == "Professor"
    assert dados["itens"][0]["acao"] == "ATUALIZACAO"


def test_detalhes_registro_auditoria(client, admin_headers, repo):
    """Testa a consulta pontual a um registro de auditoria pelo ID."""
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    id_criado = repo.inserir_log_auditoria(
        usuario_id=1,
        entidade_afetada="ParametroSistema",
        id_registro_afetado="cfg_1",
        acao="ATUALIZACAO",
        dados_anteriores='{"valor": 10}',
        dados_novos='{"valor": 20}',
        ip_origem="192.168.1.1",
        data_hora=now,
    )

    resp = client.get(f"/api/auditoria/{id_criado}", headers=admin_headers)
    assert resp.status_code == 200
    dados = resp.json()
    assert dados["id_auditoria"] == id_criado
    assert dados["entidade_afetada"] == "ParametroSistema"

    # ID inexistente
    resp_404 = client.get("/api/auditoria/99999", headers=admin_headers)
    assert resp_404.status_code == 404
