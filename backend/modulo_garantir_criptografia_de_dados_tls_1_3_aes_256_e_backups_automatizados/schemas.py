"""Modelos e Schemas Pydantic para Criptografia e Backups Automatizados."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TLSStatusResponse(BaseModel):
    protocolo_negociado: str = Field(..., description="Versão do TLS negociada na conexão")
    cifra: Optional[str] = Field(None, description="Suite de cifra criptográfica utilizada")
    versao_tls_valida: bool = Field(..., description="Indica se a versão é válida e suportada")
    em_conformidade_tls13: bool = Field(..., description="Indica conformidade com o padrão estrito TLS 1.3")


class TestEncryptionRequest(BaseModel):
    texto_plano: str = Field(..., min_length=1, description="Texto ou dado sensível a ser cifrado")


class TestEncryptionResponse(BaseModel):
    texto_plano_original: str
    carga_cifrada: str
    texto_decifrado: str
    autenticidade_validada: bool
    algoritmo: str = "AES-256-GCM"


class ExecutarBackupRequest(BaseModel):
    tipo: str = Field("MANUAL", pattern="^(COMPLETO|INCREMENTAL|MANUAL)$")
    observacoes: Optional[str] = None


class BackupRegistroResponse(BaseModel):
    id_backup: int
    nome_arquivo: str
    tipo_backup: str
    tamanho_original_bytes: int
    tamanho_cifrado_bytes: int
    checksum_sha256: str
    algoritmo_cifragem: str
    criado_em: datetime
    expira_em: datetime
    status: str
    validado_em: Optional[datetime] = None
    status_integridade: str
    iniciado_por: str


class ValidacaoIntegridadeResponse(BaseModel):
    backup_id: int
    checksum_esperado: str
    checksum_calculado: str
    integridade_preservada: bool
    validado_em: datetime


class SimulacaoRestauracaoResponse(BaseModel):
    backup_id: int
    sucesso: bool
    duracao_segundos: float
    dentro_do_rto: bool
    tabelas_restauradas: int
    total_registros_validados: int
    mensagem: str


class PoliticaRetencaoResponse(BaseModel):
    id_politica: int
    frequencia_cron: str
    dias_retencao_diario: int
    meses_retencao_mensal: int
    copias_minimas_seguranca: int
    compactacao_habilitada: bool
    cifragem_habilitada: bool
    atualizado_em: datetime
    atualizado_por: Optional[str] = None


class AtualizarPoliticaRequest(BaseModel):
    frequencia_cron: Optional[str] = Field(None, min_length=5, max_length=50)
    dias_retencao_diario: Optional[int] = Field(None, ge=1, le=365)
    meses_retencao_mensal: Optional[int] = Field(None, ge=1, le=60)
    copias_minimas_seguranca: Optional[int] = Field(None, ge=1, le=30)


class ExpurgoResponse(BaseModel):
    quantidade_expurgada: int
    espaco_liberado_bytes: int
    copias_preservadas: int
    arquivos_removidos: List[str] = Field(default_factory=list)


class ErroResponse(BaseModel):
    detail: str
