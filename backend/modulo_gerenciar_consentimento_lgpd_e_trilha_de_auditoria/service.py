"""Regras de negócio de consentimento LGPD e integração com trilha de auditoria."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

from .audit_service import AuditService
from .models import TipoAcaoAuditoria
from .repository import LgpdAuditRepository
from .schemas import (
    AceiteConsentimentoRequest,
    AceiteConsentimentoResponse,
    ConsentimentoItemResponse,
    ConsentimentoStatusResponse,
    FinalidadeItem,
    RevogacaoConsentimentoRequest,
    RevogacaoConsentimentoResponse,
    TermoVigenteResponse,
)

# Catálogo oficial de termos e finalidades do SGA-Edu
TERMO_VIGENTE_PADRAO = TermoVigenteResponse(
    versao="v1.0",
    data_publicacao="2026-11-20T00:00:00Z",
    titulo="Termo de Consentimento e Política de Privacidade SGA-Edu",
    conteudo=(
        "O presente termo regula o tratamento de dados pessoais de estudantes, docentes "
        "e servidores técnico-administrativos da instituição de ensino superior no âmbito do SGA-Edu, "
        "em conformidade com a Lei nº 13.709/2018 (LGPD) e as Portarias MEC nº 315/2018 e 360/2022."
    ),
    finalidades=[
        FinalidadeItem(
            codigo="TRATAMENTO_ACADEMICO",
            titulo="Gestão Acadêmica, Matrículas e Histórico Escolar",
            descricao="Tratamento essencial de dados pessoais para registro pedagógico, frequência, notas e emissão de diplomas.",
            obrigatoria=True,
        ),
        FinalidadeItem(
            codigo="COMUNICACAO_INSTITUCIONAL",
            titulo="Notificações Institucionais e Avisos por E-mail/SMS",
            descricao="Envio de comunicados pedagógicos, lembretes de prazos e informativos da instituição.",
            obrigatoria=False,
        ),
        FinalidadeItem(
            codigo="SERVICOS_BIBLIOTECA_VIRTUAL",
            titulo="Acesso a Acervos e Bibliotecas Digitais Parceiras",
            descricao="Compartilhamento controlado com plataformas conveniadas de livros e periódicos digitais.",
            obrigatoria=False,
        ),
    ],
)


class ConsentimentoService:
    """Orquestra o ciclo de vida dos termos de consentimento e integrações de auditoria."""

    def __init__(self, repository: LgpdAuditRepository, audit_service: AuditService):
        self.repository = repository
        self.audit_service = audit_service
        self._termo_vigente = TERMO_VIGENTE_PADRAO

    def obter_termo_vigente(self) -> TermoVigenteResponse:
        return self._termo_vigente

    def consultar_status_usuario(self, usuario_id: int) -> ConsentimentoStatusResponse:
        termo = self._termo_vigente
        ativos = self.repository.buscar_consentimentos_ativos(usuario_id, termo.versao)
        codigos_ativos = {item["finalidade"] for item in ativos}

        obrigatorias = {f.codigo for f in termo.finalidades if f.obrigatoria}
        possui_obrigatorias = obrigatorias.issubset(codigos_ativos)

        # Checa se possui consentimentos em versões mais antigas
        todos = self.repository.listar_historico_consentimentos(usuario_id)
        versoes_anteriores = {item["versao_termo"] for item in todos if item["versao_termo"] != termo.versao}
        pendente_nova_versao = bool(versoes_anteriores and not possui_obrigatorias)

        return ConsentimentoStatusResponse(
            usuario_id=usuario_id,
            versao_vigente=termo.versao,
            possui_aceite_vigente=possui_obrigatorias,
            pendente_nova_versao=pendente_nova_versao,
            consentimentos_ativos=sorted(list(codigos_ativos)),
        )

    def aceitar_consentimento(
        self,
        usuario_id: int,
        request: AceiteConsentimentoRequest,
        ip_origem: str,
    ) -> AceiteConsentimentoResponse:
        termo = self._termo_vigente
        if request.versao_termo != termo.versao:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Versão do termo inválida. A versão vigente é '{termo.versao}'.",
            )

        finalidades_validas = {f.codigo for f in termo.finalidades}
        finalidades_obrigatorias = {f.codigo for f in termo.finalidades if f.obrigatoria}

        solicitadas = set(request.finalidades)
        if not solicitadas.issubset(finalidades_validas):
            finalidades_invalidas = solicitadas - finalidades_validas
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Finalidades desconhecidas: {', '.join(sorted(finalidades_invalidas))}",
            )

        # O aceite deve incluir obrigatoriamente as finalidades essenciais
        if not finalidades_obrigatorias.issubset(solicitadas):
            faltantes = finalidades_obrigatorias - solicitadas
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"As seguintes finalidades obrigatórias não foram aceitas: {', '.join(sorted(faltantes))}",
            )

        agora = datetime.now(timezone.utc)
        total_gravados = 0

        for finalidade_codigo in request.finalidades:
            self.repository.registrar_consentimento(
                usuario_id=usuario_id,
                versao_termo=request.versao_termo,
                finalidade=finalidade_codigo,
                aceito=True,
                ip_origem=ip_origem,
                data_aceite=agora,
            )
            total_gravados += 1

        # Registro automático na trilha imutável de auditoria
        self.audit_service.registrar_evento(
            acao=TipoAcaoAuditoria.CRIACAO.value,
            entidade_afetada="TermoConsentimentoLGPD",
            id_registro_afetado=f"usr_{usuario_id}:{request.versao_termo}",
            usuario_id=usuario_id,
            dados_novos={
                "versao_termo": request.versao_termo,
                "finalidades_aceitas": sorted(list(solicitadas)),
            },
            ip_origem=ip_origem,
            data_hora=agora,
        )

        return AceiteConsentimentoResponse(
            mensagem="Consentimento registrado com sucesso.",
            versao_termo=request.versao_termo,
            total_aceites_gravados=total_gravados,
            data_hora=agora.isoformat(),
        )

    def revogar_consentimento(
        self,
        usuario_id: int,
        request: RevogacaoConsentimentoRequest,
        ip_origem: str,
    ) -> RevogacaoConsentimentoResponse:
        termo = self._termo_vigente
        finalidade_obj = next((f for f in termo.finalidades if f.codigo == request.finalidade), None)

        if not finalidade_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Finalidade '{request.finalidade}' desconhecida.",
            )

        if finalidade_obj.obrigatoria:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Finalidades obrigatórias de execução contratual e cumprimento de dever legal não podem ser revogadas.",
            )

        agora = datetime.now(timezone.utc)
        sucesso = self.repository.revogar_consentimento(
            usuario_id=usuario_id,
            versao_termo=request.versao_termo,
            finalidade=request.finalidade,
            ip_origem=ip_origem,
            data_revogacao=agora,
        )

        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consentimento ativo não encontrado para esta versão e finalidade.",
            )

        # Registro de auditoria da revogação
        self.audit_service.registrar_evento(
            acao=TipoAcaoAuditoria.REVOGACAO_LGPD.value,
            entidade_afetada="TermoConsentimentoLGPD",
            id_registro_afetado=f"usr_{usuario_id}:{request.versao_termo}:{request.finalidade}",
            usuario_id=usuario_id,
            dados_anteriores={"aceito": True, "finalidade": request.finalidade},
            dados_novos={"aceito": False, "finalidade": request.finalidade, "data_revogacao": agora.isoformat()},
            ip_origem=ip_origem,
            data_hora=agora,
        )

        return RevogacaoConsentimentoResponse(
            mensagem="Consentimento revogado com sucesso.",
            versao_termo=request.versao_termo,
            finalidade=request.finalidade,
            data_revogacao=agora.isoformat(),
        )

    def listar_historico_titular(self, usuario_id: int) -> List[ConsentimentoItemResponse]:
        registros = self.repository.listar_historico_consentimentos(usuario_id)
        return [
            ConsentimentoItemResponse(
                id_consentimento=item["id_consentimento"],
                usuario_id=item["usuario_id"],
                versao_termo=item["versao_termo"],
                finalidade=item["finalidade"],
                aceito=bool(item["aceito"]),
                data_aceite=str(item["data_aceite"]),
                data_revogacao=str(item["data_revogacao"]) if item["data_revogacao"] else None,
                ip_origem=item["ip_origem"],
            )
            for item in registros
        ]
