"""Regras de negócio para validação de aproveitamento de estudos e equivalências (SGA-26)."""

from datetime import datetime, timezone
import json
from typing import Any, Optional
from fastapi import HTTPException, status

HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

try:
    from .audit_service import serializar_snapshot_auditoria
    from .repository import AproveitamentoRepository
    from .schemas import (
        DecisaoDeliberacaoEnum,
        DeliberacaoAproveitamentoEntrada,
        EquivalenciaAtualizacao,
        EquivalenciaEntrada,
        ModalidadeAproveitamentoEnum,
        NOTA_MINIMA_APROVACAO,
        OrigemAtendimentoPreRequisitoEnum,
        PERCENTUAL_MINIMO_CARGA_HORARIA,
        SolicitacaoAproveitamentoEntrada,
        StatusSolicitacaoEnum,
    )
    from .security import OperadorAutenticado
except ImportError:
    from audit_service import serializar_snapshot_auditoria
    from repository import AproveitamentoRepository
    from schemas import (
        DecisaoDeliberacaoEnum,
        DeliberacaoAproveitamentoEntrada,
        EquivalenciaAtualizacao,
        EquivalenciaEntrada,
        ModalidadeAproveitamentoEnum,
        NOTA_MINIMA_APROVACAO,
        OrigemAtendimentoPreRequisitoEnum,
        PERCENTUAL_MINIMO_CARGA_HORARIA,
        SolicitacaoAproveitamentoEntrada,
        StatusSolicitacaoEnum,
    )
    from security import OperadorAutenticado


class AproveitamentoService:
    """Orquestrador das regras de equivalência, pré-validação, deliberação e dispensas."""

    def __init__(self, repo: AproveitamentoRepository) -> None:
        self.repo = repo

    # ------------------------------------------------------------------
    # US1: Gestão de Equivalências
    # ------------------------------------------------------------------

    def criar_equivalencia(
        self,
        entrada: EquivalenciaEntrada,
        operador: OperadorAutenticado,
        ip_origem: str,
    ) -> dict[str, Any]:
        if entrada.disciplina_origem_id == entrada.disciplina_equivalente_id:
            raise HTTPException(
                status_code=HTTP_422,
                detail="Uma disciplina não pode ser cadastrada como equivalente a si mesma.",
            )

        origem = self.repo.buscar_disciplina_por_id(entrada.disciplina_origem_id)
        if origem is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disciplina de origem não encontrada.",
            )

        equivalente = self.repo.buscar_disciplina_por_id(entrada.disciplina_equivalente_id)
        if equivalente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disciplina equivalente não encontrada.",
            )

        existente = self.repo.buscar_equivalencia_por_par(
            entrada.disciplina_origem_id, entrada.disciplina_equivalente_id
        )
        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma regra de equivalência cadastrada para este par de disciplinas.",
            )

        snapshot_novo = serializar_snapshot_auditoria(
            {
                "disciplina_origem_id": entrada.disciplina_origem_id,
                "disciplina_equivalente_id": entrada.disciplina_equivalente_id,
                "portaria_aprovacao": entrada.portaria_aprovacao,
                "ativa": True,
            }
        )
        assert snapshot_novo is not None

        return self.repo.criar_equivalencia_com_auditoria(
            disciplina_origem_id=entrada.disciplina_origem_id,
            disciplina_equivalente_id=entrada.disciplina_equivalente_id,
            portaria_aprovacao=entrada.portaria_aprovacao,
            operador_usuario_id=operador.usuario_id,
            ip_origem=ip_origem,
            dados_novos_json=snapshot_novo,
        )

    def listar_equivalencias(
        self,
        disciplina_origem_id: Optional[int] = None,
        disciplina_equivalente_id: Optional[int] = None,
        ativa: Optional[bool] = None,
    ) -> list[dict[str, Any]]:
        return self.repo.listar_equivalencias(
            disciplina_origem_id=disciplina_origem_id,
            disciplina_equivalente_id=disciplina_equivalente_id,
            ativa=ativa,
        )

    def obter_equivalencia(self, id_equivalencia: int) -> dict[str, Any]:
        eq = self.repo.buscar_equivalencia_por_id(id_equivalencia)
        if eq is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Regra de equivalência não encontrada.",
            )
        return eq

    def atualizar_equivalencia(
        self,
        id_equivalencia: int,
        entrada: EquivalenciaAtualizacao,
        operador: OperadorAutenticado,
        ip_origem: str,
    ) -> dict[str, Any]:
        atual = self.repo.buscar_equivalencia_por_id(id_equivalencia)
        if atual is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Regra de equivalência não encontrada.",
            )

        nova_portaria = (
            entrada.portaria_aprovacao
            if entrada.portaria_aprovacao is not None
            else atual["portaria_aprovacao"]
        )
        nova_ativa = entrada.ativa if entrada.ativa is not None else atual["ativa"]

        dados_ant = serializar_snapshot_auditoria(
            {
                "portaria_aprovacao": atual["portaria_aprovacao"],
                "ativa": atual["ativa"],
            }
        )
        dados_nov = serializar_snapshot_auditoria(
            {
                "portaria_aprovacao": nova_portaria,
                "ativa": nova_ativa,
            }
        )
        assert dados_ant is not None and dados_nov is not None

        return self.repo.atualizar_equivalencia_com_auditoria(
            id_equivalencia=id_equivalencia,
            portaria_aprovacao=nova_portaria,
            ativa=nova_ativa,
            operador_usuario_id=operador.usuario_id,
            ip_origem=ip_origem,
            dados_anteriores_json=dados_ant,
            dados_novos_json=dados_nov,
        )

    # ------------------------------------------------------------------
    # US2: Motor de Pré-Validação e Protocolos de Aproveitamento
    # ------------------------------------------------------------------

    def _avaliar_elegibilidade(
        self,
        aluno_matricula: int,
        disciplina_alvo: dict[str, Any],
        modalidade: str,
        carga_horaria_cursada: int,
        nota_obtida: float,
        disciplina_origem_id: Optional[int] = None,
    ) -> tuple[dict[str, Any], Optional[int]]:
        """Executa pré-validação objetiva de nota, carga horária e regras de equivalência."""
        ch_alvo = int(disciplina_alvo["carga_horaria"])
        percentual_ch = round((carga_horaria_cursada / ch_alvo) * 100.0, 2) if ch_alvo > 0 else 0.0
        ch_compativel = percentual_ch >= PERCENTUAL_MINIMO_CARGA_HORARIA
        nota_aprovada = nota_obtida >= NOTA_MINIMA_APROVACAO

        pendencias: list[str] = []
        equivalencia_ativa: Optional[bool] = None
        aprovacao_interna: Optional[bool] = None
        equivalencia_id: Optional[int] = None

        if modalidade == ModalidadeAproveitamentoEnum.EQUIVALENCIA_INTERNA.value:
            assert disciplina_origem_id is not None
            eq = self.repo.buscar_equivalencia_por_par(
                disciplina_origem_id, int(disciplina_alvo["id_disciplina"])
            )
            if eq is not None:
                equivalencia_id = int(eq["id_equivalencia"])
                equivalencia_ativa = bool(eq["ativa"])
                if not equivalencia_ativa:
                    pendencias.append(
                        "A regra de equivalência interna entre a disciplina de origem e a disciplina alvo está inativa."
                    )
            else:
                equivalencia_ativa = False
                pendencias.append(
                    "Não existe regra de equivalência interna cadastrada ligando a disciplina de origem à disciplina alvo."
                )

            aprov = self.repo.buscar_aprovacao_interna_em_disciplina(aluno_matricula, disciplina_origem_id)
            if aprov is not None and aprov["media_final"] is not None and float(aprov["media_final"]) >= NOTA_MINIMA_APROVACAO:
                aprovacao_interna = True
            else:
                aprovacao_interna = False
                pendencias.append(
                    "Não há comprovação de aprovação interna do estudante na disciplina de origem com média mínima de 6.00."
                )

        if not nota_aprovada:
            pendencias.append(
                f"Nota obtida ({nota_obtida:.2f}) é inferior à nota mínima institucional de aprovação ({NOTA_MINIMA_APROVACAO:.2f})."
            )

        if not ch_compativel:
            pendencias.append(
                f"Carga horária cursada ({carga_horaria_cursada}h, equivalente a {percentual_ch:.2f}% de {ch_alvo}h) "
                f"é inferior ao mínimo exigido de {PERCENTUAL_MINIMO_CARGA_HORARIA:.0f}%."
            )

        diagnostico = {
            "elegivel": len(pendencias) == 0,
            "nota_aprovada": nota_aprovada,
            "carga_horaria_compativel": ch_compativel,
            "percentual_carga_horaria": percentual_ch,
            "equivalencia_ativa_encontrada": equivalencia_ativa,
            "aprovacao_interna_comprovada": aprovacao_interna,
            "pendencias": pendencias,
        }
        return diagnostico, equivalencia_id

    def abrir_solicitacao(
        self,
        entrada: SolicitacaoAproveitamentoEntrada,
        operador: OperadorAutenticado,
        ip_origem: str,
    ) -> dict[str, Any]:
        aluno = self.repo.buscar_aluno_por_matricula(entrada.aluno_matricula)
        if aluno is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado.",
            )

        status_acad = str(aluno["status_academico"])
        if status_acad != "ATIVO":
            raise HTTPException(
                status_code=HTTP_422,
                detail=(
                    f"Estudante inelegível para protocolar aproveitamento: situação acadêmica atual é "
                    f"'{status_acad}' (exigido 'ATIVO')."
                ),
            )

        disciplina_alvo = self.repo.buscar_disciplina_por_id(entrada.disciplina_alvo_id)
        if disciplina_alvo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disciplina alvo não encontrada.",
            )

        if self.repo.buscar_aprovacao_interna_em_disciplina(entrada.aluno_matricula, entrada.disciplina_alvo_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="O estudante já possui aprovação registrada na disciplina alvo.",
            )

        if self.repo.buscar_dispensa_por_aluno_e_disciplina(entrada.aluno_matricula, entrada.disciplina_alvo_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="O estudante já possui dispensa deferida para a disciplina alvo.",
            )

        pendente = self.repo.buscar_solicitacao_em_analise(entrada.aluno_matricula, entrada.disciplina_alvo_id)
        if pendente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Já existe um protocolo em análise ({pendente['protocolo']}) para este estudante "
                    f"e disciplina alvo."
                ),
            )

        if entrada.modalidade == ModalidadeAproveitamentoEnum.EQUIVALENCIA_INTERNA:
            assert entrada.disciplina_origem_id is not None
            disciplina_origem = self.repo.buscar_disciplina_por_id(entrada.disciplina_origem_id)
            if disciplina_origem is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Disciplina de origem não encontrada.",
                )
            carga_horaria_cursada = int(disciplina_origem["carga_horaria"])
            aprov_origem = self.repo.buscar_aprovacao_interna_em_disciplina(
                entrada.aluno_matricula, entrada.disciplina_origem_id
            )
            nota_obtida = (
                round(float(aprov_origem["media_final"]), 2)
                if aprov_origem is not None and aprov_origem["media_final"] is not None
                else 0.0
            )
            ementa = disciplina_origem.get("ementa") or entrada.ementa_resumo
            instituicao_origem = None
            disciplina_externa_nome = None
        else:
            assert entrada.carga_horaria_cursada is not None and entrada.nota_obtida is not None
            carga_horaria_cursada = int(entrada.carga_horaria_cursada)
            nota_obtida = round(float(entrada.nota_obtida), 2)
            ementa = entrada.ementa_resumo
            instituicao_origem = entrada.instituicao_origem
            disciplina_externa_nome = entrada.disciplina_externa_nome

        diagnostico, equivalencia_id = self._avaliar_elegibilidade(
            aluno_matricula=entrada.aluno_matricula,
            disciplina_alvo=disciplina_alvo,
            modalidade=entrada.modalidade.value,
            carga_horaria_cursada=carga_horaria_cursada,
            nota_obtida=nota_obtida,
            disciplina_origem_id=entrada.disciplina_origem_id,
        )

        aberto_em = datetime.now(timezone.utc).isoformat()
        protocolo = self.repo.gerar_numero_protocolo()
        diag_json = json.dumps(diagnostico, ensure_ascii=False, sort_keys=True)
        snapshot_novo = serializar_snapshot_auditoria(
            {
                "protocolo": protocolo,
                "aluno_matricula": entrada.aluno_matricula,
                "disciplina_alvo_id": entrada.disciplina_alvo_id,
                "modalidade": entrada.modalidade.value,
                "disciplina_origem_id": entrada.disciplina_origem_id,
                "equivalencia_id": equivalencia_id,
                "carga_horaria_cursada": carga_horaria_cursada,
                "nota_obtida": nota_obtida,
                "pre_validacao_elegivel": diagnostico["elegivel"],
                "status_solicitacao": StatusSolicitacaoEnum.EM_ANALISE.value,
            }
        )
        assert snapshot_novo is not None

        return self.repo.criar_solicitacao_com_auditoria(
            protocolo=protocolo,
            aluno_matricula=entrada.aluno_matricula,
            disciplina_alvo_id=entrada.disciplina_alvo_id,
            modalidade=entrada.modalidade.value,
            disciplina_origem_id=entrada.disciplina_origem_id,
            equivalencia_id=equivalencia_id,
            instituicao_origem=instituicao_origem,
            disciplina_externa_nome=disciplina_externa_nome,
            carga_horaria_cursada=carga_horaria_cursada,
            nota_obtida=nota_obtida,
            ementa_resumo=ementa,
            documentacao_comprobatoria=entrada.documentacao_comprobatoria,
            pre_validacao_elegivel=bool(diagnostico["elegivel"]),
            pre_validacao_detalhes_json=diag_json,
            aberto_por_usuario_id=operador.usuario_id,
            aberto_em=aberto_em,
            ip_origem=ip_origem,
            dados_novos_auditoria_json=snapshot_novo,
        )

    def listar_solicitacoes(
        self,
        aluno_matricula: Optional[int] = None,
        disciplina_alvo_id: Optional[int] = None,
        modalidade: Optional[str] = None,
        status_solicitacao: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        return self.repo.listar_solicitacoes(
            aluno_matricula=aluno_matricula,
            disciplina_alvo_id=disciplina_alvo_id,
            modalidade=modalidade,
            status_solicitacao=status_solicitacao,
        )

    def obter_solicitacao(self, id_solicitacao: int) -> dict[str, Any]:
        sol = self.repo.buscar_solicitacao_por_id(id_solicitacao)
        if sol is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitação de aproveitamento não encontrada.",
            )
        return sol

    # ------------------------------------------------------------------
    # US3: Deliberação Formal, Dispensas e Pré-Requisitos
    # ------------------------------------------------------------------

    def deliberar_solicitacao(
        self,
        id_solicitacao: int,
        entrada: DeliberacaoAproveitamentoEntrada,
        operador: OperadorAutenticado,
        ip_origem: str,
    ) -> dict[str, Any]:
        sol = self.repo.buscar_solicitacao_por_id(id_solicitacao)
        if sol is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitação de aproveitamento não encontrada.",
            )

        if sol["status_solicitacao"] != StatusSolicitacaoEnum.EM_ANALISE.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Solicitação {sol['protocolo']} já foi encerrada com status "
                    f"'{sol['status_solicitacao']}'. Deliberações concluídas são imutáveis."
                ),
            )

        criar_dispensa = entrada.decisao == DecisaoDeliberacaoEnum.DEFERIDO
        if criar_dispensa:
            if self.repo.buscar_dispensa_por_aluno_e_disciplina(
                sol["aluno_matricula"], sol["disciplina_alvo_id"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="O estudante já possui dispensa consolidada para esta disciplina.",
                )
            if self.repo.buscar_aprovacao_interna_em_disciplina(
                sol["aluno_matricula"], sol["disciplina_alvo_id"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="O estudante já possui aprovação cursada para esta disciplina.",
                )

            disciplina_alvo = self.repo.buscar_disciplina_por_id(sol["disciplina_alvo_id"])
            assert disciplina_alvo is not None
            diagnostico_atual, _ = self._avaliar_elegibilidade(
                aluno_matricula=sol["aluno_matricula"],
                disciplina_alvo=disciplina_alvo,
                modalidade=sol["modalidade"],
                carga_horaria_cursada=sol["carga_horaria_cursada"],
                nota_obtida=sol["nota_obtida"],
                disciplina_origem_id=sol["disciplina_origem_id"],
            )
            if not diagnostico_atual["elegivel"]:
                motivos = "; ".join(diagnostico_atual["pendencias"])
                raise HTTPException(
                    status_code=HTTP_422,
                    detail=f"Não é possível deferir solicitação inelegível: {motivos}",
                )

        deliberado_em = datetime.now(timezone.utc).isoformat()
        dados_ant_sol = serializar_snapshot_auditoria(
            {
                "protocolo": sol["protocolo"],
                "status_solicitacao": sol["status_solicitacao"],
                "parecer_tecnico": sol["parecer_tecnico"],
            }
        )
        dados_nov_sol = serializar_snapshot_auditoria(
            {
                "protocolo": sol["protocolo"],
                "status_solicitacao": entrada.decisao.value,
                "parecer_tecnico": entrada.parecer_tecnico,
                "deliberado_em": deliberado_em,
            }
        )
        dados_nov_dispensa = (
            serializar_snapshot_auditoria(
                {
                    "aluno_matricula": sol["aluno_matricula"],
                    "disciplina_id": sol["disciplina_alvo_id"],
                    "solicitacao_id": id_solicitacao,
                    "modalidade": sol["modalidade"],
                    "nota_aproveitada": sol["nota_obtida"],
                    "carga_horaria_aproveitada": sol["disciplina_alvo_carga_horaria"],
                }
            )
            if criar_dispensa
            else None
        )
        assert dados_ant_sol is not None and dados_nov_sol is not None

        sol_atualizada, dispensa = self.repo.deliberar_solicitacao_atomico(
            id_solicitacao=id_solicitacao,
            decisao=entrada.decisao.value,
            parecer_tecnico=entrada.parecer_tecnico,
            deliberado_por_usuario_id=operador.usuario_id,
            deliberado_em=deliberado_em,
            ip_origem=ip_origem,
            dados_anteriores_sol_json=dados_ant_sol,
            dados_novos_sol_json=dados_nov_sol,
            criar_dispensa=criar_dispensa,
            aluno_matricula=sol["aluno_matricula"],
            disciplina_id=sol["disciplina_alvo_id"],
            modalidade=sol["modalidade"],
            nota_aproveitada=sol["nota_obtida"],
            carga_horaria_aproveitada=sol["disciplina_alvo_carga_horaria"],
            dados_novos_dispensa_json=dados_nov_dispensa,
        )
        return {"solicitacao": sol_atualizada, "dispensa": dispensa}

    def listar_dispensas_aluno(self, aluno_matricula: int) -> dict[str, Any]:
        aluno = self.repo.buscar_aluno_por_matricula(aluno_matricula)
        if aluno is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado.",
            )
        dispensas = self.repo.listar_dispensas_por_aluno(aluno_matricula)
        ch_total = sum(int(d["carga_horaria_aproveitada"]) for d in dispensas)
        return {
            "aluno_matricula": aluno_matricula,
            "aluno_nome": str(aluno["nome"] or ""),
            "total_disciplinas_dispensadas": len(dispensas),
            "carga_horaria_total_aproveitada": ch_total,
            "dispensas": dispensas,
        }

    def verificar_pre_requisitos_aluno(
        self, aluno_matricula: int, disciplina_id: int
    ) -> dict[str, Any]:
        aluno = self.repo.buscar_aluno_por_matricula(aluno_matricula)
        if aluno is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado.",
            )
        disciplina = self.repo.buscar_disciplina_por_id(disciplina_id)
        if disciplina is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disciplina não encontrada.",
            )

        pre_reqs = self.repo.listar_pre_requisitos_da_disciplina(disciplina_id)
        itens: list[dict[str, Any]] = []
        for req in pre_reqs:
            req_id = int(req["requisito_disciplina_id"])
            if self.repo.buscar_aprovacao_interna_em_disciplina(aluno_matricula, req_id):
                atendido = True
                origem = OrigemAtendimentoPreRequisitoEnum.APROVADO_TURMA
            elif self.repo.buscar_dispensa_por_aluno_e_disciplina(aluno_matricula, req_id):
                atendido = True
                origem = OrigemAtendimentoPreRequisitoEnum.DISPENSA_APROVEITAMENTO
            else:
                atendido = False
                origem = OrigemAtendimentoPreRequisitoEnum.PENDENTE

            itens.append(
                {
                    "requisito_disciplina_id": req_id,
                    "codigo": str(req["codigo"]),
                    "nome": str(req["nome"]),
                    "atendido": atendido,
                    "origem_atendimento": origem,
                }
            )

        return {
            "aluno_matricula": aluno_matricula,
            "disciplina_id": disciplina_id,
            "disciplina_codigo": str(disciplina["codigo"]),
            "disciplina_nome": str(disciplina["nome"]),
            "apto_para_matricula": all(item["atendido"] for item in itens),
            "requisitos": itens,
        }

    # ------------------------------------------------------------------
    # US4: Auditoria LGPD
    # ------------------------------------------------------------------

    def listar_auditoria(
        self,
        entidade_afetada: Optional[str] = None,
        id_registro_afetado: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        return self.repo.listar_auditoria(
            entidade_afetada=entidade_afetada,
            id_registro_afetado=id_registro_afetado,
        )
