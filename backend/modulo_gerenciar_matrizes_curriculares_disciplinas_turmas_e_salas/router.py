from typing import List, Optional
from fastapi import APIRouter

try:
    from schemas import (
        Alocacao,
        AlocacaoEntrada,
        Dependencia,
        DependenciaEntrada,
        Disciplina,
        DisciplinaEntrada,
        Matriz,
        MatrizDetalhe,
        MatrizEntrada,
        OcupacaoSala,
        Sala,
        SalaEntrada,
        Turma,
        TurmaDetalhe,
        TurmaEntrada,
    )
    import services
except ImportError:
    from .schemas import (
        Alocacao,
        AlocacaoEntrada,
        Dependencia,
        DependenciaEntrada,
        Disciplina,
        DisciplinaEntrada,
        Matriz,
        MatrizDetalhe,
        MatrizEntrada,
        OcupacaoSala,
        Sala,
        SalaEntrada,
        Turma,
        TurmaDetalhe,
        TurmaEntrada,
    )
    from . import services

router = APIRouter()


# ---------------------------------------------------------------------------
# Endpoints: Matrizes Curriculares e Disciplinas (US1)
# ---------------------------------------------------------------------------

@router.post("/api/matrizes", response_model=Matriz, status_code=201, tags=["Matrizes Curriculares"])
def criar_matriz(dados: MatrizEntrada):
    """Cria uma nova matriz curricular com código único."""
    return services.cadastrar_matriz(dados)


@router.get("/api/matrizes", response_model=List[Matriz], tags=["Matrizes Curriculares"])
def listar_matrizes():
    """Lista todas as matrizes curriculares cadastradas."""
    return services.listar_matrizes()


@router.get("/api/matrizes/{matriz_id}", response_model=MatrizDetalhe, tags=["Matrizes Curriculares"])
def detalhar_matriz(matriz_id: int):
    """Retorna os dados da matriz, suas disciplinas e regras de dependência."""
    return services.detalhar_matriz(matriz_id)


@router.post("/api/matrizes/{matriz_id}/disciplinas", response_model=Disciplina, status_code=201, tags=["Disciplinas"])
def adicionar_disciplina(matriz_id: int, dados: DisciplinaEntrada):
    """Adiciona um componente curricular à matriz com cálculo automático de horas."""
    return services.cadastrar_disciplina(matriz_id, dados)


@router.get("/api/matrizes/{matriz_id}/disciplinas", response_model=List[Disciplina], tags=["Disciplinas"])
def listar_disciplinas(matriz_id: int):
    """Lista todas as disciplinas vinculadas a uma matriz curricular."""
    return services.listar_disciplinas(matriz_id)


# ---------------------------------------------------------------------------
# Endpoints: Dependências Curriculares (US2)
# ---------------------------------------------------------------------------

@router.post("/api/matrizes/{matriz_id}/dependencias", response_model=Dependencia, status_code=201, tags=["Dependências Curriculares"])
def criar_dependencia(matriz_id: int, dados: DependenciaEntrada):
    """Registra pré-requisito ou correquisito com validação rigorosa de ciclo acíclico (DFS)."""
    return services.cadastrar_dependencia(matriz_id, dados)


@router.get("/api/matrizes/{matriz_id}/dependencias", response_model=List[Dependencia], tags=["Dependências Curriculares"])
def listar_dependencias(matriz_id: int):
    """Lista as dependências curriculares cadastradas na matriz."""
    return services.listar_dependencias(matriz_id)


# ---------------------------------------------------------------------------
# Endpoints: Salas e Espaços Físicos (US3)
# ---------------------------------------------------------------------------

@router.post("/api/salas", response_model=Sala, status_code=201, tags=["Salas"])
def criar_sala(dados: SalaEntrada):
    """Cadastra um espaço físico didático ou laboratório com capacidade máxima."""
    return services.cadastrar_sala(dados)


@router.get("/api/salas", response_model=List[Sala], tags=["Salas"])
def listar_salas():
    """Lista as salas e laboratórios cadastrados."""
    return services.listar_salas()


@router.get("/api/salas/{sala_id}/ocupacao", response_model=OcupacaoSala, tags=["Salas"])
def consultar_ocupacao_sala(sala_id: int, periodo_letivo: Optional[str] = None):
    """Consulta a grade de horários ocupados de uma sala em determinado período letivo."""
    return services.consultar_ocupacao_sala(sala_id, periodo_letivo)


# ---------------------------------------------------------------------------
# Endpoints: Turmas e Alocações de Horário (US4)
# ---------------------------------------------------------------------------

@router.post("/api/turmas", response_model=Turma, status_code=201, tags=["Turmas"])
def criar_turma(dados: TurmaEntrada):
    """Cria uma nova oferta de turma para uma disciplina no período letivo especificado."""
    return services.cadastrar_turma(dados)


@router.get("/api/turmas", response_model=List[Turma], tags=["Turmas"])
def listar_turmas(periodo_letivo: Optional[str] = None):
    """Lista as turmas cadastradas, com filtro opcional por período letivo."""
    return services.listar_turmas(periodo_letivo)


@router.get("/api/turmas/{turma_id}", response_model=TurmaDetalhe, tags=["Turmas"])
def detalhar_turma(turma_id: int):
    """Obtém detalhes da turma e suas alocações de horário e sala."""
    return services.detalhar_turma(turma_id)


@router.post("/api/turmas/{turma_id}/alocacoes", response_model=Alocacao, status_code=201, tags=["Alocações e Horários"])
def alocar_horario(turma_id: int, dados: AlocacaoEntrada):
    """Aloca sala, dia da semana e horário para a turma com detecção de choques de sala e docente."""
    return services.alocar_horario_turma(turma_id, dados)


@router.get("/api/turmas/{turma_id}/alocacoes", response_model=List[Alocacao], tags=["Alocações e Horários"])
def listar_alocacoes(turma_id: int):
    """Lista as alocações de horários e salas de uma turma."""
    return services.listar_alocacoes_turma(turma_id)
