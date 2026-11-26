"""Fixtures compartilhadas para os testes do módulo SGA-26."""

from typing import Any
from fastapi.testclient import TestClient
import pytest

try:
    from ..repository import AproveitamentoRepository, get_repository
    from ..router import app
    from ..security import criar_token_sessao
except ImportError:
    from repository import AproveitamentoRepository, get_repository
    from router import app
    from security import criar_token_sessao


@pytest.fixture()
def repo() -> AproveitamentoRepository:
    instancia = AproveitamentoRepository(db_path=":memory:")
    yield instancia
    instancia.close()


@pytest.fixture()
def dados_base(repo: AproveitamentoRepository) -> dict[str, Any]:
    """Cria massa institucional completa: operadores RBAC, matriz, disciplinas, pré-requisitos e alunos."""
    uid_aluno_op = repo.inserir_usuario_seed("aluno.op", "hash_fake", perfil_id=1, status_conta=1)
    uid_prof_op = repo.inserir_usuario_seed("prof.op", "hash_fake", perfil_id=2, status_conta=1)
    uid_sec = repo.inserir_usuario_seed("secretaria.op", "hash_fake", perfil_id=3, status_conta=1)
    uid_fin = repo.inserir_usuario_seed("financeiro.op", "hash_fake", perfil_id=4, status_conta=1)
    uid_admin = repo.inserir_usuario_seed("admin.op", "hash_fake", perfil_id=5, status_conta=1)
    uid_inativo = repo.inserir_usuario_seed("sec.inativa", "hash_fake", perfil_id=3, status_conta=0)

    dep_id = repo.inserir_departamento_seed("DCET-I", "Departamento de Ciências Exatas", "DCET1")
    curso_id = repo.inserir_curso_seed("MEC-SI-2026", "Sistemas de Informação", dep_id)
    matriz_antiga_id = repo.inserir_matriz_seed(curso_id, "MAT-SI-2020", ano_vigencia=2020)
    matriz_nova_id = repo.inserir_matriz_seed(curso_id, "MAT-SI-2026", ano_vigencia=2026)

    # Disciplinas:
    # d_origem_60h (60h) -> equivalente a d_alvo_60h (60h) [100% CH >= 75%]
    # d_origem_curta_30h (30h) -> carga horária insuficiente para d_alvo_60h [50% CH < 75%]
    # d_alvo_ja_aprovada (60h) -> aluno ativo já aprovado
    # d_avancada (60h) -> tem como PRE_REQUISITO d_alvo_60h e d_alvo_ja_aprovada
    d_origem_60h = repo.inserir_disciplina_seed(
        matriz_antiga_id, "SI101", "Algoritmos I (Grade 2020)", semestre_ideal=1, carga_horaria=60, ementa="Lógica e algoritmos."
    )
    d_origem_curta_30h = repo.inserir_disciplina_seed(
        matriz_antiga_id, "SI102", "Noções de Programação", semestre_ideal=1, carga_horaria=30, ementa="Introdução breve."
    )
    d_alvo_60h = repo.inserir_disciplina_seed(
        matriz_nova_id, "SI201", "Programação Estruturada", semestre_ideal=1, carga_horaria=60, ementa="Algoritmos e estruturas."
    )
    d_alvo_ja_aprovada = repo.inserir_disciplina_seed(
        matriz_nova_id, "SI202", "Matemática Discreta", semestre_ideal=1, carga_horaria=60, ementa="Lógica e grafos."
    )
    d_avancada = repo.inserir_disciplina_seed(
        matriz_nova_id, "SI301", "Estruturas de Dados", semestre_ideal=2, carga_horaria=60, ementa="Listas, árvores e grafos."
    )

    # SI301 exige SI201 e SI202 como pré-requisitos
    repo.inserir_prerequisito_seed(d_avancada, d_alvo_60h, "PRE_REQUISITO")
    repo.inserir_prerequisito_seed(d_avancada, d_alvo_ja_aprovada, "PRE_REQUISITO")

    periodo_id = repo.inserir_periodo_seed("2026.1", 2026, 1)
    turma_origem = repo.inserir_turma_seed("SI101-20261", d_origem_60h, periodo_id)
    turma_origem_curta = repo.inserir_turma_seed("SI102-20261", d_origem_curta_30h, periodo_id)
    turma_ja_aprovada = repo.inserir_turma_seed("SI202-20261", d_alvo_ja_aprovada, periodo_id)

    # Alunos
    uid_a1 = repo.inserir_usuario_seed("lucas.ativo", "hash_fake", perfil_id=1)
    mat_ativo = repo.inserir_aluno_seed(
        matricula=20260101,
        usuario_id=uid_a1,
        nome="Lucas Pereira",
        email="lucas.pereira@sga.edu.br",
        cpf="52998224725",
        curso_id=curso_id,
        status_academico="ATIVO",
    )

    uid_a2 = repo.inserir_usuario_seed("mariana.trancada", "hash_fake", perfil_id=1)
    mat_trancado = repo.inserir_aluno_seed(
        matricula=20260102,
        usuario_id=uid_a2,
        nome="Mariana Costa",
        email="mariana.costa@sga.edu.br",
        cpf="15350946056",
        curso_id=curso_id,
        status_academico="TRANCADO",
    )

    uid_a3 = repo.inserir_usuario_seed("pedro.ativo2", "hash_fake", perfil_id=1)
    mat_sem_aprovacao = repo.inserir_aluno_seed(
        matricula=20260103,
        usuario_id=uid_a3,
        nome="Pedro Santos",
        email="pedro.santos@sga.edu.br",
        cpf="98765432100",
        curso_id=curso_id,
        status_academico="ATIVO",
    )

    # Lucas foi aprovado em SI101 (8.5), SI102 (9.0, 30h) e SI202 (7.5)
    repo.inserir_matricula_turma_seed(mat_ativo, turma_origem, media_final=8.5, situacao="APROVADO")
    repo.inserir_matricula_turma_seed(mat_ativo, turma_origem_curta, media_final=9.0, situacao="APROVADO")
    repo.inserir_matricula_turma_seed(mat_ativo, turma_ja_aprovada, media_final=7.5, situacao="APROVADO")

    return {
        "disciplinas": {
            "origem_60h": d_origem_60h,
            "origem_curta_30h": d_origem_curta_30h,
            "alvo_60h": d_alvo_60h,
            "alvo_ja_aprovada": d_alvo_ja_aprovada,
            "avancada": d_avancada,
        },
        "mat_ativo": mat_ativo,
        "mat_trancado": mat_trancado,
        "mat_sem_aprovacao": mat_sem_aprovacao,
        "usuarios": {
            "aluno": uid_aluno_op,
            "professor": uid_prof_op,
            "secretaria": uid_sec,
            "financeiro": uid_fin,
            "admin": uid_admin,
            "inativo": uid_inativo,
        },
        "tokens": {
            "aluno": criar_token_sessao(uid_aluno_op, 1),
            "professor": criar_token_sessao(uid_prof_op, 2),
            "secretaria": criar_token_sessao(uid_sec, 3),
            "financeiro": criar_token_sessao(uid_fin, 4),
            "admin": criar_token_sessao(uid_admin, 5),
            "inativo": criar_token_sessao(uid_inativo, 3),
            "expirado": criar_token_sessao(uid_sec, 3, ttl_segundos=-10),
        },
    }


@pytest.fixture()
def client(repo: AproveitamentoRepository, dados_base: dict[str, Any]) -> TestClient:
    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
