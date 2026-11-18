"""Fixtures isoladas para testes do módulo de funcionários administrativos."""

from pathlib import Path
import sys
from typing import Callable

MODULO_DIR = Path(__file__).resolve().parent.parent
if str(MODULO_DIR) not in sys.path:
    sys.path.insert(0, str(MODULO_DIR))

import pytest
from fastapi.testclient import TestClient

from repository import FuncionarioAdminRepository, get_repository
from security import criar_token_sessao, hash_password


@pytest.fixture
def repo() -> FuncionarioAdminRepository:
    """Cria um repositório SQLite em memória isolado para cada caso de teste."""
    instancia = FuncionarioAdminRepository(db_path=":memory:")
    yield instancia
    instancia.close()


@pytest.fixture
def seed_atores(repo: FuncionarioAdminRepository) -> dict[str, dict[str, int | str]]:
    """Semeia contas de teste para todos os perfis RBAC e retorna tokens/IDs."""
    senha_padrao = hash_password("SenhaTeste@2026", rounds=4)
    atores: dict[str, dict[str, int | str]] = {}

    definicoes = [
        ("aluno", "aluno.teste@sga.edu.br", 1, 1),
        ("professor", "prof.teste@sga.edu.br", 2, 1),
        ("secretaria", "sec.teste@sga.edu.br", 3, 1),
        ("financeiro", "fin.teste@sga.edu.br", 4, 1),
        ("admin", "admin.principal@sga.edu.br", 5, 1),
        ("admin_inativo", "admin.inativo@sga.edu.br", 5, 0),
    ]
    for chave, login, perfil_id, status_conta in definicoes:
        uid = repo.inserir_usuario_seed(
            login=login,
            senha_hash=senha_padrao,
            perfil_id=perfil_id,
            status_conta=status_conta,
        )
        atores[chave] = {
            "usuario_id": uid,
            "login": login,
            "perfil_id": perfil_id,
            "token": criar_token_sessao(usuario_id=uid, perfil_id=perfil_id),
        }
    return atores


@pytest.fixture
def headers_para(seed_atores: dict[str, dict[str, int | str]]) -> Callable[[str], dict[str, str]]:
    """Fábrica de cabeçalhos Authorization Bearer por ator semeado."""

    def _build(chave_ator: str) -> dict[str, str]:
        token = seed_atores[chave_ator]["token"]
        return {"Authorization": f"Bearer {token}"}

    return _build


@pytest.fixture
def client(repo: FuncionarioAdminRepository):
    """Cliente FastAPI usando o repositório isolado por teste."""
    from router import app

    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
