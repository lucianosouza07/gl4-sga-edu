"""Fixtures compartilhadas para os testes do módulo Cadastrar Alunos (SGA-15)."""

from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient

from modulo_cadastrar_alunos.repository import AlunoRepository, get_repository
from modulo_cadastrar_alunos.router import app
from modulo_cadastrar_alunos.security import criar_token_sessao, hash_password


@pytest.fixture()
def repo() -> Generator[AlunoRepository, None, None]:
    """Cria um repositório SQLite em memória isolado por teste."""
    repositorio = AlunoRepository(db_path=":memory:")
    yield repositorio
    repositorio.close()


@pytest.fixture()
def client(repo: AlunoRepository) -> Generator[TestClient, None, None]:
    """Fornece TestClient FastAPI com override do repositório para a instância isolada."""
    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def secretaria_operator(repo: AlunoRepository) -> dict[str, int | str]:
    """Cria um operador com perfil Secretaria (perfil_id=3) ativo."""
    uid = repo.inserir_usuario_seed(
        login="secretaria.academica@uneb.br",
        senha_hash=hash_password("Sec@2026Forte", rounds=4),
        perfil_id=3,
        status_conta=1,
    )
    token = criar_token_sessao(usuario_id=uid, perfil_id=3)
    return {"usuario_id": uid, "token": token}


@pytest.fixture()
def secretaria_headers(secretaria_operator: dict[str, int | str]) -> dict[str, str]:
    """Retorna cabeçalho Authorization Bearer para operador Secretaria ativo."""
    return {"Authorization": f"Bearer {secretaria_operator['token']}"}


@pytest.fixture()
def admin_operator(repo: AlunoRepository) -> dict[str, int | str]:
    """Cria um operador com perfil Admin (perfil_id=5) ativo."""
    uid = repo.inserir_usuario_seed(
        login="admin.sistema@uneb.br",
        senha_hash=hash_password("Admin@2026Forte", rounds=4),
        perfil_id=5,
        status_conta=1,
    )
    token = criar_token_sessao(usuario_id=uid, perfil_id=5)
    return {"usuario_id": uid, "token": token}


@pytest.fixture()
def admin_headers(admin_operator: dict[str, int | str]) -> dict[str, str]:
    """Retorna cabeçalho Authorization Bearer para operador Admin ativo."""
    return {"Authorization": f"Bearer {admin_operator['token']}"}


def gerar_cpf_valido(base_9_digitos: str) -> str:
    """Calcula os 2 dígitos verificadores para uma base numérica de 9 dígitos."""
    assert len(base_9_digitos) == 9 and base_9_digitos.isdigit()
    soma1 = sum(int(d) * (10 - idx) for idx, d in enumerate(base_9_digitos))
    r1 = (soma1 * 10) % 11
    d1 = 0 if r1 == 10 else r1
    parcial10 = f"{base_9_digitos}{d1}"
    soma2 = sum(int(d) * (11 - idx) for idx, d in enumerate(parcial10))
    r2 = (soma2 * 10) % 11
    d2 = 0 if r2 == 10 else r2
    return f"{parcial10}{d2}"
