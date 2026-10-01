import uuid
from datetime import date
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.usuario import Usuario, PerfilUsuario
from app.models.aluno import Aluno, StatusAluno
from app.core.security import gerar_hash_senha


def test_criar_usuario_com_sucesso(db_session: Session):
    """Garante que um usuário pode ser criado com todos os campos e defaults."""
    usuario = Usuario(
        nome="Secretaria Maria",
        email="secretaria@gl4.edu",
        senha_hash=gerar_hash_senha("senha123"),
        perfil=PerfilUsuario.SECRETARIA.value,
        ativo=True
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    assert isinstance(usuario.id, uuid.UUID)
    assert usuario.nome == "Secretaria Maria"
    assert usuario.email == "secretaria@gl4.edu"
    assert usuario.perfil == PerfilUsuario.SECRETARIA.value
    assert usuario.ativo is True
    assert usuario.criado_em is not None


def test_usuario_email_unico(db_session: Session):
    """Garante que não é permitido criar dois usuários com o mesmo e-mail."""
    u1 = Usuario(
        nome="Usuario Um",
        email="duplicado@gl4.edu",
        senha_hash=gerar_hash_senha("123"),
        perfil=PerfilUsuario.ALUNO.value
    )
    db_session.add(u1)
    db_session.commit()

    u2 = Usuario(
        nome="Usuario Dois",
        email="duplicado@gl4.edu",
        senha_hash=gerar_hash_senha("456"),
        perfil=PerfilUsuario.ALUNO.value
    )
    db_session.add(u2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_criar_aluno_com_relacionamento_usuario(db_session: Session):
    """Garante que um Aluno é criado vinculado a um Usuário 1:1."""
    usuario = Usuario(
        nome="Carlos Eduardo Silva",
        email="aluno.teste@gl4.edu",
        senha_hash=gerar_hash_senha("senhaAluno123"),
        perfil=PerfilUsuario.ALUNO.value
    )
    db_session.add(usuario)
    db_session.commit()

    aluno = Aluno(
        usuario_id=usuario.id,
        matricula="20261001",
        nome_completo="Carlos Eduardo Silva",
        cpf="123.456.789-00",
        email=usuario.email,
        telefone="(11) 98765-4321",
        data_nascimento=date(2002, 5, 14),
        status=StatusAluno.ATIVO.value
    )
    db_session.add(aluno)
    db_session.commit()
    db_session.refresh(aluno)

    assert isinstance(aluno.id, uuid.UUID)
    assert aluno.usuario_id == usuario.id
    assert aluno.matricula == "20261001"
    assert aluno.usuario.email == "aluno.teste@gl4.edu"
    assert aluno.usuario.nome == "Carlos Eduardo Silva"
    assert usuario.aluno.nome_completo == "Carlos Eduardo Silva"


def test_aluno_matricula_e_cpf_unicos(db_session: Session):
    """Garante restrição única de matrícula e CPF."""
    u1 = Usuario(nome="Aluno 1", email="a1@gl4.edu", senha_hash="h1")
    u2 = Usuario(nome="Aluno 2", email="a2@gl4.edu", senha_hash="h2")
    db_session.add_all([u1, u2])
    db_session.commit()

    aluno1 = Aluno(
        usuario_id=u1.id,
        matricula="20269999",
        nome_completo="Aluno Um",
        cpf="111.222.333-44",
        email=u1.email,
        data_nascimento=date(2000, 1, 1)
    )
    db_session.add(aluno1)
    db_session.commit()

    # Tentativa com mesma matrícula
    aluno2 = Aluno(
        usuario_id=u2.id,
        matricula="20269999",
        nome_completo="Aluno Dois",
        cpf="999.888.777-66",
        email=u2.email,
        data_nascimento=date(2001, 2, 2)
    )
    db_session.add(aluno2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Tentativa com mesmo CPF
    aluno3 = Aluno(
        usuario_id=u2.id,
        matricula="20268888",
        nome_completo="Aluno Tres",
        cpf="111.222.333-44",
        email=u2.email,
        data_nascimento=date(2001, 2, 2)
    )
    db_session.add(aluno3)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
