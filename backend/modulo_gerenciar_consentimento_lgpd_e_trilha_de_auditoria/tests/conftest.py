"""Fixtures e configuração de testes para o módulo LGPD e Auditoria."""

import pytest
from fastapi.testclient import TestClient

from ..repository import LgpdAuditRepository
from ..router import criar_app
from ..security import gerar_token_sessao


@pytest.fixture
def repo():
    """Instancia um repositório isolado em memória para cada teste com seeds de usuários."""
    repository = LgpdAuditRepository(db_path=":memory:")

    # Seeds de usuários nos diferentes perfis
    repository.criar_usuario(login="admin@sga.edu.br", perfil_RBAC=5, statusCONTA=1, usuario_id=1)
    repository.criar_usuario(login="prof@sga.edu.br", perfil_RBAC=2, statusCONTA=1, usuario_id=2)
    repository.criar_usuario(login="aluno@sga.edu.br", perfil_RBAC=1, statusCONTA=1, usuario_id=3)
    repository.criar_usuario(login="aluno2@sga.edu.br", perfil_RBAC=1, statusCONTA=1, usuario_id=4)
    repository.criar_usuario(login="inativo@sga.edu.br", perfil_RBAC=1, statusCONTA=0, usuario_id=5)

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
    """Token Bearer assinado para o Administrador (id=1, perfil=5)."""
    return gerar_token_sessao(usuario_id=1, login="admin@sga.edu.br", perfil_id=5)


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def aluno_token():
    """Token Bearer assinado para o Aluno (id=3, perfil=1)."""
    return gerar_token_sessao(usuario_id=3, login="aluno@sga.edu.br", perfil_id=1)


@pytest.fixture
def aluno_headers(aluno_token):
    return {"Authorization": f"Bearer {aluno_token}"}


@pytest.fixture
def aluno2_token():
    """Token Bearer assinado para outro Aluno (id=4, perfil=1)."""
    return gerar_token_sessao(usuario_id=4, login="aluno2@sga.edu.br", perfil_id=1)


@pytest.fixture
def aluno2_headers(aluno2_token):
    return {"Authorization": f"Bearer {aluno2_token}"}


@pytest.fixture
def prof_token():
    """Token Bearer assinado para o Professor (id=2, perfil=2)."""
    return gerar_token_sessao(usuario_id=2, login="prof@sga.edu.br", perfil_id=2)


@pytest.fixture
def prof_headers(prof_token):
    return {"Authorization": f"Bearer {prof_token}"}
