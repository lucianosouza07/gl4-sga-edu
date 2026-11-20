"""Schemas Pydantic v2 para requisições, respostas e validações do módulo LGPD e Auditoria."""

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class FinalidadeItem(BaseModel):
    codigo: str
    titulo: str
    descricao: str
    obrigatoria: bool


class TermoVigenteResponse(BaseModel):
    versao: str
    data_publicacao: str
    titulo: str
    conteudo: str
    finalidades: List[FinalidadeItem]


class ConsentimentoStatusResponse(BaseModel):
    usuario_id: int
    versao_vigente: str
    possui_aceite_vigente: bool
    pendente_nova_versao: bool
    consentimentos_ativos: List[str]


class AceiteConsentimentoRequest(BaseModel):
    versao_termo: str = Field(..., min_length=1, max_length=20)
    finalidades: List[str] = Field(..., min_length=1)


class AceiteConsentimentoResponse(BaseModel):
    mensagem: str
    versao_termo: str
    total_aceites_gravados: int
    data_hora: str


class RevogacaoConsentimentoRequest(BaseModel):
    versao_termo: str = Field(..., min_length=1, max_length=20)
    finalidade: str = Field(..., min_length=1, max_length=120)


class RevogacaoConsentimentoResponse(BaseModel):
    mensagem: str
    versao_termo: str
    finalidade: str
    data_revogacao: str


class ConsentimentoItemResponse(BaseModel):
    id_consentimento: int
    usuario_id: int
    versao_termo: str
    finalidade: str
    aceito: bool
    data_aceite: str
    data_revogacao: Optional[str] = None
    ip_origem: str


class LogAuditoriaCriacao(BaseModel):
    usuario_id: Optional[int] = None
    entidade_afetada: str = Field(..., min_length=1, max_length=80)
    id_registro_afetado: Optional[str] = Field(None, max_length=64)
    acao: str = Field(..., min_length=1, max_length=50)
    dados_anteriores: Optional[Any] = None
    dados_novos: Optional[Any] = None
    ip_origem: Optional[str] = "127.0.0.1"


class LogAuditoriaItemResponse(BaseModel):
    id_auditoria: int
    usuario_id: Optional[int] = None
    entidade_afetada: str
    id_registro_afetado: Optional[str] = None
    acao: str
    dados_anteriores: Optional[str] = None
    dados_novos: Optional[str] = None
    ip_origem: str
    data_hora: str


class AuditoriaConsultaFiltros(BaseModel):
    usuario_id: Optional[int] = None
    entidade_afetada: Optional[str] = None
    acao: Optional[str] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    limite: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)


class AuditoriaConsultaResponse(BaseModel):
    total: int
    limite: int
    offset: int
    itens: List[LogAuditoriaItemResponse]


class SimpleMessageResponse(BaseModel):
    mensagem: str
