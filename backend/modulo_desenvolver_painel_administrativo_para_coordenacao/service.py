"""Regras de negócio do painel administrativo da coordenação (SGA-27)."""

from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import HTTPException, status

try:
    from .audit_service import serializar_snapshot_auditoria
    from .repository import PainelCoordenacaoRepository
    from .schemas import (
        DespachoRequerimentoEntrada,
        LIMIAR_FREQUENCIA_RISCO,
        LIMIAR_IRA_RISCO,
        STATUS_EVASAO,
        StatusRequerimentoEnum,
        TIPOS_MOVIMENTACAO_EVASAO,
        TipoConflitoEnum,
    )
    from .security import OperadorAutenticado
except ImportError:
    from audit_service import serializar_snapshot_auditoria
    from repository import PainelCoordenacaoRepository
    from schemas import (
        DespachoRequerimentoEntrada,
        LIMIAR_FREQUENCIA_RISCO,
        LIMIAR_IRA_RISCO,
        STATUS_EVASAO,
        StatusRequerimentoEnum,
        TIPOS_MOVIMENTACAO_EVASAO,
        TipoConflitoEnum,
    )
    from security import OperadorAutenticado


def _para_minutos(hhmm: str) -> int:
    partes = hhmm.strip().split(":")
    return int(partes[0]) * 60 + int(partes[1])


def _de_minutos(total_min: int) -> str:
    return f"{total_min // 60:02d}:{total_min % 60:02d}"


def _calcular_pendencias_turma(turma: dict[str, Any]) -> list[str]:
    pendencias: list[str] = []
    if turma["professor_id"] is None:
        pendencias.append("sem_professor")
    if turma["sala_id"] is None:
        pendencias.append("sem_sala")
    if not turma["horarios"]:
        pendencias.append("sem_horarios")
    if int(turma["vagas_totais"]) > 0 and int(turma["vagas_ocupadas"]) >= int(turma["vagas_totais"]):
        pendencias.append("lotacao_esgotada")
    return pendencias


class PainelCoordenacaoService:
    """Serviço gerencial de KPIs, evasão, oferta/conflitos, requerimentos, docentes e auditoria."""

    def __init__(self, repo: PainelCoordenacaoRepository) -> None:
        self.repo = repo

    def _validar_filtros(
        self, curso_id: Optional[int] = None, periodo_letivo_id: Optional[int] = None
    ) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]]]:
        curso = None
        if curso_id is not None:
            curso = self.repo.buscar_curso_por_id(curso_id)
            if curso is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Curso não encontrado.",
                )
        periodo = None
        if periodo_letivo_id is not None:
            periodo = self.repo.buscar_periodo_por_id(periodo_letivo_id)
            if periodo is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Período letivo não encontrado.",
                )
        return curso, periodo

    # ------------------------------------------------------------------
    # US1: Painel de KPIs e Relatório de Evasão / Alertas de Risco
    # ------------------------------------------------------------------

    def _calcular_evasao_base(
        self,
        alunos: list[dict[str, Any]],
        movimentacoes: list[dict[str, Any]],
    ) -> tuple[dict[str, int], set[int], float]:
        por_tipo: dict[str, int] = {t: 0 for t in TIPOS_MOVIMENTACAO_EVASAO}
        evadidos_unicos: set[int] = set()

        for aluno in alunos:
            if str(aluno["status_academico"]).upper() in STATUS_EVASAO:
                evadidos_unicos.add(int(aluno["matricula"]))

        matriculas_escopo = {int(a["matricula"]) for a in alunos}
        for mov in movimentacoes:
            tipo = str(mov["tipo_movimentacao"]).upper()
            if tipo in por_tipo:
                por_tipo[tipo] += 1
                mat = int(mov["aluno_matricula"])
                if mat in matriculas_escopo:
                    evadidos_unicos.add(mat)

        total_alunos = len(alunos)
        taxa = round(min(100.0, (len(evadidos_unicos) / total_alunos) * 100.0), 2) if total_alunos > 0 else 0.0
        return por_tipo, evadidos_unicos, taxa

    def obter_resumo_painel(
        self,
        curso_id: Optional[int] = None,
        periodo_letivo_id: Optional[int] = None,
    ) -> dict[str, Any]:
        curso, periodo = self._validar_filtros(curso_id=curso_id, periodo_letivo_id=periodo_letivo_id)

        alunos = self.repo.listar_alunos_escopo(curso_id=curso_id)
        alunos_ativos = [a for a in alunos if str(a["status_academico"]).upper() == "ATIVO"]
        movimentacoes = self.repo.listar_movimentacoes_deferidas(
            curso_id=curso_id, periodo_letivo_id=periodo_letivo_id
        )
        por_tipo, _evadidos, taxa_evasao = self._calcular_evasao_base(alunos, movimentacoes)

        turmas = [
            t
            for t in self.repo.listar_oferta_turmas(
                periodo_letivo_id=periodo_letivo_id, curso_id=curso_id
            )
            if str(t["status_turma"]).upper() != "CANCELADA"
        ]
        matriculas = self.repo.listar_matriculas_escopo(
            curso_id=curso_id, periodo_letivo_id=periodo_letivo_id
        )
        processos_abertos = self.repo.contar_processos_abertos(
            curso_id=curso_id, periodo_letivo_id=periodo_letivo_id
        )

        docentes_alocados = {int(t["professor_id"]) for t in turmas if t["professor_id"] is not None}
        total_vagas = sum(int(t["vagas_totais"]) for t in turmas)
        total_ocupadas = sum(int(t["vagas_ocupadas"]) for t in turmas)
        taxa_ocupacao = round((total_ocupadas / total_vagas) * 100.0, 2) if total_vagas > 0 else 0.0
        ira_medio = (
            round(sum(float(a["ira"]) for a in alunos_ativos) / len(alunos_ativos), 2)
            if alunos_ativos
            else 0.0
        )

        return {
            "curso_id": curso_id,
            "curso_nome": str(curso["nome"]) if curso else None,
            "periodo_letivo_id": periodo_letivo_id,
            "periodo_letivo_codigo": str(periodo["codigo"]) if periodo else None,
            "processos_abertos": processos_abertos,
            "matriculas_ativas_turmas": len(matriculas),
            "trancamentos_deferidos": por_tipo["TRANCAMENTO"],
            "movimentacoes_evasao_deferidas": sum(por_tipo.values()),
            "docentes_ativos_alocados": len(docentes_alocados),
            "total_turmas_ofertadas": len(turmas),
            "total_alunos_vinculados": len(alunos),
            "total_alunos_ativos": len(alunos_ativos),
            "taxa_ocupacao_media_percentual": taxa_ocupacao,
            "ira_medio_ativos": ira_medio,
            "taxa_evasao_percentual": taxa_evasao,
        }

    def obter_relatorio_evasao(
        self,
        curso_id: Optional[int] = None,
        periodo_letivo_id: Optional[int] = None,
    ) -> dict[str, Any]:
        self._validar_filtros(curso_id=curso_id, periodo_letivo_id=periodo_letivo_id)

        alunos = self.repo.listar_alunos_escopo(curso_id=curso_id)
        movimentacoes = self.repo.listar_movimentacoes_deferidas(
            curso_id=curso_id, periodo_letivo_id=periodo_letivo_id
        )
        por_tipo, evadidos_unicos, taxa_evasao = self._calcular_evasao_base(alunos, movimentacoes)

        matriculas = self.repo.listar_matriculas_escopo(
            curso_id=curso_id, periodo_letivo_id=periodo_letivo_id
        )
        menor_freq_por_aluno: dict[int, float] = {}
        for m in matriculas:
            mat = int(m["aluno_matricula"])
            freq = round(float(m["percentual_frequencia"]), 2)
            if mat not in menor_freq_por_aluno or freq < menor_freq_por_aluno[mat]:
                menor_freq_por_aluno[mat] = freq

        alertas: list[dict[str, Any]] = []
        for aluno in alunos:
            if str(aluno["status_academico"]).upper() != "ATIVO":
                continue
            mat = int(aluno["matricula"])
            ira = round(float(aluno["ira"]), 2)
            menor_freq = menor_freq_por_aluno.get(mat)
            motivos: list[str] = []
            if menor_freq is not None and menor_freq < LIMIAR_FREQUENCIA_RISCO:
                motivos.append(
                    f"Frequência abaixo de {LIMIAR_FREQUENCIA_RISCO:.0f}% ({menor_freq:.2f}%)."
                )
            if ira < LIMIAR_IRA_RISCO:
                motivos.append(f"IRA abaixo do critério institucional ({ira:.2f} < {LIMIAR_IRA_RISCO:.2f}).")

            if motivos:
                alertas.append(
                    {
                        "matricula": mat,
                        "nome": str(aluno["nome"] or ""),
                        "curso_nome": aluno["curso_nome"],
                        "ira": ira,
                        "menor_frequencia_percentual": menor_freq,
                        "motivos_alerta": motivos,
                    }
                )

        return {
            "curso_id": curso_id,
            "periodo_letivo_id": periodo_letivo_id,
            "total_alunos_vinculados": len(alunos),
            "alunos_em_evasao_unicos": len(evadidos_unicos),
            "taxa_evasao_percentual": taxa_evasao,
            "movimentacoes_por_tipo": por_tipo,
            "total_alertas_risco": len(alertas),
            "alertas_risco": alertas,
        }

    # ------------------------------------------------------------------
    # US2: Oferta de Turmas e Diagnóstico de Conflitos
    # ------------------------------------------------------------------

    def listar_oferta_turmas(
        self,
        periodo_letivo_id: Optional[int] = None,
        curso_id: Optional[int] = None,
        turno: Optional[str] = None,
        status_turma: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        self._validar_filtros(curso_id=curso_id, periodo_letivo_id=periodo_letivo_id)
        turmas = self.repo.listar_oferta_turmas(
            periodo_letivo_id=periodo_letivo_id,
            curso_id=curso_id,
            turno=turno,
            status_turma=status_turma,
        )
        itens: list[dict[str, Any]] = []
        for t in turmas:
            vagas_totais = int(t["vagas_totais"])
            vagas_ocupadas = int(t["vagas_ocupadas"])
            taxa = round((vagas_ocupadas / vagas_totais) * 100.0, 2) if vagas_totais > 0 else 0.0
            itens.append(
                {
                    "id_turma": int(t["id_turma"]),
                    "codigo_turma": str(t["codigo_turma"]),
                    "disciplina_codigo": str(t["disciplina_codigo"]),
                    "disciplina_nome": str(t["disciplina_nome"]),
                    "carga_horaria": int(t["carga_horaria"]),
                    "curso_nome": str(t["curso_nome"]),
                    "periodo_letivo_codigo": str(t["periodo_letivo_codigo"]),
                    "turno": str(t["turno"]),
                    "status_turma": str(t["status_turma"]),
                    "professor_id": int(t["professor_id"]) if t["professor_id"] is not None else None,
                    "professor_nome": t["professor_nome"],
                    "sala_id": int(t["sala_id"]) if t["sala_id"] is not None else None,
                    "codigo_sala": t["codigo_sala"],
                    "vagas_totais": vagas_totais,
                    "vagas_ocupadas": vagas_ocupadas,
                    "taxa_ocupacao_percentual": taxa,
                    "horarios": t["horarios"],
                    "pendencias": _calcular_pendencias_turma(t),
                }
            )
        return itens

    def diagnosticar_conflitos_oferta(
        self,
        periodo_letivo_id: int,
        curso_id: Optional[int] = None,
    ) -> dict[str, Any]:
        _curso, periodo = self._validar_filtros(curso_id=curso_id, periodo_letivo_id=periodo_letivo_id)
        assert periodo is not None

        turmas_ativas = [
            t
            for t in self.repo.listar_oferta_turmas(
                periodo_letivo_id=periodo_letivo_id, curso_id=curso_id
            )
            if str(t["status_turma"]).upper() != "CANCELADA"
        ]

        conflitos: list[dict[str, Any]] = []
        choques_sala = 0
        choques_docente = 0

        for idx_a in range(len(turmas_ativas)):
            ta = turmas_ativas[idx_a]
            for idx_b in range(idx_a + 1, len(turmas_ativas)):
                tb = turmas_ativas[idx_b]
                mesma_sala = ta["sala_id"] is not None and ta["sala_id"] == tb["sala_id"]
                mesmo_docente = ta["professor_id"] is not None and ta["professor_id"] == tb["professor_id"]
                if not mesma_sala and not mesmo_docente:
                    continue

                for ha in ta["horarios"]:
                    for hb in tb["horarios"]:
                        if int(ha["dia_semana"]) != int(hb["dia_semana"]):
                            continue
                        ini_a = _para_minutos(str(ha["hora_inicio"]))
                        fim_a = _para_minutos(str(ha["hora_fim"]))
                        ini_b = _para_minutos(str(hb["hora_inicio"]))
                        fim_b = _para_minutos(str(hb["hora_fim"]))
                        # Sobreposição estrita: intervalos contíguos (fim_a == ini_b) não conflitam
                        if ini_a < fim_b and ini_b < fim_a:
                            intervalo = f"{_de_minutos(max(ini_a, ini_b))}-{_de_minutos(min(fim_a, fim_b))}"
                            if mesma_sala:
                                choques_sala += 1
                                conflitos.append(
                                    {
                                        "tipo_conflito": TipoConflitoEnum.CHOQUE_SALA,
                                        "dia_semana": int(ha["dia_semana"]),
                                        "intervalo_conflitante": intervalo,
                                        "recurso_id": int(ta["sala_id"]),
                                        "recurso_descricao": f"Sala {ta['codigo_sala']}",
                                        "turma_a_id": int(ta["id_turma"]),
                                        "turma_a_codigo": str(ta["codigo_turma"]),
                                        "turma_b_id": int(tb["id_turma"]),
                                        "turma_b_codigo": str(tb["codigo_turma"]),
                                    }
                                )
                            if mesmo_docente:
                                choques_docente += 1
                                conflitos.append(
                                    {
                                        "tipo_conflito": TipoConflitoEnum.CHOQUE_DOCENTE,
                                        "dia_semana": int(ha["dia_semana"]),
                                        "intervalo_conflitante": intervalo,
                                        "recurso_id": int(ta["professor_id"]),
                                        "recurso_descricao": str(ta["professor_nome"]),
                                        "turma_a_id": int(ta["id_turma"]),
                                        "turma_a_codigo": str(ta["codigo_turma"]),
                                        "turma_b_id": int(tb["id_turma"]),
                                        "turma_b_codigo": str(tb["codigo_turma"]),
                                    }
                                )

        turmas_com_pendencias: list[dict[str, Any]] = []
        for t in turmas_ativas:
            pend = [p for p in _calcular_pendencias_turma(t) if p in ("sem_professor", "sem_sala", "sem_horarios")]
            if pend:
                turmas_com_pendencias.append(
                    {
                        "id_turma": int(t["id_turma"]),
                        "codigo_turma": str(t["codigo_turma"]),
                        "disciplina_nome": str(t["disciplina_nome"]),
                        "pendencias": pend,
                    }
                )

        return {
            "periodo_letivo_id": periodo_letivo_id,
            "periodo_letivo_codigo": str(periodo["codigo"]),
            "curso_id": curso_id,
            "total_conflitos": len(conflitos),
            "total_choques_sala": choques_sala,
            "total_choques_docente": choques_docente,
            "conflitos": conflitos,
            "turmas_com_pendencias": turmas_com_pendencias,
        }

    # ------------------------------------------------------------------
    # US3: Requerimentos, Despachos Atômicos e Alocação do Corpo Docente
    # ------------------------------------------------------------------

    def listar_requerimentos(
        self,
        curso_id: Optional[int] = None,
        periodo_letivo_id: Optional[int] = None,
        tipo_requerimento: Optional[str] = None,
        aluno_matricula: Optional[int] = None,
        status_requerimento: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        self._validar_filtros(curso_id=curso_id, periodo_letivo_id=periodo_letivo_id)
        return self.repo.listar_requerimentos(
            curso_id=curso_id,
            periodo_letivo_id=periodo_letivo_id,
            tipo_requerimento=tipo_requerimento,
            aluno_matricula=aluno_matricula,
            status_requerimento=status_requerimento,
        )

    def obter_requerimento(self, id_requerimento: int) -> dict[str, Any]:
        req = self.repo.buscar_requerimento_por_id(id_requerimento)
        if req is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requerimento acadêmico não encontrado.",
            )
        return req

    def despachar_requerimento(
        self,
        id_requerimento: int,
        entrada: DespachoRequerimentoEntrada,
        operador: OperadorAutenticado,
        ip_origem: str,
    ) -> dict[str, Any]:
        req = self.repo.buscar_requerimento_por_id(id_requerimento)
        if req is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requerimento acadêmico não encontrado.",
            )

        status_atual = str(req["status_requerimento"])
        if status_atual in (StatusRequerimentoEnum.DEFERIDO.value, StatusRequerimentoEnum.INDEFERIDO.value):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Requerimento {req['protocolo']} já foi encerrado com status '{status_atual}'. "
                    f"Despachos encerrados são imutáveis."
                ),
            )

        atualizado_em = datetime.now(timezone.utc).isoformat()
        dados_ant = serializar_snapshot_auditoria(
            {
                "protocolo": req["protocolo"],
                "status_requerimento": status_atual,
                "parecer_secretaria": req["parecer_secretaria"],
            }
        )
        dados_nov = serializar_snapshot_auditoria(
            {
                "protocolo": req["protocolo"],
                "status_requerimento": entrada.novo_status.value,
                "parecer_secretaria": entrada.parecer,
                "atualizado_em": atualizado_em,
            }
        )
        assert dados_ant is not None and dados_nov is not None

        return self.repo.despachar_requerimento_atomico(
            id_requerimento=id_requerimento,
            protocolo=req["protocolo"],
            novo_status=entrada.novo_status.value,
            parecer=entrada.parecer,
            atualizado_em=atualizado_em,
            operador_usuario_id=operador.usuario_id,
            ip_origem=ip_origem,
            dados_anteriores_json=dados_ant,
            dados_novos_json=dados_nov,
        )

    def listar_alocacao_docentes(
        self,
        departamento: Optional[str] = None,
        curso_id: Optional[int] = None,
        periodo_letivo_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        self._validar_filtros(curso_id=curso_id, periodo_letivo_id=periodo_letivo_id)
        return self.repo.listar_alocacao_docentes(
            departamento=departamento,
            curso_id=curso_id,
            periodo_letivo_id=periodo_letivo_id,
        )

    # ------------------------------------------------------------------
    # US4: Auditoria LGPD
    # ------------------------------------------------------------------

    def listar_auditoria(self, id_registro_afetado: Optional[str] = None) -> list[dict[str, Any]]:
        return self.repo.listar_auditoria(id_registro_afetado=id_registro_afetado)
