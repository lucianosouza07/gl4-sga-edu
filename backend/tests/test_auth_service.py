import pytest
from datetime import date
from sqlalchemy.orm import Session
from app.models.usuario import Usuario, PerfilUsuario
from app.models.aluno import Aluno
from app.core.security import gerar_hash_senha, decodificar_token_jwt
from app.core.exceptions import CredenciaisInvalidasError
from app.services.auth_service import AuthService


def test_autenticar_por_email_com_sucesso(db_session: Session):
    usuario = Usuario(
        nome="Secretaria Maria",
        email="maria@gl4.edu",
        senha_hash=gerar_hash_senha("senha123"),
        perfil=PerfilUsuario.SECRETARIA.value,
        ativo=True
    )
    db_session.add(usuario)
    db_session.commit()

    service = AuthService(db_session)
    usuario_autenticado = service.autenticar_usuario("maria@gl4.edu", "senha123")

    assert usuario_autenticado.id == usuario.id
    assert usuario_autenticado.email == "maria@gl4.edu"
    assert usuario_autenticado.perfil == PerfilUsuario.SECRETARIA.value


def test_autenticar_por_matricula_com_sucesso(db_session: Session):
    usuario = Usuario(
        nome="Lucas Aluno",
        email="lucas@gl4.edu",
        senha_hash=gerar_hash_senha("senha123"),
        perfil=PerfilUsuario.ALUNO.value,
        ativo=True
    )
    db_session.add(usuario)
    db_session.flush()

    aluno = Aluno(
        usuario_id=usuario.id,
        matricula="202610099",
        nome_completo="Lucas Aluno",
        cpf="11122233344",
        email="lucas@gl4.edu",
        data_nascimento=date(2003, 5, 12),
        status="ATIVO"
    )
    db_session.add(aluno)
    db_session.commit()

    service = AuthService(db_session)
    usuario_autenticado = service.autenticar_usuario("202610099", "senha123")

    assert usuario_autenticado.id == usuario.id
    assert usuario_autenticado.email == "lucas@gl4.edu"
    assert usuario_autenticado.aluno.matricula == "202610099"


def test_autenticar_senha_incorreta_lanca_excecao(db_session: Session):
    usuario = Usuario(
        nome="Admin Master",
        email="admin@gl4.edu",
        senha_hash=gerar_hash_senha("senhaCorreta"),
        perfil=PerfilUsuario.ADMIN.value,
        ativo=True
    )
    db_session.add(usuario)
    db_session.commit()

    service = AuthService(db_session)
    with pytest.raises(CredenciaisInvalidasError, match="Credenciais inválidas"):
        service.autenticar_usuario("admin@gl4.edu", "senhaErrada")


def test_autenticar_usuario_inexistente_lanca_excecao(db_session: Session):
    service = AuthService(db_session)
    with pytest.raises(CredenciaisInvalidasError, match="Credenciais inválidas"):
        service.autenticar_usuario("naoexiste@gl4.edu", "senha123")


def test_autenticar_usuario_inativo_lanca_excecao(db_session: Session):
    usuario = Usuario(
        nome="Usuario Bloqueado",
        email="bloqueado@gl4.edu",
        senha_hash=gerar_hash_senha("senha123"),
        perfil=PerfilUsuario.ALUNO.value,
        ativo=False
    )
    db_session.add(usuario)
    db_session.commit()

    service = AuthService(db_session)
    with pytest.raises(CredenciaisInvalidasError, match="Credenciais inválidas"):
        service.autenticar_usuario("bloqueado@gl4.edu", "senha123")


def test_gerar_token_jwt_valido_com_claims(db_session: Session):
    usuario = Usuario(
        nome="Admin Teste",
        email="adm@gl4.edu",
        senha_hash=gerar_hash_senha("senha123"),
        perfil=PerfilUsuario.ADMIN.value,
        ativo=True
    )
    db_session.add(usuario)
    db_session.commit()

    service = AuthService(db_session)
    token_resp = service.gerar_token_para_usuario(usuario)

    assert token_resp.access_token is not None
    assert token_resp.token_type == "bearer"
    assert token_resp.usuario.email == "adm@gl4.edu"
    assert token_resp.usuario.perfil == PerfilUsuario.ADMIN.value

    # Validação do JWT decodificado
    payload = decodificar_token_jwt(token_resp.access_token)
    assert payload["sub"] == str(usuario.id)
    assert payload["email"] == "adm@gl4.edu"
    assert payload["perfil"] == PerfilUsuario.ADMIN.value
    assert payload["nome"] == "Admin Teste"
