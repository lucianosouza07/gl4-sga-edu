import uuid
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException

try:
    from schemas import (
        CertidaoResponse,
        DiscenteCreate,
        DiscenteResponse,
        InscricaoTurma,
        MovimentacaoResponse,
        RegraCurso,
        StatusDiscente,
        StatusTramitacao,
        TipoMovimentacao,
        TrancamentoRequest,
        DestrancamentoRequest,
        TransferenciaRequest,
        CancelamentoRequest,
        JubilamentoRequest,
    )
except ImportError:
    from .schemas import (
        CertidaoResponse,
        DiscenteCreate,
        DiscenteResponse,
        InscricaoTurma,
        MovimentacaoResponse,
        RegraCurso,
        StatusDiscente,
        StatusTramitacao,
        TipoMovimentacao,
        TrancamentoRequest,
        DestrancamentoRequest,
        TransferenciaRequest,
        CancelamentoRequest,
        JubilamentoRequest,
    )


class MovimentacaoAcademicaService:
    def __init__(self):
        self._discentes: Dict[str, DiscenteResponse] = {}
        self._regras_curso: Dict[str, RegraCurso] = {}
        self._movimentacoes: Dict[str, MovimentacaoResponse] = {}
        self._inscricoes_turmas: Dict[str, List[InscricaoTurma]] = {}
        self._seq_discente: int = 1
        self._seq_movimentacao: int = 1
        self._seq_inscricao: int = 1
        self._popular_regras_padrao()

    def _popular_regras_padrao(self):
        padroes = [
            RegraCurso(
                curso_id="CURSO_ENG_SOFT",
                nome_curso="Engenharia de Software",
                duracao_padrao_semestres=8,
                duracao_maxima_semestres=14,
                limite_semestres_trancamento=4,
                permite_trancamento_primeiro_semestre=False,
                vagas_transferencia_disponiveis=5,
            ),
            RegraCurso(
                curso_id="CURSO_CC",
                nome_curso="Ciência da Computação",
                duracao_padrao_semestres=8,
                duracao_maxima_semestres=14,
                limite_semestres_trancamento=4,
                permite_trancamento_primeiro_semestre=False,
                vagas_transferencia_disponiveis=3,
            ),
            RegraCurso(
                curso_id="CURSO_SI",
                nome_curso="Sistemas de Informação",
                duracao_padrao_semestres=8,
                duracao_maxima_semestres=12,
                limite_semestres_trancamento=4,
                permite_trancamento_primeiro_semestre=False,
                vagas_transferencia_disponiveis=0,
            ),
        ]
        for r in padroes:
            self._regras_curso[r.curso_id] = r

    def reset_database(self):
        self._discentes.clear()
        self._movimentacoes.clear()
        self._inscricoes_turmas.clear()
        self._seq_discente = 1
        self._seq_movimentacao = 1
        self._seq_inscricao = 1
        self._popular_regras_padrao()

    def cadastrar_regra_curso(self, regra: RegraCurso) -> RegraCurso:
        self._regras_curso[regra.curso_id] = regra
        return regra

    def obter_regra_curso(self, curso_id: str) -> RegraCurso:
        if curso_id in self._regras_curso:
            return self._regras_curso[curso_id]
        nova = RegraCurso(
            curso_id=curso_id,
            nome_curso=f"Curso {curso_id}",
            duracao_padrao_semestres=8,
            duracao_maxima_semestres=14,
            limite_semestres_trancamento=4,
            permite_trancamento_primeiro_semestre=False,
            vagas_transferencia_disponiveis=5,
        )
        self._regras_curso[curso_id] = nova
        return nova

    def criar_discente(self, dados: DiscenteCreate) -> DiscenteResponse:
        for d in self._discentes.values():
            if d.matricula == dados.matricula:
                raise HTTPException(status_code=400, detail=f"Já existe discente com matrícula {dados.matricula}.")
            if d.cpf == dados.cpf:
                raise HTTPException(status_code=400, detail=f"Já existe discente com CPF {dados.cpf}.")

        discente_id = f"DISC-{self._seq_discente:04d}"
        self._seq_discente += 1

        discente = DiscenteResponse(
            id=discente_id,
            matricula=dados.matricula,
            nome=dados.nome,
            cpf=dados.cpf,
            curso_id=dados.curso_id,
            nome_curso=dados.nome_curso,
            semestre_ingresso=dados.semestre_ingresso,
            status=StatusDiscente.ATIVO,
            semestres_cursados=dados.semestres_cursados,
            semestres_trancados=dados.semestres_trancados,
        )
        self._discentes[discente_id] = discente
        self.obter_regra_curso(dados.curso_id)
        return discente

    def listar_discentes(self) -> List[DiscenteResponse]:
        return list(self._discentes.values())

    def obter_discente(self, discente_id: str) -> DiscenteResponse:
        if discente_id not in self._discentes:
            raise HTTPException(status_code=404, detail=f"Discente {discente_id} não encontrado.")
        return self._discentes[discente_id]

    def matricular_em_turma(self, discente_id: str, turma_id: str, periodo_letivo: str) -> InscricaoTurma:
        self.obter_discente(discente_id)
        insc_id = f"INSC-{self._seq_inscricao:04d}"
        self._seq_inscricao += 1
        inscricao = InscricaoTurma(
            id=insc_id,
            discente_id=discente_id,
            turma_id=turma_id,
            periodo_letivo=periodo_letivo,
            status="ATIVA",
        )
        if discente_id not in self._inscricoes_turmas:
            self._inscricoes_turmas[discente_id] = []
        self._inscricoes_turmas[discente_id].append(inscricao)
        return inscricao

    def listar_inscricoes_turma(self, discente_id: str) -> List[InscricaoTurma]:
        return self._inscricoes_turmas.get(discente_id, [])

    def _desocupar_turmas_ativas(self, discente_id: str, periodo_letivo: str) -> int:
        canceladas = 0
        for insc in self._inscricoes_turmas.get(discente_id, []):
            if insc.periodo_letivo == periodo_letivo and insc.status == "ATIVA":
                insc.status = "CANCELADA_MOVIMENTACAO"
                canceladas += 1
        return canceladas

    def solicitar_trancamento(self, req: TrancamentoRequest) -> MovimentacaoResponse:
        discente = self.obter_discente(req.discente_id)

        if discente.status in (StatusDiscente.CANCELADO, StatusDiscente.JUBILADO):
            raise HTTPException(
                status_code=400,
                detail=f"Discente com vínculo {discente.status.value} não pode realizar trancamento de matrícula.",
            )

        if discente.status == StatusDiscente.TRANCADO:
            raise HTTPException(
                status_code=400,
                detail="Discente já se encontra com a matrícula com status TRANCADO.",
            )

        regra = self.obter_regra_curso(discente.curso_id)

        if (
            discente.semestres_cursados == 0
            and not regra.permite_trancamento_primeiro_semestre
            and not req.excecao_motivo_medico
        ):
            raise HTTPException(
                status_code=400,
                detail="Trancamento não autorizado para discentes no primeiro semestre sem comprovação médica ou exceção justificada.",
            )

        if discente.semestres_trancados + 1 > regra.limite_semestres_trancamento:
            raise HTTPException(
                status_code=400,
                detail=f"Limite máximo regulamentar de trancamento ({regra.limite_semestres_trancamento} semestres) excedido.",
            )

        status_anterior = discente.status
        discente.status = StatusDiscente.TRANCADO
        discente.semestres_trancados += 1

        self._desocupar_turmas_ativas(discente.id, req.periodo_letivo)

        mov_id = f"MOV-{self._seq_movimentacao:04d}"
        self._seq_movimentacao += 1
        agora = datetime.now()
        codigo_aut = f"CERT-TRANC-{uuid.uuid4().hex[:12].upper()}"

        movimentacao = MovimentacaoResponse(
            id=mov_id,
            discente_id=discente.id,
            tipo=TipoMovimentacao.TRANCAMENTO,
            status_tramitacao=StatusTramitacao.HOMOLOGADO,
            status_anterior=status_anterior,
            status_novo=StatusDiscente.TRANCADO,
            periodo_letivo=req.periodo_letivo,
            data_solicitacao=agora,
            data_homologacao=agora,
            justificativa=req.justificativa,
            parecer="Trancamento total homologado com liberação de vagas em turmas e suspensão de vínculo temporária.",
            operador_id=req.operador_id,
            codigo_autenticidade=codigo_aut,
        )
        self._movimentacoes[mov_id] = movimentacao
        return movimentacao

    def homologar_destrancamento(self, req: DestrancamentoRequest) -> MovimentacaoResponse:
        discente = self.obter_discente(req.discente_id)

        if discente.status != StatusDiscente.TRANCADO:
            raise HTTPException(
                status_code=400,
                detail=f"Destrancamento só é aplicável a discentes com matrícula TRANCADO. Status atual: {discente.status.value}.",
            )

        status_anterior = discente.status
        discente.status = StatusDiscente.ATIVO

        mov_id = f"MOV-{self._seq_movimentacao:04d}"
        self._seq_movimentacao += 1
        agora = datetime.now()
        codigo_aut = f"CERT-DEST-{uuid.uuid4().hex[:12].upper()}"

        movimentacao = MovimentacaoResponse(
            id=mov_id,
            discente_id=discente.id,
            tipo=TipoMovimentacao.DESTRANCAMENTO,
            status_tramitacao=StatusTramitacao.HOMOLOGADO,
            status_anterior=status_anterior,
            status_novo=StatusDiscente.ATIVO,
            periodo_letivo=req.periodo_letivo,
            data_solicitacao=agora,
            data_homologacao=agora,
            justificativa=req.justificativa,
            parecer="Destrancamento de matrícula homologado. Vínculo discente restabelecido para status ATIVO.",
            operador_id=req.operador_id,
            codigo_autenticidade=codigo_aut,
        )
        self._movimentacoes[mov_id] = movimentacao
        return movimentacao

    def homologar_transferencia(self, req: TransferenciaRequest) -> MovimentacaoResponse:
        discente = self.obter_discente(req.discente_id)

        if discente.status in (StatusDiscente.CANCELADO, StatusDiscente.JUBILADO):
            raise HTTPException(
                status_code=400,
                detail=f"Discente com vínculo {discente.status.value} não pode realizar transferência.",
            )

        status_anterior = discente.status
        curso_origem = discente.curso_id
        curso_destino = req.curso_destino_id
        inst_externa = req.instituicao_destino

        if req.tipo_transferencia == TipoMovimentacao.TRANSFERENCIA_INTERNA:
            if not req.curso_destino_id:
                raise HTTPException(status_code=400, detail="É obrigatório informar curso_destino_id para transferência interna.")
            if req.curso_destino_id == discente.curso_id:
                raise HTTPException(status_code=400, detail="O curso de destino não pode ser idêntico ao curso de origem atual.")

            regra_dest = self.obter_regra_curso(req.curso_destino_id)
            if regra_dest.vagas_transferencia_disponiveis <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Não há vagas disponíveis para transferência interna no curso {req.curso_destino_id}.",
                )

            regra_dest.vagas_transferencia_disponiveis -= 1
            discente.curso_id = req.curso_destino_id
            if req.nome_curso_destino:
                discente.nome_curso = req.nome_curso_destino
            discente.status = StatusDiscente.TRANSFERIDO
        else:
            if not req.instituicao_destino:
                raise HTTPException(status_code=400, detail="É obrigatório informar instituicao_destino para transferência externa de saída.")
            discente.status = StatusDiscente.TRANSFERIDO

        self._desocupar_turmas_ativas(discente.id, req.periodo_letivo)

        mov_id = f"MOV-{self._seq_movimentacao:04d}"
        self._seq_movimentacao += 1
        agora = datetime.now()
        codigo_aut = f"CERT-TRANSF-{uuid.uuid4().hex[:12].upper()}"

        movimentacao = MovimentacaoResponse(
            id=mov_id,
            discente_id=discente.id,
            tipo=req.tipo_transferencia,
            status_tramitacao=StatusTramitacao.HOMOLOGADO,
            status_anterior=status_anterior,
            status_novo=StatusDiscente.TRANSFERIDO,
            periodo_letivo=req.periodo_letivo,
            data_solicitacao=agora,
            data_homologacao=agora,
            justificativa=req.justificativa,
            parecer="Transferência acadêmica homologada com atualização de vínculo e liberação de vagas.",
            operador_id=req.operador_id,
            curso_origem_id=curso_origem,
            curso_destino_id=curso_destino,
            instituicao_externa=inst_externa,
            codigo_autenticidade=codigo_aut,
        )
        self._movimentacoes[mov_id] = movimentacao
        return movimentacao

    def homologar_cancelamento(self, req: CancelamentoRequest) -> MovimentacaoResponse:
        discente = self.obter_discente(req.discente_id)

        if discente.status in (StatusDiscente.CANCELADO, StatusDiscente.JUBILADO):
            raise HTTPException(
                status_code=400,
                detail=f"Discente já possui vínculo encerrado definitivamente com status {discente.status.value}.",
            )

        status_anterior = discente.status
        discente.status = StatusDiscente.CANCELADO

        self._desocupar_turmas_ativas(discente.id, req.periodo_letivo)

        mov_id = f"MOV-{self._seq_movimentacao:04d}"
        self._seq_movimentacao += 1
        agora = datetime.now()
        codigo_aut = f"CERT-CANC-{uuid.uuid4().hex[:12].upper()}"

        movimentacao = MovimentacaoResponse(
            id=mov_id,
            discente_id=discente.id,
            tipo=req.tipo_cancelamento,
            status_tramitacao=StatusTramitacao.HOMOLOGADO,
            status_anterior=status_anterior,
            status_novo=StatusDiscente.CANCELADO,
            periodo_letivo=req.periodo_letivo,
            data_solicitacao=agora,
            data_homologacao=agora,
            justificativa=req.justificativa,
            parecer=f"Cancelamento definitivo de matrícula ({req.tipo_cancelamento.value}) homologado com desligamento institucional.",
            operador_id=req.operador_id,
            codigo_autenticidade=codigo_aut,
        )
        self._movimentacoes[mov_id] = movimentacao
        return movimentacao

    def homologar_jubilamento(self, req: JubilamentoRequest) -> MovimentacaoResponse:
        discente = self.obter_discente(req.discente_id)

        if discente.status in (StatusDiscente.CANCELADO, StatusDiscente.JUBILADO):
            raise HTTPException(
                status_code=400,
                detail=f"Discente já possui vínculo encerrado definitivamente com status {discente.status.value}.",
            )

        regra = self.obter_regra_curso(discente.curso_id)
        total_decorrido = discente.semestres_cursados + discente.semestres_trancados

        if total_decorrido < regra.duracao_maxima_semestres:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Discente não atingiu o prazo máximo regulamentar de integralização do curso "
                    f"({regra.duracao_maxima_semestres} semestres). Total decorrido: {total_decorrido} semestres."
                ),
            )

        status_anterior = discente.status
        discente.status = StatusDiscente.JUBILADO

        self._desocupar_turmas_ativas(discente.id, req.periodo_letivo)

        mov_id = f"MOV-{self._seq_movimentacao:04d}"
        self._seq_movimentacao += 1
        agora = datetime.now()
        codigo_aut = f"CERT-JUB-{uuid.uuid4().hex[:12].upper()}"

        movimentacao = MovimentacaoResponse(
            id=mov_id,
            discente_id=discente.id,
            tipo=TipoMovimentacao.JUBILAMENTO,
            status_tramitacao=StatusTramitacao.HOMOLOGADO,
            status_anterior=status_anterior,
            status_novo=StatusDiscente.JUBILADO,
            periodo_letivo=req.periodo_letivo,
            data_solicitacao=agora,
            data_homologacao=agora,
            justificativa=req.justificativa,
            parecer=(
                f"Jubilamento compulsório homologado por expiração do prazo máximo de integralização curricular "
                f"({total_decorrido} semestres decorridos / limite de {regra.duracao_maxima_semestres} semestres)."
            ),
            operador_id=req.operador_id,
            codigo_autenticidade=codigo_aut,
        )
        self._movimentacoes[mov_id] = movimentacao
        return movimentacao

    def listar_historico_discente(self, discente_id: str) -> List[MovimentacaoResponse]:
        self.obter_discente(discente_id)
        historico = [m for m in self._movimentacoes.values() if m.discente_id == discente_id]
        historico.sort(key=lambda x: x.data_solicitacao)
        return historico

    def emitir_certidao(self, movimentacao_id: str) -> CertidaoResponse:
        if movimentacao_id not in self._movimentacoes:
            raise HTTPException(status_code=404, detail=f"Movimentação {movimentacao_id} não encontrada.")

        mov = self._movimentacoes[movimentacao_id]
        discente = self._discentes[mov.discente_id]
        agora = datetime.now()

        texto = (
            f"CERTIFICAMOS, para os devidos fins de direito e instrução acadêmica, que o(a) discente "
            f"{discente.nome.upper()}, portador(a) do CPF nº {discente.cpf} e matrícula institucional nº {discente.matricula}, "
            f"regularmente vinculado(a) ao curso de {discente.nome_curso}, teve o ato formal de {mov.tipo.value} devidamente "
            f"HOMOLOGADO pela Secretaria Acadêmica no período letivo {mov.periodo_letivo}, resultando na situação cadastral "
            f"{mov.status_novo.value}. Processo registrado sob código de validação institucional {mov.codigo_autenticidade}."
        )

        return CertidaoResponse(
            codigo_autenticidade=mov.codigo_autenticidade,
            data_emissao=agora,
            nome_discente=discente.nome,
            matricula=discente.matricula,
            curso=discente.nome_curso,
            tipo_movimentacao=mov.tipo.value,
            periodo_letivo=mov.periodo_letivo,
            status_resultante=mov.status_novo.value,
            texto_certidao=texto,
        )


servico_movimentacao = MovimentacaoAcademicaService()
