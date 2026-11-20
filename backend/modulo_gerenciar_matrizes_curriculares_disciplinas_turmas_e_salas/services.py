from typing import Dict, List, Optional
from fastapi import HTTPException

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

# ---------------------------------------------------------------------------
# Repositório em memória
# ---------------------------------------------------------------------------
MATRIZES: List[dict] = []
DISCIPLINAS: List[dict] = []
DEPENDENCIAS: List[dict] = []
SALAS: List[dict] = []
TURMAS: List[dict] = []
ALOCACOES: List[dict] = []


def limpar_dados():
    """Utilizado para redefinir o estado durante testes."""
    MATRIZES.clear()
    DISCIPLINAS.clear()
    DEPENDENCIAS.clear()
    SALAS.clear()
    TURMAS.clear()
    ALOCACOES.clear()


# ---------------------------------------------------------------------------
# Serviços: Matrizes e Disciplinas (US1)
# ---------------------------------------------------------------------------

def buscar_matriz(matriz_id: int) -> dict:
    for m in MATRIZES:
        if m["id"] == matriz_id:
            return m
    raise HTTPException(status_code=404, detail="Matriz curricular não encontrada.")


def cadastrar_matriz(dados: MatrizEntrada) -> Matriz:
    for m in MATRIZES:
        if m["codigo"].lower() == dados.codigo.lower():
            raise HTTPException(
                status_code=409,
                detail=f"Já existe uma matriz curricular cadastrada com o código '{dados.codigo}'."
            )
    novo_id = max((m["id"] for m in MATRIZES), default=0) + 1
    matriz_dict = {"id": novo_id, **dados.model_dump()}
    MATRIZES.append(matriz_dict)
    return Matriz(**matriz_dict)


def listar_matrizes() -> List[Matriz]:
    return [Matriz(**m) for m in sorted(MATRIZES, key=lambda x: x["codigo"].lower())]


def detalhar_matriz(matriz_id: int) -> MatrizDetalhe:
    matriz_dict = buscar_matriz(matriz_id)
    disciplinas_da_matriz = [
        Disciplina(**d) for d in DISCIPLINAS if d["matriz_id"] == matriz_id
    ]
    dependencias_da_matriz = [
        Dependencia(**dep) for dep in DEPENDENCIAS if dep["matriz_id"] == matriz_id
    ]
    return MatrizDetalhe(
        **matriz_dict,
        disciplinas=disciplinas_da_matriz,
        dependencias=dependencias_da_matriz,
    )


def buscar_disciplina(disciplina_id: int) -> dict:
    for d in DISCIPLINAS:
        if d["id"] == disciplina_id:
            return d
    raise HTTPException(status_code=404, detail="Disciplina não encontrada.")


def cadastrar_disciplina(matriz_id: int, dados: DisciplinaEntrada) -> Disciplina:
    buscar_matriz(matriz_id)
    for d in DISCIPLINAS:
        if d["matriz_id"] == matriz_id and d["codigo"].lower() == dados.codigo.lower():
            raise HTTPException(
                status_code=409,
                detail=f"Já existe uma disciplina com o código '{dados.codigo}' nesta matriz."
            )
    novo_id = max((d["id"] for d in DISCIPLINAS), default=0) + 1
    carga_total = dados.carga_horaria_teorica + dados.carga_horaria_pratica
    disciplina_dict = {
        "id": novo_id,
        "matriz_id": matriz_id,
        "carga_horaria_total": carga_total,
        "status": "ativa",
        **dados.model_dump(),
    }
    DISCIPLINAS.append(disciplina_dict)
    return Disciplina(**disciplina_dict)


def listar_disciplinas(matriz_id: int) -> List[Disciplina]:
    buscar_matriz(matriz_id)
    return [
        Disciplina(**d)
        for d in DISCIPLINAS
        if d["matriz_id"] == matriz_id
    ]


# ---------------------------------------------------------------------------
# Serviços: Dependências Curriculares e Detecção de Ciclos DFS (US2)
# ---------------------------------------------------------------------------

def _existe_caminho_dependencia(matriz_id: int, origem_id: int, destino_id: int) -> bool:
    """
    Verifica se existe um caminho direcionado de dependência partindo de `origem_id` até `destino_id`.
    Se `origem_id` já alcança `destino_id`, adicionar uma dependência de `destino_id` para `origem_id`
    fecharia um ciclo proibido.
    """
    visitados = set()
    fila = [origem_id]

    while fila:
        atual = fila.pop(0)
        if atual == destino_id:
            return True
        if atual not in visitados:
            visitados.add(atual)
            # Vizinhos são as disciplinas das quais `atual` depende diretamente
            vizinhos = [
                dep["disciplina_requisito_id"]
                for dep in DEPENDENCIAS
                if dep["matriz_id"] == matriz_id and dep["disciplina_id"] == atual
            ]
            fila.extend(vizinhos)
    return False


def cadastrar_dependencia(matriz_id: int, dados: DependenciaEntrada) -> Dependencia:
    buscar_matriz(matriz_id)
    disc = buscar_disciplina(dados.disciplina_id)
    disc_req = buscar_disciplina(dados.disciplina_requisito_id)

    if disc["matriz_id"] != matriz_id or disc_req["matriz_id"] != matriz_id:
        raise HTTPException(
            status_code=400,
            detail="Ambas as disciplinas devem pertencer à mesma matriz curricular."
        )

    # Verificar se já existe exatamente essa dependência
    for dep in DEPENDENCIAS:
        if (
            dep["matriz_id"] == matriz_id
            and dep["disciplina_id"] == dados.disciplina_id
            and dep["disciplina_requisito_id"] == dados.disciplina_requisito_id
        ):
            raise HTTPException(
                status_code=409,
                detail="Esta dependência curricular já está cadastrada nesta matriz."
            )

    # Se a disciplina requerida já alcança a disciplina alvo, cria-se ciclo
    if _existe_caminho_dependencia(matriz_id, dados.disciplina_requisito_id, dados.disciplina_id):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Dependência circular detectada! A disciplina '{disc_req['nome']}' "
                f"já depende direta ou indiretamente de '{disc['nome']}'."
            )
        )

    novo_id = max((dep["id"] for dep in DEPENDENCIAS), default=0) + 1
    dep_dict = {
        "id": novo_id,
        "matriz_id": matriz_id,
        **dados.model_dump(),
    }
    DEPENDENCIAS.append(dep_dict)
    return Dependencia(**dep_dict)


def listar_dependencias(matriz_id: int) -> List[Dependencia]:
    buscar_matriz(matriz_id)
    return [
        Dependencia(**dep)
        for dep in DEPENDENCIAS
        if dep["matriz_id"] == matriz_id
    ]


# ---------------------------------------------------------------------------
# Serviços: Salas e Espaços Físicos (US3)
# ---------------------------------------------------------------------------

def buscar_sala(sala_id: int) -> dict:
    for s in SALAS:
        if s["id"] == sala_id:
            return s
    raise HTTPException(status_code=404, detail="Sala não encontrada.")


def cadastrar_sala(dados: SalaEntrada) -> Sala:
    for s in SALAS:
        if s["codigo"].lower() == dados.codigo.lower():
            raise HTTPException(
                status_code=409,
                detail=f"Já existe uma sala cadastrada com o código '{dados.codigo}'."
            )
    novo_id = max((s["id"] for s in SALAS), default=0) + 1
    sala_dict = {"id": novo_id, **dados.model_dump()}
    SALAS.append(sala_dict)
    return Sala(**sala_dict)


def listar_salas() -> List[Sala]:
    return [Sala(**s) for s in sorted(SALAS, key=lambda x: x["codigo"].lower())]


def consultar_ocupacao_sala(sala_id: int, periodo_letivo: Optional[str] = None) -> OcupacaoSala:
    sala_dict = buscar_sala(sala_id)
    alocacoes_sala = []

    for aloc in ALOCACOES:
        if aloc["sala_id"] == sala_id:
            turma = buscar_turma(aloc["turma_id"])
            if periodo_letivo is None or turma["periodo_letivo"] == periodo_letivo:
                alocacoes_sala.append(Alocacao(**aloc))

    return OcupacaoSala(
        sala=Sala(**sala_dict),
        periodo_letivo=periodo_letivo or "Todos",
        alocacoes=alocacoes_sala,
    )


# ---------------------------------------------------------------------------
# Serviços: Ofertas de Turmas e Alocação de Horários (US4)
# ---------------------------------------------------------------------------

def buscar_turma(turma_id: int) -> dict:
    for t in TURMAS:
        if t["id"] == turma_id:
            return t
    raise HTTPException(status_code=404, detail="Turma não encontrada.")


def cadastrar_turma(dados: TurmaEntrada) -> Turma:
    buscar_disciplina(dados.disciplina_id)

    for t in TURMAS:
        if (
            t["codigo"].lower() == dados.codigo.lower()
            and t["periodo_letivo"] == dados.periodo_letivo
        ):
            raise HTTPException(
                status_code=409,
                detail=f"Já existe uma turma com o código '{dados.codigo}' no período letivo {dados.periodo_letivo}."
            )

    novo_id = max((t["id"] for t in TURMAS), default=0) + 1
    turma_dict = {"id": novo_id, **dados.model_dump()}
    TURMAS.append(turma_dict)
    return Turma(**turma_dict)


def listar_turmas(periodo_letivo: Optional[str] = None) -> List[Turma]:
    resultado = []
    for t in TURMAS:
        if periodo_letivo is None or t["periodo_letivo"] == periodo_letivo:
            resultado.append(Turma(**t))
    return sorted(resultado, key=lambda x: x.codigo.lower())


def detalhar_turma(turma_id: int) -> TurmaDetalhe:
    turma_dict = buscar_turma(turma_id)
    alocs = [Alocacao(**a) for a in ALOCACOES if a["turma_id"] == turma_id]
    return TurmaDetalhe(**turma_dict, alocacoes=alocs)


def _ha_sobreposicao(inicio_a: str, fim_a: str, inicio_b: str, fim_b: str) -> bool:
    """Retorna True se há sobreposição temporal entre [inicio_a, fim_a] e [inicio_b, fim_b]."""
    return (inicio_a < fim_b) and (fim_a > inicio_b)


def alocar_horario_turma(turma_id: int, dados: AlocacaoEntrada) -> Alocacao:
    turma = buscar_turma(turma_id)
    sala = buscar_sala(dados.sala_id)

    # 1. Validação de capacidade física
    if turma["vagas_ofertadas"] > sala["capacidade_maxima"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"As vagas ofertadas para a turma ({turma['vagas_ofertadas']}) excedem a "
                f"capacidade máxima da sala '{sala['codigo']}' ({sala['capacidade_maxima']} lugares)."
            ),
        )

    periodo_letivo_atual = turma["periodo_letivo"]

    # 2. Validação de choque de salas
    for aloc in ALOCACOES:
        if aloc["sala_id"] == dados.sala_id and aloc["dia_semana"] == dados.dia_semana:
            turma_alocada = buscar_turma(aloc["turma_id"])
            if (
                turma_alocada["periodo_letivo"] == periodo_letivo_atual
                and turma_alocada["status"] != "cancelada"
            ):
                if _ha_sobreposicao(
                    dados.horario_inicio,
                    dados.horario_fim,
                    aloc["horario_inicio"],
                    aloc["horario_fim"],
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            f"Choque de salas detectado! A sala '{sala['codigo']}' já está alocada "
                            f"para a turma '{turma_alocada['codigo']}' na {dados.dia_semana} "
                            f"das {aloc['horario_inicio']} às {aloc['horario_fim']}."
                        ),
                    )

    # 3. Validação de choque docente
    professor_id = turma.get("professor_id")
    if professor_id is not None:
        for aloc in ALOCACOES:
            if aloc["dia_semana"] == dados.dia_semana:
                turma_alocada = buscar_turma(aloc["turma_id"])
                if (
                    turma_alocada["periodo_letivo"] == periodo_letivo_atual
                    and turma_alocada.get("professor_id") == professor_id
                    and turma_alocada["id"] != turma_id
                    and turma_alocada["status"] != "cancelada"
                ):
                    if _ha_sobreposicao(
                        dados.horario_inicio,
                        dados.horario_fim,
                        aloc["horario_inicio"],
                        aloc["horario_fim"],
                    ):
                        raise HTTPException(
                            status_code=409,
                            detail=(
                                f"Choque de horário docente! O professor (ID {professor_id}) já possui "
                                f"a turma '{turma_alocada['codigo']}' alocada na {dados.dia_semana} "
                                f"das {aloc['horario_inicio']} às {aloc['horario_fim']}."
                            ),
                        )

    novo_id = max((a["id"] for a in ALOCACOES), default=0) + 1
    aloc_dict = {
        "id": novo_id,
        "turma_id": turma_id,
        **dados.model_dump(),
    }
    ALOCACOES.append(aloc_dict)
    return Alocacao(**aloc_dict)


def listar_alocacoes_turma(turma_id: int) -> List[Alocacao]:
    buscar_turma(turma_id)
    return [Alocacao(**a) for a in ALOCACOES if a["turma_id"] == turma_id]
