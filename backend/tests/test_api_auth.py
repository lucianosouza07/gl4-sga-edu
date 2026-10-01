from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.usuario import Usuario, PerfilUsuario
from app.models.aluno import Aluno
from app.core.security import gerar_hash_senha


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_por_email_sucesso(client: TestClient, db_session: Session):
    usuario = Usuario(
        nome="Secretaria Maria",
        email="maria.sec@gl4.edu",
        senha_hash=gerar_hash_senha("senhaSecreta123"),
        perfil=PerfilUsuario.SECRETARIA.value,
        ativo=True
    )
    db_session.add(usuario)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"identificador": "maria.sec@gl4.edu", "senha": "senhaSecreta123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["usuario"]["email"] == "maria.sec@gl4.edu"
    assert data["usuario"]["perfil"] == PerfilUsuario.SECRETARIA.value


def test_login_por_matricula_sucesso(client: TestClient, db_session: Session):
    usuario = Usuario(
        nome="Lucas Matrícula",
        email="lucas.aluno@gl4.edu",
        senha_hash=gerar_hash_senha("senhaAluno123"),
        perfil=PerfilUsuario.ALUNO.value,
        ativo=True
    )
    db_session.add(usuario)
    db_session.flush()

    aluno = Aluno(
        usuario_id=usuario.id,
        matricula="202610999",
        nome_completo="Lucas Matrícula",
        cpf="99988877766",
        email="lucas.aluno@gl4.edu",
        data_nascimento=date(2004, 8, 20),
        status="ATIVO"
    )
    db_session.add(aluno)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"identificador": "202610999", "senha": "senhaAluno123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["usuario"]["email"] == "lucas.aluno@gl4.edu"
    assert data["usuario"]["perfil"] == PerfilUsuario.ALUNO.value


def test_login_senha_incorreta_retorna_401(client: TestClient, admin_user: Usuario):
    response = client.post(
        "/api/v1/auth/login",
        json={"identificador": admin_user.email, "senha": "senhaTotalmenteErrada"}
    )
    assert response.status_code == 401
    assert "Credenciais inválidas" in response.json()["detail"]


def test_login_usuario_inexistente_retorna_401(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"identificador": "fantasma@gl4.edu", "senha": "123456qualquer"}
    )
    assert response.status_code == 401


def test_obter_usuario_logado_me_sucesso(client: TestClient, admin_user: Usuario, admin_headers: dict):
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == admin_user.email
    assert data["perfil"] == PerfilUsuario.ADMIN.value
    assert data["nome"] == admin_user.nome


def test_obter_usuario_logado_sem_token_retorna_401_em_portugues(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Não autenticado" in response.json()["detail"]


def test_obter_usuario_logado_token_invalido_retorna_401(client: TestClient):
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token.completamente.falso"})
    assert response.status_code == 401
    assert "Credenciais inválidas" in response.json()["detail"]


def test_rota_inexistente_retorna_404_em_portugues(client: TestClient):
    response = client.get("/api/v1/rota-totalmente-inexistente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Recurso ou rota não encontrada no sistema."


def test_validacao_schema_retorna_422_em_portugues(client: TestClient):
    response = client.post("/api/v1/auth/login", json={})
    assert response.status_code == 422
    data = response.json()
    assert data["detail"] == "Erro de validação nos dados enviados."
    assert any(e["mensagem"] == "Campo obrigatório não informado." for e in data["erros"])
