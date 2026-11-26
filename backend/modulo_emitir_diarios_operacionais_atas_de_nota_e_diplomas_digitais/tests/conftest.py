"""Fixtures compartilhadas para os testes do módulo SGA-25."""

from pathlib import Path
import sys
from typing import Any
from fastapi.testclient import TestClient
import pytest

MODULE_DIR = Path(__file__).resolve().parent.parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

try:
    from ..repository import DocumentoRepository, get_repository
    from ..router import app
    from ..security import criar_token_sessao
except ImportError:
    from repository import DocumentoRepository, get_repository
    from router import app
    from security import criar_token_sessao


@pytest.fixture()
def repo() -> DocumentoRepository:
    instancia = DocumentoRepository(db_path=":memory:")
    yield instancia
    instancia.close()


@pytest.fixture()
def dados_base(repo: DocumentoRepository) -> dict[str, Any]:
    """Cria massa institucional completa: operadores RBAC, curso, turmas, alunos, notas e frequências."""
    uid_aluno_op = repo.inserir_usuario_seed("aluno.op", "hash_fake", perfil_id=1, status_conta=1)
    uid_prof_op = repo.inserir_usuario_seed("prof.op", "hash_fake", perfil_id=2, status_conta=1)
    uid_sec = repo.inserir_usuario_seed("secretaria.op", "hash_fake", perfil_id=3, status_conta=1)
    uid_fin = repo.inserir_usuario_seed("financeiro.op", "hash_fake", perfil_id=4, status_conta=1)
    uid_admin = repo.inserir_usuario_seed("admin.op", "hash_fake", perfil_id=5, status_conta=1)
    uid_inativo = repo.inserir_usuario_seed("sec.inativa", "hash_fake", perfil_id=3, status_conta=0)

    dep_id = repo.inserir_departamento_seed("DCET-I", "Departamento de Ciências Exatas", "DCET1")
    prof_id = repo.inserir_professor_seed(
        nome="Prof. Alex Coelho",
        email="alex.coelho@sga.edu.br",
        cpf="11122233344",
        departamento="DCET-I",
        titulacao="Doutorado",
        usuario_id=uid_prof_op,
    )
    curso_id = repo.inserir_curso_seed(
        codigo_mec="MEC-SI-2026",
        nome="Sistemas de Informação",
        departamento_id=dep_id,
        grau_academico="Bacharelado",
        modalidade="PRESENCIAL",
        carga_horaria_total=3000,
        duracao_semestres=8,
        coordenador_id=prof_id,
    )
    matriz_id = repo.inserir_matriz_seed(curso_id=curso_id, codigo_matriz="MAT-SI-2026-1")
    disc_id = repo.inserir_disciplina_seed(
        matriz_id=matriz_id,
        codigo="SI401",
        nome="Engenharia de Software II",
        carga_horaria=60,
        creditos=4,
    )
    periodo_id = repo.inserir_periodo_seed(codigo="2026.2", ano=2026, semestre=2)

    # Turma 1: consolidada com 3 alunos (aprovado, reprovado nota, reprovado falta com média alta)
    turma_consolidada_id = repo.inserir_turma_seed(
        codigo_turma="SI-20262-A",
        disciplina_id=disc_id,
        periodo_letivo_id=periodo_id,
        professor_id=prof_id,
        turno="NOTURNO",
        status_turma="ENCERRADA",
    )
    # Turma 2: vazia (sem alunos matriculados)
    turma_vazia_id = repo.inserir_turma_seed(
        codigo_turma="SI-20262-VAZIA",
        disciplina_id=disc_id,
        periodo_letivo_id=periodo_id,
        professor_id=prof_id,
        turno="MATUTINO",
    )
    # Turma 3: em andamento com aluno sem notas lançadas
    turma_pendente_id = repo.inserir_turma_seed(
        codigo_turma="SI-20262-PEND",
        disciplina_id=disc_id,
        periodo_letivo_id=periodo_id,
        professor_id=prof_id,
        turno="VESPERTINO",
    )

    # Alunos com diferentes situações acadêmicas
    uid_a1 = repo.inserir_usuario_seed("ana.formada", "hash_fake", perfil_id=1)
    mat_formado = repo.inserir_aluno_seed(
        matricula=20260001,
        usuario_id=uid_a1,
        nome="Ana Clara Souza",
        email="ana.clara@sga.edu.br",
        cpf="52998224725",
        curso_id=curso_id,
        status_academico="FORMADO",
        ira=9.15,
    )

    uid_a2 = repo.inserir_usuario_seed("bruno.ativo", "hash_fake", perfil_id=1)
    mat_ativo = repo.inserir_aluno_seed(
        matricula=20260002,
        usuario_id=uid_a2,
        nome="Bruno Henrique Lima",
        email="bruno.lima@sga.edu.br",
        cpf="15350946056",
        curso_id=curso_id,
        status_academico="ATIVO",
        ira=5.20,
    )

    uid_a3 = repo.inserir_usuario_seed("carla.faltosa", "hash_fake", perfil_id=1)
    mat_faltoso = repo.inserir_aluno_seed(
        matricula=20260003,
        usuario_id=uid_a3,
        nome="Carla Mendes Silva",
        email="carla.silva@sga.edu.br",
        cpf="98765432100",
        curso_id=curso_id,
        status_academico="TRANCADO",
        ira=8.40,
    )

    uid_a4 = repo.inserir_usuario_seed("diego.semcurso", "hash_fake", perfil_id=1)
    mat_sem_curso = repo.inserir_aluno_seed(
        matricula=20260004,
        usuario_id=uid_a4,
        nome="Diego Oliveira",
        email="diego.oliveira@sga.edu.br",
        cpf="12312312387",
        curso_id=None,
        status_academico="FORMADO",
        ira=7.50,
    )

    # Matrículas na Turma 1 (consolidada)
    # Ana: média ponderada (8.0*1 + 9.0*2)/3 = 8.67, 90% presença -> APROVADO
    mt_ana = repo.inserir_matricula_turma_seed(mat_formado, turma_consolidada_id, percentual_frequencia=90.0)
    repo.inserir_avaliacao_seed(mt_ana, "N1", 8.0, peso=1.0)
    repo.inserir_avaliacao_seed(mt_ana, "N2", 9.0, peso=2.0)
    repo.inserir_frequencia_seed(mt_ana, "2026-08-10", presente=True, quantidade_aulas=18)
    repo.inserir_frequencia_seed(mt_ana, "2026-08-17", presente=False, quantidade_aulas=2)

    # Bruno: média (4.0 + 5.0)/2 = 4.50, 100% presença -> REPROVADO_NOTA
    mt_bruno = repo.inserir_matricula_turma_seed(mat_ativo, turma_consolidada_id, percentual_frequencia=100.0)
    repo.inserir_avaliacao_seed(mt_bruno, "N1", 4.0, peso=1.0)
    repo.inserir_avaliacao_seed(mt_bruno, "N2", 5.0, peso=1.0)
    repo.inserir_frequencia_seed(mt_bruno, "2026-08-10", presente=True, quantidade_aulas=20)

    # Carla: média 9.00, mas 30% faltas (70% presença < 75%) -> REPROVADO_FALTA
    mt_carla = repo.inserir_matricula_turma_seed(mat_faltoso, turma_consolidada_id, percentual_frequencia=70.0)
    repo.inserir_avaliacao_seed(mt_carla, "N1", 9.0, peso=1.0)
    repo.inserir_avaliacao_seed(mt_carla, "N2", 9.0, peso=1.0)
    repo.inserir_frequencia_seed(mt_carla, "2026-08-10", presente=True, quantidade_aulas=14)
    repo.inserir_frequencia_seed(mt_carla, "2026-08-17", presente=False, quantidade_aulas=6)

    # Matrícula na Turma 3 (pendente, sem nota)
    repo.inserir_matricula_turma_seed(mat_ativo, turma_pendente_id, media_final=None, percentual_frequencia=80.0)

    return {
        "curso_id": curso_id,
        "turma_consolidada_id": turma_consolidada_id,
        "turma_vazia_id": turma_vazia_id,
        "turma_pendente_id": turma_pendente_id,
        "mat_formado": mat_formado,
        "mat_ativo": mat_ativo,
        "mat_faltoso": mat_faltoso,
        "mat_sem_curso": mat_sem_curso,
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
def client(repo: DocumentoRepository, dados_base: dict[str, Any]) -> TestClient:
    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
