import uuid
from fastapi.testclient import TestClient


def test_criar_aluno_sucesso_pela_secretaria(client: TestClient, secretaria_headers: dict):
    payload = {
        "matricula": "202610501",
        "nome_completo": "Juliana Silveira",
        "cpf": "11122233344",
        "email": "juliana@gl4.edu",
        "telefone": "11988887777",
        "data_nascimento": "2005-04-10"
    }

    response = client.post("/api/v1/alunos", json=payload, headers=secretaria_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["matricula"] == "202610501"
    assert data["nome_completo"] == "Juliana Silveira"
    assert data["status"] == "ATIVO"
    assert data["usuario_id"] is not None


def test_criar_aluno_sucesso_pelo_admin(client: TestClient, admin_headers: dict):
    payload = {
        "matricula": "202610502",
        "nome_completo": "Renato Augusto",
        "cpf": "22233344455",
        "email": "renato@gl4.edu",
        "data_nascimento": "2004-11-25"
    }

    response = client.post("/api/v1/alunos", json=payload, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["matricula"] == "202610502"


def test_criar_aluno_negado_para_perfil_aluno_rbac(client: TestClient, aluno_headers: dict):
    payload = {
        "matricula": "202610503",
        "nome_completo": "Tentativa Invalida",
        "cpf": "33344455566",
        "email": "tentativa@gl4.edu",
        "data_nascimento": "2004-01-01"
    }

    # Perfil ALUNO não tem permissão para cadastrar alunos (apenas SECRETARIA ou ADMIN)
    response = client.post("/api/v1/alunos", json=payload, headers=aluno_headers)
    assert response.status_code == 403
    assert "Acesso não autorizado" in response.json()["detail"]


def test_criar_aluno_sem_token_retorna_401(client: TestClient):
    payload = {
        "matricula": "202610504",
        "nome_completo": "Sem Token",
        "cpf": "44455566677",
        "email": "semtoken@gl4.edu",
        "data_nascimento": "2004-01-01"
    }

    response = client.post("/api/v1/alunos", json=payload)
    assert response.status_code == 401


def test_criar_aluno_matricula_duplicada_retorna_409(client: TestClient, secretaria_headers: dict):
    payload1 = {
        "matricula": "202610505",
        "nome_completo": "Primeiro Aluno",
        "cpf": "55566677788",
        "email": "primeiro@gl4.edu",
        "data_nascimento": "2004-01-01"
    }
    client.post("/api/v1/alunos", json=payload1, headers=secretaria_headers)

    payload2 = {
        "matricula": "202610505",  # Mesma matrícula
        "nome_completo": "Segundo Aluno",
        "cpf": "66677788899",
        "email": "segundo@gl4.edu",
        "data_nascimento": "2004-01-01"
    }
    response = client.post("/api/v1/alunos", json=payload2, headers=secretaria_headers)
    assert response.status_code == 409
    assert "já está cadastrada" in response.json()["detail"]


def test_listar_alunos_com_busca(client: TestClient, secretaria_headers: dict):
    client.post("/api/v1/alunos", json={
        "matricula": "202610506",
        "nome_completo": "Amanda Nogueira",
        "cpf": "77788899900",
        "email": "amanda@gl4.edu",
        "data_nascimento": "2003-02-14"
    }, headers=secretaria_headers)

    client.post("/api/v1/alunos", json={
        "matricula": "202610507",
        "nome_completo": "Bernardo Lima",
        "cpf": "88899900011",
        "email": "bernardo@gl4.edu",
        "data_nascimento": "2003-06-18"
    }, headers=secretaria_headers)

    # Listagem completa
    response = client.get("/api/v1/alunos", headers=secretaria_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 2

    # Busca específica por nome
    res_busca = client.get("/api/v1/alunos?busca=Amanda", headers=secretaria_headers)
    assert res_busca.status_code == 200
    assert len(res_busca.json()) == 1
    assert res_busca.json()[0]["nome_completo"] == "Amanda Nogueira"


def test_obter_aluno_por_id_sucesso(client: TestClient, secretaria_headers: dict):
    criado = client.post("/api/v1/alunos", json={
        "matricula": "202610508",
        "nome_completo": "Camila Correia",
        "cpf": "12312312399",
        "email": "camila@gl4.edu",
        "data_nascimento": "2002-09-09"
    }, headers=secretaria_headers).json()

    aluno_id = criado["id"]
    response = client.get(f"/api/v1/alunos/{aluno_id}", headers=secretaria_headers)
    assert response.status_code == 200
    assert response.json()["matricula"] == "202610508"


def test_obter_aluno_inexistente_retorna_404(client: TestClient, secretaria_headers: dict):
    id_falso = str(uuid.uuid4())
    response = client.get(f"/api/v1/alunos/{id_falso}", headers=secretaria_headers)
    assert response.status_code == 404


def test_atualizar_aluno_sucesso(client: TestClient, secretaria_headers: dict):
    criado = client.post("/api/v1/alunos", json={
        "matricula": "202610509",
        "nome_completo": "Diego Antigo",
        "cpf": "32132132188",
        "email": "diego@gl4.edu",
        "data_nascimento": "2001-12-12"
    }, headers=secretaria_headers).json()

    aluno_id = criado["id"]
    response = client.put(
        f"/api/v1/alunos/{aluno_id}",
        json={"nome_completo": "Diego Nome Novo", "telefone": "11977776666"},
        headers=secretaria_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome_completo"] == "Diego Nome Novo"
    assert data["telefone"] == "11977776666"


def test_inativar_aluno_soft_delete(client: TestClient, secretaria_headers: dict):
    criado = client.post("/api/v1/alunos", json={
        "matricula": "202610510",
        "nome_completo": "Eduardo Inativar",
        "cpf": "45645645677",
        "email": "eduardo@gl4.edu",
        "data_nascimento": "2002-05-05"
    }, headers=secretaria_headers).json()

    aluno_id = criado["id"]
    response = client.patch(f"/api/v1/alunos/{aluno_id}/inativar", headers=secretaria_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "INATIVO"

    # Na listagem de ativos (padrão), o aluno não deve mais aparecer
    res_ativos = client.get("/api/v1/alunos?apenas_ativos=true", headers=secretaria_headers)
    assert not any(a["id"] == aluno_id for a in res_ativos.json())
