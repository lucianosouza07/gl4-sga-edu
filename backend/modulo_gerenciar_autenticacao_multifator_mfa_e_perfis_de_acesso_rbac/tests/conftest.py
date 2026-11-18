"""Fixtures compartilhadas para a suíte de testes de MFA e governança RBAC."""

import pytest
from fastapi.testclient import TestClient

from ..repository import MfaRbacRepository
from ..router import criar_app
from ..security import gerar_token_sessao, hash_senha


@pytest.fixture
def repo():
    """Instancia um repositório isolado em memória para cada teste com seeds completas."""
    repository = MfaRbacRepository(db_path=":memory:")

    senha_padrao_hash = hash_senha("SenhaForte#2026")

    # Seeds de usuários nos 5 perfis e variações de estado
    repository.criar_usuario(
        login="admin@sga.edu.br",
        senha_hash=senha_padrao_hash,
        perfil_RBAC=5,  # Admin
        statusCONTA=1,
    )
    repository.criar_usuario(
        login="admin2@sga.edu.br",
        senha_hash=senha_padrao_hash,
        perfil_RBAC=5,  # Admin secundário
        statusCONTA=1,
    )
    repository.criar_usuario(
        login="prof@sga.edu.br",
        senha_hash=senha_padrao_hash,
        perfil_RBAC=2,  # Professor
        statusCONTA=1,
    )
    repository.criar_usuario(
        login="aluno@sga.edu.br",
        senha_hash=senha_padrao_hash,
        perfil_RBAC=1,  # Aluno
        statusCONTA=1,
    )
    repository.criar_usuario(
        login="secretaria@sga.edu.br",
        senha_hash=senha_padrao_hash,
        perfil_RBAC=3,  # Secretaria
        statusCONTA=1,
    )
    repository.criar_usuario(
        login="financeiro@sga.edu.br",
        senha_hash=senha_padrao_hash,
        perfil_RBAC=4,  # Financeiro
        statusCONTA=1,
    )
    repository.criar_usuario(
        login="inativo@sga.edu.br",
        senha_hash=senha_padrao_hash,
        perfil_RBAC=3,  # Secretaria inativa
        statusCONTA=0,
    )

    yield repository
    repository.fechar()


@pytest.fixture
def client(repo):
    """Instancia cliente HTTP de teste FastAPI com o repositório injetado."""
    app = criar_app(repo=repo)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token():
    """Token Bearer assinado para o Admin principal (id=1)."""
    return gerar_token_sessao(usuario_id=1, login="admin@sga.edu.br", perfil_id=5)


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def admin2_token():
    """Token Bearer assinado para o segundo Admin (id=2)."""
    return gerar_token_sessao(usuario_id=2, login="admin2@sga.edu.br", perfil_id=5)


@pytest.fixture
def admin2_headers(admin2_token):
    return {"Authorization": f"Bearer {admin2_token}"}


@pytest.fixture
def prof_token():
    """Token Bearer assinado para o Professor (id=3)."""
    return gerar_token_sessao(usuario_id=3, login="prof@sga.edu.br", perfil_id=2)


@pytest.fixture
def prof_headers(prof_token):
    return {"Authorization": f"Bearer {prof_token}"}


@pytest.fixture
def aluno_token():
    """Token Bearer assinado para o Aluno (id=4)."""
    return gerar_token_sessao(usuario_id=4, login="aluno@sga.edu.br", perfil_id=1)


@pytest.fixture
def aluno_headers(aluno_token):
    return {"Authorization": f"Bearer {aluno_token}"}


@pytest.fixture
def secretaria_token():
    """Token Bearer assinado para Secretaria (id=5)."""
    return gerar_token_sessao(usuario_id=5, login="secretaria@sga.edu.br", perfil_id=3)


@pytest.fixture
def secretaria_headers(secretaria_token):
    return {"Authorization": f"Bearer {secretaria_token}"}


@pytest.fixture
def inativo_token():
    """Token Bearer de usuário inativo (id=7)."""
    return gerar_token_sessao(usuario_id=7, login="inativo@sga.edu.br", perfil_id=3)


@pytest.fixture
def inativo_headers(inativo_token):
    return {"Authorization": f"Bearer {inativo_token}"}
