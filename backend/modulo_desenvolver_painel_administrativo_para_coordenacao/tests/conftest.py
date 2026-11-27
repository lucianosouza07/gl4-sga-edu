"""Fixtures compartilhadas para os testes do módulo SGA-27."""

from typing import Any
from fastapi.testclient import TestClient
import pytest

try:
    from ..repository import PainelCoordenacaoRepository, get_repository
    from ..router import app
    from ..security import criar_token_sessao
except ImportError:
    from repository import PainelCoordenacaoRepository, get_repository
    from router import app
    from security import criar_token_sessao


@pytest.fixture()
def repo() -> PainelCoordenacaoRepository:
    instancia = PainelCoordenacaoRepository(db_path=":memory:")
    yield instancia
    instancia.close()


@pytest.fixture()
def dados_base(repo: PainelCoordenacaoRepository) -> dict[str, Any]:
    """Cria massa institucional completa para KPIs, evasão, conflitos de oferta, requerimentos e docentes."""
    uid_aluno_op = repo.inserir_usuario_seed("aluno.op", "hash_fake", perfil_id=1, status_conta=1)
    uid_prof_op = repo.inserir_usuario_seed("prof.op", "hash_fake", perfil_id=2, status_conta=1)
    uid_sec = repo.inserir_usuario_seed("secretaria.op", "hash_fake", perfil_id=3, status_conta=1)
    uid_fin = repo.inserir_usuario_seed("financeiro.op", "hash_fake", perfil_id=4, status_conta=1)
    uid_admin = repo.inserir_usuario_seed("admin.op", "hash_fake", perfil_id=5, status_conta=1)
    uid_inativo = repo.inserir_usuario_seed("sec.inativa", "hash_fake", perfil_id=3, status_conta=0)

    dep_id = repo.inserir_departamento_seed("DCET-I", "Departamento de Ciências Exatas", "DCET1")
    prof1 = repo.inserir_professor_seed(
        nome="Prof. Alex Coelho",
        email="alex@sga.edu.br",
        cpf="11122233344",
        departamento="DCET-I",
        titulacao="Doutorado",
        usuario_id=uid_prof_op,
    )
    prof2 = repo.inserir_professor_seed(
        nome="Profa. Ana Rocha",
        email="ana.rocha@sga.edu.br",
        cpf="22233344455",
        departamento="DCET-I",
        titulacao="Mestrado",
    )

    curso_si = repo.inserir_curso_seed("MEC-SI-2026", "Sistemas de Informação", dep_id, coordenador_id=prof2)
    curso_vazio = repo.inserir_curso_seed("MEC-ES-2026", "Engenharia de Software", dep_id)

    matriz_si = repo.inserir_matriz_seed(curso_si, "MAT-SI-2026")
    d1 = repo.inserir_disciplina_seed(matriz_si, "SI101", "Algoritmos", carga_horaria=60)
    d2 = repo.inserir_disciplina_seed(matriz_si, "SI201", "Banco de Dados", carga_horaria=60)
    d3 = repo.inserir_disciplina_seed(matriz_si, "SI301", "Engenharia Web", carga_horaria=60)

    p_atual = repo.inserir_periodo_seed("2026.2", 2026, 2)
    p_limpo = repo.inserir_periodo_seed("2027.1", 2027, 1)

    sala_a = repo.inserir_sala_seed("B1-101", "Bloco 1", capacidade=40)
    sala_b = repo.inserir_sala_seed("B1-102", "Bloco 1", capacidade=40)

    # Turmas em 2026.2:
    # t1: prof1, sala_a, seg 19:00-20:40 (vagas=2 -> ficará lotada!)
    t1 = repo.inserir_turma_seed("SI101-A", d1, p_atual, professor_id=prof1, sala_id=sala_a, turno="NOTURNO", vagas_totais=2)
    repo.inserir_horario_turma_seed(t1, 2, "19:00", "20:40")

    # t2: prof2, sala_a, seg 20:00-21:40 -> CHOQUE_SALA com t1 (20:00-20:40)!
    t2 = repo.inserir_turma_seed("SI201-A", d2, p_atual, professor_id=prof2, sala_id=sala_a, turno="NOTURNO", vagas_totais=40)
    repo.inserir_horario_turma_seed(t2, 2, "20:00", "21:40")

    # t3: prof1, sala_b, seg 19:30-21:10 -> CHOQUE_DOCENTE com t1 (19:30-20:40)!
    t3 = repo.inserir_turma_seed("SI301-A", d3, p_atual, professor_id=prof1, sala_id=sala_b, turno="NOTURNO", vagas_totais=40)
    repo.inserir_horario_turma_seed(t3, 2, "19:30", "21:10")

    # t4: prof2, sala_b, qua 20:40-22:20 + t5 contígua qua 19:00-20:40 -> SEM CONFLITO!
    t4 = repo.inserir_turma_seed("SI101-B", d1, p_atual, professor_id=prof2, sala_id=sala_b, turno="NOTURNO", vagas_totais=40)
    repo.inserir_horario_turma_seed(t4, 4, "20:40", "22:20")

    t5 = repo.inserir_turma_seed("SI201-B", d2, p_atual, professor_id=prof2, sala_id=sala_b, turno="NOTURNO", vagas_totais=40)
    repo.inserir_horario_turma_seed(t5, 4, "19:00", "20:40")

    # t_cancelada: mesmo horário e sala de t1, mas CANCELADA -> NÃO deve gerar conflito!
    t_cancel = repo.inserir_turma_seed("SI301-CANC", d3, p_atual, professor_id=prof1, sala_id=sala_a, turno="NOTURNO", status_turma="CANCELADA")
    repo.inserir_horario_turma_seed(t_cancel, 2, "19:00", "20:40")

    # t_pend: sem professor, sem sala, sem horários -> deve aparecer em pendências!
    t_pend = repo.inserir_turma_seed("SI301-PEND", d3, p_atual, professor_id=None, sala_id=None, turno="MATUTINO", vagas_totais=30)

    # Turma em 2027.1 sem conflitos
    t_limpa = repo.inserir_turma_seed("SI101-20271", d1, p_limpo, professor_id=prof1, sala_id=sala_a, turno="MATUTINO")
    repo.inserir_horario_turma_seed(t_limpa, 2, "08:00", "09:40")

    # Alunos do curso SI (4 alunos: 2 ativos [1 normal, 1 risco freq+IRA], 1 trancado, 1 cancelado)
    u_a1 = repo.inserir_usuario_seed("a1.normal", "hash_fake", 1)
    m_normal = repo.inserir_aluno_seed(20261001, u_a1, "Beatriz Lima", "beatriz@sga.edu.br", "52998224725", curso_si, "ATIVO", ira=8.8)

    u_a2 = repo.inserir_usuario_seed("a2.risco", "hash_fake", 1)
    m_risco = repo.inserir_aluno_seed(20261002, u_a2, "Carlos Souza", "carlos@sga.edu.br", "15350946056", curso_si, "ATIVO", ira=4.8)

    u_a3 = repo.inserir_usuario_seed("a3.tranc", "hash_fake", 1)
    m_trancado = repo.inserir_aluno_seed(20261003, u_a3, "Fernanda Alves", "fernanda@sga.edu.br", "98765432100", curso_si, "TRANCADO", ira=7.2)

    u_a4 = repo.inserir_usuario_seed("a4.canc", "hash_fake", 1)
    m_cancelado = repo.inserir_aluno_seed(20261004, u_a4, "Gabriel Nunes", "gabriel@sga.edu.br", "12312312387", curso_si, "CANCELADO", ira=5.5)

    # Matrículas em t1 (ocupa 2/2 -> lotação esgotada!)
    repo.inserir_matricula_turma_seed(m_normal, t1, percentual_frequencia=92.0)
    repo.inserir_matricula_turma_seed(m_risco, t1, percentual_frequencia=65.0)  # < 75% -> risco!

    # Movimentações deferidas
    repo.inserir_movimentacao_seed(m_trancado, p_atual, "TRANCAMENTO", "Motivo pessoal", "DEFERIDO")
    repo.inserir_movimentacao_seed(m_cancelado, p_atual, "CANCELAMENTO", "Desistência", "DEFERIDO")

    # Requerimentos
    req_aberto = repo.inserir_requerimento_seed(
        "REQ-2026-0001", m_normal, "REVISAO_NOTA", "Solicito revisão da N2", p_atual, "ABERTO"
    )
    req_deferido = repo.inserir_requerimento_seed(
        "REQ-2026-0002", m_risco, "SEGUNDA_CHAMADA", "Atestado médico", p_atual, "DEFERIDO", "Deferido."
    )

    return {
        "curso_si": curso_si,
        "curso_vazio": curso_vazio,
        "periodo_atual": p_atual,
        "periodo_limpo": p_limpo,
        "professores": {"prof1": prof1, "prof2": prof2},
        "turmas": {"t1": t1, "t2": t2, "t3": t3, "t_pend": t_pend, "t_cancel": t_cancel},
        "alunos": {"normal": m_normal, "risco": m_risco, "trancado": m_trancado, "cancelado": m_cancelado},
        "requerimentos": {"aberto": req_aberto, "deferido": req_deferido},
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
def client(repo: PainelCoordenacaoRepository, dados_base: dict[str, Any]) -> TestClient:
    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
