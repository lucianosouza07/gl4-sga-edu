import pytest
from fastapi.testclient import TestClient

try:
    from main import app
    from schemas import StatusDiscente, TipoMovimentacao
    from services import servico_movimentacao
except ImportError:
    from .main import app
    from .schemas import StatusDiscente, TipoMovimentacao
    from .services import servico_movimentacao

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown():
    servico_movimentacao.reset_database()
    yield


# ==============================================================================
# FASE 3 / USER STORY 1: Trancamento e Destrancamento de Matrícula (MVP)
# ==============================================================================

def test_criar_discente_sucesso():
    payload = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
        "semestres_cursados": 2,
        "semestres_trancados": 0,
    }
    response = client.post("/api/movimentacao/discentes", json=payload)
    assert response.status_code == 201
    dados = response.json()
    assert dados["id"] == "DISC-0001"
    assert dados["matricula"] == "2024101001"
    assert dados["status"] == "ATIVO"
    assert dados["semestres_cursados"] == 2
    assert dados["semestres_trancados"] == 0


def test_criar_discente_duplicado():
    payload = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
    }
    res1 = client.post("/api/movimentacao/discentes", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/movimentacao/discentes", json=payload)
    assert res2.status_code == 400
    assert "Já existe discente" in res2.json()["detail"]


def test_obter_discente_inexistente():
    response = client.get("/api/movimentacao/discentes/DISC-9999")
    assert response.status_code == 404


def test_trancar_matricula_sucesso_e_desocupar_turmas():
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
        "semestres_cursados": 2,
        "semestres_trancados": 0,
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    # Simular matrícula em 2 turmas no semestre 2026.2
    servico_movimentacao.matricular_em_turma(discente_id, "TURMA-ENG-01", "2026.2")
    servico_movimentacao.matricular_em_turma(discente_id, "TURMA-ENG-02", "2026.2")

    trancamento_payload = {
        "discente_id": discente_id,
        "periodo_letivo": "2026.2",
        "justificativa": "Motivos profissionais e viagens a trabalho",
        "operador_id": "SEC_ADMIN_01",
        "excecao_motivo_medico": False,
    }
    res_tranc = client.post("/api/movimentacao/trancamento", json=trancamento_payload)
    assert res_tranc.status_code == 200
    dados = res_tranc.json()
    assert dados["tipo"] == "TRANCAMENTO"
    assert dados["status_anterior"] == "ATIVO"
    assert dados["status_novo"] == "TRANCADO"
    assert "CERT-TRANC-" in dados["codigo_autenticidade"]

    # Conferir discente atualizado
    d_atualizado = client.get(f"/api/movimentacao/discentes/{discente_id}").json()
    assert d_atualizado["status"] == "TRANCADO"
    assert d_atualizado["semestres_trancados"] == 1

    # Conferir turmas desocupadas
    inscricoes = servico_movimentacao.listar_inscricoes_turma(discente_id)
    assert len(inscricoes) == 2
    assert all(i.status == "CANCELADA_MOVIMENTACAO" for i in inscricoes)


def test_trancar_matricula_ja_trancada():
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
        "semestres_cursados": 2,
        "semestres_trancados": 1,
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    trancamento_payload = {
        "discente_id": discente_id,
        "periodo_letivo": "2026.2",
        "justificativa": "Motivo particular",
        "operador_id": "SEC_ADMIN_01",
    }
    res1 = client.post("/api/movimentacao/trancamento", json=trancamento_payload)
    assert res1.status_code == 200

    # Segunda tentativa no mesmo estado TRANCADO
    res2 = client.post("/api/movimentacao/trancamento", json=trancamento_payload)
    assert res2.status_code == 400
    assert "TRANCADO" in res2.json()["detail"]


def test_trancar_matricula_limite_excedido():
    # Limite é 4 semestres
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
        "semestres_cursados": 4,
        "semestres_trancados": 4,
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    trancamento_payload = {
        "discente_id": discente_id,
        "periodo_letivo": "2026.2",
        "justificativa": "Tentativa de trancar quinto semestre",
        "operador_id": "SEC_ADMIN_01",
    }
    res = client.post("/api/movimentacao/trancamento", json=trancamento_payload)
    assert res.status_code == 400
    assert "Limite máximo regulamentar" in res.json()["detail"]


def test_trancar_matricula_calouro_regras():
    payload_calouro = {
        "matricula": "2026101002",
        "nome": "Mariana Ramos",
        "cpf": "234.567.890-11",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2026.2",
        "semestres_cursados": 0,
        "semestres_trancados": 0,
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_calouro).json()
    discente_id = d_res["id"]

    # Tentativa sem exceção médica -> bloqueado
    res_bloq = client.post(
        "/api/movimentacao/trancamento",
        json={
            "discente_id": discente_id,
            "periodo_letivo": "2026.2",
            "justificativa": "Trancamento por conveniência",
            "operador_id": "SEC_ADMIN_01",
            "excecao_motivo_medico": False,
        },
    )
    assert res_bloq.status_code == 400
    assert "primeiro semestre" in res_bloq.json()["detail"]

    # Tentativa com exceção médica -> deferido
    res_ok = client.post(
        "/api/movimentacao/trancamento",
        json={
            "discente_id": discente_id,
            "periodo_letivo": "2026.2",
            "justificativa": "Tratamento cirúrgico com laudo médico anexo",
            "operador_id": "SEC_ADMIN_01",
            "excecao_motivo_medico": True,
        },
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["status_novo"] == "TRANCADO"


def test_destrancar_matricula_sucesso():
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
        "semestres_cursados": 2,
        "semestres_trancados": 1,
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    # Primeiro trancar
    client.post(
        "/api/movimentacao/trancamento",
        json={
            "discente_id": discente_id,
            "periodo_letivo": "2026.2",
            "justificativa": "Trancamento regular",
            "operador_id": "SEC_ADMIN_01",
        },
    )

    # Destrancar
    res_dest = client.post(
        "/api/movimentacao/destrancamento",
        json={
            "discente_id": discente_id,
            "periodo_letivo": "2027.1",
            "justificativa": "Retorno regular às aulas",
            "operador_id": "SEC_ADMIN_01",
        },
    )
    assert res_dest.status_code == 200
    dados = res_dest.json()
    assert dados["tipo"] == "DESTRANCAMENTO"
    assert dados["status_anterior"] == "TRANCADO"
    assert dados["status_novo"] == "ATIVO"

    d_final = client.get(f"/api/movimentacao/discentes/{discente_id}").json()
    assert d_final["status"] == "ATIVO"


def test_destrancar_aluno_ativo_rejeicao():
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
        "semestres_cursados": 2,
        "semestres_trancados": 0,
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    res = client.post(
        "/api/movimentacao/destrancamento",
        json={
            "discente_id": discente_id,
            "periodo_letivo": "2026.2",
            "justificativa": "Tentativa de destrancar aluno ativo",
            "operador_id": "SEC_ADMIN_01",
        },
    )
    assert res.status_code == 400
    assert "Destrancamento só é aplicável" in res.json()["detail"]


# ==============================================================================
# FASE 4 / USER STORY 2: Transferências Acadêmicas
# ==============================================================================

def test_transferencia_interna_sucesso_decrementa_vagas():
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
        "semestres_cursados": 2,
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    regra_cc_antes = servico_movimentacao.obter_regra_curso("CURSO_CC").vagas_transferencia_disponiveis

    transf_payload = {
        "discente_id": discente_id,
        "tipo_transferencia": "TRANSFERENCIA_INTERNA",
        "curso_destino_id": "CURSO_CC",
        "nome_curso_destino": "Ciência da Computação",
        "periodo_letivo": "2026.2",
        "justificativa": "Mudança de vocação acadêmica",
        "operador_id": "COORD_CC_01",
    }
    res = client.post("/api/movimentacao/transferencia", json=transf_payload)
    assert res.status_code == 200
    dados = res.json()
    assert dados["tipo"] == "TRANSFERENCIA_INTERNA"
    assert dados["status_novo"] == "TRANSFERIDO"
    assert dados["curso_origem_id"] == "CURSO_ENG_SOFT"
    assert dados["curso_destino_id"] == "CURSO_CC"

    regra_cc_depois = servico_movimentacao.obter_regra_curso("CURSO_CC").vagas_transferencia_disponiveis
    assert regra_cc_depois == regra_cc_antes - 1

    d_atual = client.get(f"/api/movimentacao/discentes/{discente_id}").json()
    assert d_atual["curso_id"] == "CURSO_CC"
    assert d_atual["nome_curso"] == "Ciência da Computação"


def test_transferencia_interna_mesmo_curso_rejeicao():
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    transf_payload = {
        "discente_id": discente_id,
        "tipo_transferencia": "TRANSFERENCIA_INTERNA",
        "curso_destino_id": "CURSO_ENG_SOFT",
        "periodo_letivo": "2026.2",
        "justificativa": "Tentativa de transferir para o mesmo curso",
        "operador_id": "COORD_01",
    }
    res = client.post("/api/movimentacao/transferencia", json=transf_payload)
    assert res.status_code == 400
    assert "não pode ser idêntico" in res.json()["detail"]


def test_transferencia_interna_sem_vagas_rejeicao():
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    # CURSO_SI está configurado com 0 vagas de transferência
    transf_payload = {
        "discente_id": discente_id,
        "tipo_transferencia": "TRANSFERENCIA_INTERNA",
        "curso_destino_id": "CURSO_SI",
        "periodo_letivo": "2026.2",
        "justificativa": "Transferência para SI",
        "operador_id": "COORD_01",
    }
    res = client.post("/api/movimentacao/transferencia", json=transf_payload)
    assert res.status_code == 400
    assert "Não há vagas disponíveis" in res.json()["detail"]


def test_transferencia_externa_saida_sucesso():
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    servico_movimentacao.matricular_em_turma(discente_id, "TURMA-ENG-01", "2026.2")

    transf_payload = {
        "discente_id": discente_id,
        "tipo_transferencia": "TRANSFERENCIA_EXTERNA_SAIDA",
        "instituicao_destino": "Universidade Federal de Tecnologia",
        "periodo_letivo": "2026.2",
        "justificativa": "Mudança para outra cidade",
        "operador_id": "SEC_ADMIN_01",
    }
    res = client.post("/api/movimentacao/transferencia", json=transf_payload)
    assert res.status_code == 200
    dados = res.json()
    assert dados["tipo"] == "TRANSFERENCIA_EXTERNA_SAIDA"
    assert dados["status_novo"] == "TRANSFERIDO"
    assert dados["instituicao_externa"] == "Universidade Federal de Tecnologia"

    # Confere cancelamento de turmas
    inscricoes = servico_movimentacao.listar_inscricoes_turma(discente_id)
    assert inscricoes[0].status == "CANCELADA_MOVIMENTACAO"


# ==============================================================================
# FASE 5 / USER STORY 3: Cancelamento e Jubilamento Acadêmico
# ==============================================================================

def test_cancelamento_voluntario_sucesso():
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    canc_payload = {
        "discente_id": discente_id,
        "tipo_cancelamento": "CANCELAMENTO_VOLUNTARIO",
        "periodo_letivo": "2026.2",
        "justificativa": "Desistência formal definitiva do curso a pedido do aluno",
        "operador_id": "SEC_ADMIN_01",
    }
    res = client.post("/api/movimentacao/cancelamento", json=canc_payload)
    assert res.status_code == 200
    dados = res.json()
    assert dados["tipo"] == "CANCELAMENTO_VOLUNTARIO"
    assert dados["status_novo"] == "CANCELADO"

    d_atual = client.get(f"/api/movimentacao/discentes/{discente_id}").json()
    assert d_atual["status"] == "CANCELADO"

    # Tentativa subsequente de trancar deve ser bloqueada
    res_tranc = client.post(
        "/api/movimentacao/trancamento",
        json={
            "discente_id": discente_id,
            "periodo_letivo": "2027.1",
            "justificativa": "Tentativa indevida",
            "operador_id": "SEC_ADMIN_01",
        },
    )
    assert res_tranc.status_code == 400
    assert "CANCELADO" in res_tranc.json()["detail"]


def test_jubilamento_prazo_insuficiente_rejeicao():
    # ENG_SOFT maximo = 14 semestres. Aluno tem 8 cursados + 2 trancados = 10 semestres
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
        "semestres_cursados": 8,
        "semestres_trancados": 2,
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    jub_payload = {
        "discente_id": discente_id,
        "periodo_letivo": "2026.2",
        "justificativa": "Tentativa precipitada de jubilamento",
        "operador_id": "SEC_ADMIN_01",
    }
    res = client.post("/api/movimentacao/jubilamento", json=jub_payload)
    assert res.status_code == 400
    assert "não atingiu o prazo máximo" in res.json()["detail"]


def test_jubilamento_prazo_extrapolado_sucesso():
    # ENG_SOFT maximo = 14 semestres. Aluno tem 11 cursados + 4 trancados = 15 semestres
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2018.1",
        "semestres_cursados": 11,
        "semestres_trancados": 4,
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    jub_payload = {
        "discente_id": discente_id,
        "periodo_letivo": "2026.2",
        "justificativa": "Extrapolação dos 14 semestres regulamentares de integralização",
        "operador_id": "COLEGIADO_01",
    }
    res = client.post("/api/movimentacao/jubilamento", json=jub_payload)
    assert res.status_code == 200
    dados = res.json()
    assert dados["tipo"] == "JUBILAMENTO"
    assert dados["status_novo"] == "JUBILADO"

    d_atual = client.get(f"/api/movimentacao/discentes/{discente_id}").json()
    assert d_atual["status"] == "JUBILADO"

    # Tentativa de operação em aluno jubilado é rejeitada
    res_transf = client.post(
        "/api/movimentacao/transferencia",
        json={
            "discente_id": discente_id,
            "tipo_transferencia": "TRANSFERENCIA_INTERNA",
            "curso_destino_id": "CURSO_CC",
            "periodo_letivo": "2027.1",
            "justificativa": "Tentativa em aluno jubilado",
            "operador_id": "SEC_01",
        },
    )
    assert res_transf.status_code == 400
    assert "JUBILADO" in res_transf.json()["detail"]


# ==============================================================================
# FASE 6 / USER STORY 4: Histórico de Auditoria e Emissão de Certidões
# ==============================================================================

def test_historico_movimentacoes_e_certidao_digital():
    payload_discente = {
        "matricula": "2024101001",
        "nome": "Carlos Silva",
        "cpf": "123.456.789-00",
        "curso_id": "CURSO_ENG_SOFT",
        "nome_curso": "Engenharia de Software",
        "semestre_ingresso": "2024.1",
        "semestres_cursados": 2,
        "semestres_trancados": 0,
    }
    d_res = client.post("/api/movimentacao/discentes", json=payload_discente).json()
    discente_id = d_res["id"]

    # Movimentação 1: Trancamento
    res_tranc = client.post(
        "/api/movimentacao/trancamento",
        json={
            "discente_id": discente_id,
            "periodo_letivo": "2026.1",
            "justificativa": "Trancamento regular",
            "operador_id": "SEC_01",
        },
    ).json()
    mov1_id = res_tranc["id"]

    # Movimentação 2: Destrancamento
    res_dest = client.post(
        "/api/movimentacao/destrancamento",
        json={
            "discente_id": discente_id,
            "periodo_letivo": "2026.2",
            "justificativa": "Retorno às aulas",
            "operador_id": "SEC_01",
        },
    ).json()
    mov2_id = res_dest["id"]

    # Consultar histórico
    hist_res = client.get(f"/api/movimentacao/historico/{discente_id}")
    assert hist_res.status_code == 200
    historico = hist_res.json()
    assert len(historico) == 2
    assert historico[0]["id"] == mov1_id
    assert historico[0]["tipo"] == "TRANCAMENTO"
    assert historico[1]["id"] == mov2_id
    assert historico[1]["tipo"] == "DESTRANCAMENTO"

    # Emitir certidão da movimentação 1
    cert_res = client.get(f"/api/movimentacao/certidao/{mov1_id}")
    assert cert_res.status_code == 200
    cert = cert_res.json()
    assert cert["codigo_autenticidade"] == res_tranc["codigo_autenticidade"]
    assert cert["matricula"] == "2024101001"
    assert cert["nome_discente"] == "Carlos Silva"
    assert cert["curso"] == "Engenharia de Software"
    assert cert["tipo_movimentacao"] == "TRANCAMENTO"
    assert cert["status_resultante"] == "TRANCADO"
    assert "CERTIFICAMOS" in cert["texto_certidao"]


def test_emitir_certidao_inexistente():
    response = client.get("/api/movimentacao/certidao/MOV-9999")
    assert response.status_code == 404
