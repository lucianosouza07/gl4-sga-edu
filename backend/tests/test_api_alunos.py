import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.usuario import Usuario, PerfilUsuario


def test_criar_aluno_sucesso_pela_secretaria(client: TestClient, secretaria_headers: dict):
    payload = {
        "nome_completo": "Juliana Silveira",
        "cpf": "11122233344",
        "email": "juliana@gl4.edu",
        "telefone": "11988887777",
        "data_nascimento": "2005-04-10"
    }

    response = client.post("/api/v1/alunos", json=payload, headers=secretaria_headers)
    assert response.status_code == 201
    data = response.json()
    assert len(data["matricula"]) >= 9
    assert data["matricula"].isdigit()
    assert data["nome_completo"] == "Juliana Silveira"
    assert data["status"] == "ATIVO"
    assert data["usuario_id"] is not None


def test_criar_aluno_sucesso_pelo_admin(client: TestClient, admin_headers: dict):
    payload = {
        "nome_completo": "Renato Augusto",
        "cpf": "22233344455",
        "email": "renato@gl4.edu",
        "data_nascimento": "2004-11-25"
    }

    response = client.post("/api/v1/alunos", json=payload, headers=admin_headers)
    assert response.status_code == 201
    assert len(response.json()["matricula"]) >= 9


def test_login_com_matricula_gerada_automaticamente(client: TestClient, secretaria_headers: dict):
    criado = client.post("/api/v1/alunos", json={
        "nome_completo": "Aluno Login Automático",
        "cpf": "23233344455",
        "email": "login.automatico@gl4.edu",
        "data_nascimento": "2004-11-25",
    }, headers=secretaria_headers)
    assert criado.status_code == 201

    login = client.post("/api/v1/auth/login", json={
        "identificador": criado.json()["matricula"],
        "senha": "Mudar@123",
    })

    assert login.status_code == 200
    assert login.json()["usuario"]["id"] == criado.json()["usuario_id"]


def test_criar_aluno_negado_para_perfil_aluno_rbac(client: TestClient, aluno_headers: dict):
    payload = {
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
        "nome_completo": "Sem Token",
        "cpf": "44455566677",
        "email": "semtoken@gl4.edu",
        "data_nascimento": "2004-01-01"
    }

    response = client.post("/api/v1/alunos", json=payload)
    assert response.status_code == 401


def test_matricula_enviada_manualmente_e_rejeitada(client: TestClient, secretaria_headers: dict):
    payload = {
        "matricula": "202610505",
        "nome_completo": "Primeiro Aluno",
        "cpf": "55566677788",
        "email": "primeiro@gl4.edu",
        "data_nascimento": "2004-01-01"
    }
    response = client.post("/api/v1/alunos", json=payload, headers=secretaria_headers)
    assert response.status_code == 422
    assert any(error["campo"] == "matricula" for error in response.json()["erros"])


def test_listar_alunos_com_busca(client: TestClient, secretaria_headers: dict):
    client.post("/api/v1/alunos", json={
        "nome_completo": "Amanda Nogueira",
        "cpf": "77788899900",
        "email": "amanda@gl4.edu",
        "data_nascimento": "2003-02-14"
    }, headers=secretaria_headers)

    client.post("/api/v1/alunos", json={
        "nome_completo": "Bernardo Lima",
        "cpf": "88899900011",
        "email": "bernardo@gl4.edu",
        "data_nascimento": "2003-06-18"
    }, headers=secretaria_headers)

    # Listagem completa
    response = client.get("/api/v1/alunos", headers=secretaria_headers)
    assert response.status_code == 200
    assert response.json()["total"] >= 2

    # Busca específica por nome
    res_busca = client.get("/api/v1/alunos?busca=Amanda", headers=secretaria_headers)
    assert res_busca.status_code == 200
    assert res_busca.json()["total"] == 1
    assert res_busca.json()["itens"][0]["nome_completo"] == "Amanda Nogueira"


@pytest.mark.parametrize("headers_fixture", ["secretaria_headers", "admin_headers"])
def test_obter_aluno_por_id_sucesso(
    client: TestClient, request: pytest.FixtureRequest, headers_fixture: str,
):
    headers = request.getfixturevalue(headers_fixture)
    criado = client.post("/api/v1/alunos", json={
        "nome_completo": "Camila Correia",
        "cpf": "12312312399",
        "email": "camila@gl4.edu",
        "data_nascimento": "2002-09-09"
    }, headers=headers).json()

    aluno_id = criado["id"]
    response = client.get(f"/api/v1/alunos/{aluno_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["matricula"] == criado["matricula"]


@pytest.mark.parametrize("perfil", [PerfilUsuario.ALUNO, PerfilUsuario.PROFESSOR])
def test_obter_aluno_por_id_negado_para_outros_perfis(
    client: TestClient, db_session: Session, aluno_user: Usuario,
    aluno_headers: dict, secretaria_headers: dict, perfil: PerfilUsuario,
):
    criado = client.post("/api/v1/alunos", json={
        "nome_completo": "Aluno Consulta Restrita",
        "cpf": "90909090909",
        "email": "consulta.restrita@gl4.edu",
        "data_nascimento": "2002-01-01",
    }, headers=secretaria_headers).json()
    aluno_user.perfil = perfil.value
    db_session.commit()

    response = client.get(f"/api/v1/alunos/{criado['id']}", headers=aluno_headers)

    assert response.status_code == 403


def test_obter_aluno_por_id_sem_token_retorna_401(client: TestClient):
    response = client.get(f"/api/v1/alunos/{uuid.uuid4()}")

    assert response.status_code == 401


def test_obter_me_retorna_apenas_aluno_do_usuario_autenticado(
    client: TestClient, secretaria_headers: dict,
):
    outro = client.post("/api/v1/alunos", json={
        "nome_completo": "Outro Aluno",
        "cpf": "80808080808",
        "email": "outro.perfil@gl4.edu",
        "data_nascimento": "2002-01-01",
    }, headers=secretaria_headers).json()
    proprio = client.post("/api/v1/alunos", json={
        "nome_completo": "Aluno Perfil Proprio",
        "cpf": "70707070707",
        "email": "perfil.proprio@gl4.edu",
        "data_nascimento": "2003-01-01",
    }, headers=secretaria_headers).json()
    login = client.post("/api/v1/auth/login", json={
        "identificador": proprio["email"], "senha": "Mudar@123",
    })
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.get("/api/v1/alunos/me", headers=headers)
    tentativa = client.get("/api/v1/alunos/me", params={"aluno_id": outro["id"]}, headers=headers)

    assert response.status_code == 200
    assert response.json() == proprio
    assert tentativa.status_code == 200
    assert tentativa.json() == proprio
    assert "senha_hash" not in response.json()
    assert client.get(f"/api/v1/alunos/{proprio['id']}", headers=headers).status_code == 403


@pytest.mark.parametrize("perfil", [PerfilUsuario.ADMIN, PerfilUsuario.SECRETARIA, PerfilUsuario.PROFESSOR])
def test_obter_me_negado_para_outros_perfis(
    client: TestClient, db_session: Session, aluno_user: Usuario,
    aluno_headers: dict, perfil: PerfilUsuario,
):
    aluno_user.perfil = perfil.value
    db_session.commit()

    response = client.get("/api/v1/alunos/me", headers=aluno_headers)

    assert response.status_code == 403


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer token-invalido"}])
def test_obter_me_sem_autenticacao_valida_retorna_401(client: TestClient, headers: dict):
    response = client.get("/api/v1/alunos/me", headers=headers)

    assert response.status_code == 401


def test_obter_me_usuario_inativo_retorna_401(
    client: TestClient, db_session: Session, aluno_user: Usuario, aluno_headers: dict,
):
    aluno_user.ativo = False
    db_session.commit()

    response = client.get("/api/v1/alunos/me", headers=aluno_headers)

    assert response.status_code == 401


def test_obter_me_sem_aluno_vinculado_retorna_404(client: TestClient, aluno_headers: dict):
    response = client.get("/api/v1/alunos/me", headers=aluno_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Aluno vinculado ao usuário não encontrado."


def test_obter_aluno_inexistente_retorna_404(client: TestClient, secretaria_headers: dict):
    id_falso = str(uuid.uuid4())
    response = client.get(f"/api/v1/alunos/{id_falso}", headers=secretaria_headers)
    assert response.status_code == 404


def test_atualizar_aluno_sucesso(client: TestClient, secretaria_headers: dict):
    criado = client.post("/api/v1/alunos", json={
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


def test_nao_permite_editar_matricula(client: TestClient, secretaria_headers: dict):
    criado = client.post("/api/v1/alunos", json={
        "nome_completo": "Aluno Matrícula Imutável",
        "cpf": "65432198700",
        "email": "matricula.imutavel@gl4.edu",
        "data_nascimento": "2001-12-12"
    }, headers=secretaria_headers).json()

    response = client.put(
        f"/api/v1/alunos/{criado['id']}",
        json={"matricula": "199910001"},
        headers=secretaria_headers,
    )

    assert response.status_code == 422
    assert response.json()["erros"][0]["campo"] == "matricula"


def test_inativar_aluno_soft_delete(client: TestClient, secretaria_headers: dict):
    criado = client.post("/api/v1/alunos", json={
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
    assert not any(a["id"] == aluno_id for a in res_ativos.json()["itens"])


def test_reativar_aluno_restaura_status_e_acesso(client: TestClient, secretaria_headers: dict):
    criado = client.post("/api/v1/alunos", json={
        "nome_completo": "Fernanda Reativar",
        "cpf": "56756756788",
        "email": "fernanda.reativar@gl4.edu",
        "data_nascimento": "2002-05-05"
    }, headers=secretaria_headers).json()
    aluno_id = criado["id"]
    client.patch(f"/api/v1/alunos/{aluno_id}/inativar", headers=secretaria_headers)

    response = client.patch(f"/api/v1/alunos/{aluno_id}/reativar", headers=secretaria_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "ATIVO"
    ativos = client.get("/api/v1/alunos?apenas_ativos=true", headers=secretaria_headers)
    assert any(aluno["id"] == aluno_id for aluno in ativos.json()["itens"])


def test_reativar_aluno_inexistente_retorna_404(client: TestClient, secretaria_headers: dict):
    response = client.patch(
        f"/api/v1/alunos/{uuid.uuid4()}/reativar",
        headers=secretaria_headers,
    )

    assert response.status_code == 404
