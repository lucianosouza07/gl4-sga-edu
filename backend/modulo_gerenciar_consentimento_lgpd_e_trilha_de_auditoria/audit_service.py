"""Serviço transversal de auditoria com higienização de senhas e persistência imutável."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .repository import LgpdAuditRepository
from .schemas import LogAuditoriaItemResponse

PALAVRAS_SENSIVEIS = {
    "senha",
    "password",
    "hash",
    "secret",
    "token",
    "chave",
    "cartao",
    "credit_card",
    "pin",
    "cvv",
    "tokenmfa",
    "chave_mfa",
    "codigo_recuperacao",
}


def sanitize_audit_payload(dados: Any) -> Optional[str]:
    """Higieniza payloads mascarando credenciais, chaves e senhas antes de serializar em JSON."""
    if dados is None:
        return None

    def _sanitizar(obj: Any) -> Any:
        if isinstance(obj, dict):
            limpo = {}
            for k, v in obj.items():
                chave_normalizada = str(k).lower().strip()
                if any(sensivel in chave_normalizada for sensivel in PALAVRAS_SENSIVEIS):
                    limpo[k] = "[REDACTED]"
                else:
                    limpo[k] = _sanitizar(v)
            return limpo
        elif isinstance(obj, list):
            return [_sanitizar(item) for item in obj]
        elif isinstance(obj, (int, float, bool, str)):
            return obj
        elif hasattr(obj, "isoformat"):
            return obj.isoformat()
        else:
            return str(obj)

    try:
        dados_higienizados = _sanitizar(dados)
        return json.dumps(dados_higienizados, ensure_ascii=False, default=str)
    except Exception:
        return str(dados)


class AuditService:
    """Gerencia a captura, higienização e consulta da trilha de auditoria do sistema."""

    def __init__(self, repository: LgpdAuditRepository):
        self.repository = repository

    def registrar_evento(
        self,
        acao: str,
        entidade_afetada: str,
        id_registro_afetado: Optional[str] = None,
        usuario_id: Optional[int] = None,
        dados_anteriores: Optional[Any] = None,
        dados_novos: Optional[Any] = None,
        ip_origem: str = "127.0.0.1",
        data_hora: Optional[datetime] = None,
    ) -> int:
        """Registra um evento imutável na trilha de auditoria com dados higienizados."""
        ts = data_hora or datetime.now(timezone.utc)
        payload_anterior_sanitizado = sanitize_audit_payload(dados_anteriores)
        payload_novo_sanitizado = sanitize_audit_payload(dados_novos)

        return self.repository.inserir_log_auditoria(
            usuario_id=usuario_id,
            entidade_afetada=entidade_afetada,
            id_registro_afetado=str(id_registro_afetado) if id_registro_afetado is not None else None,
            acao=acao,
            dados_anteriores=payload_anterior_sanitizado,
            dados_novos=payload_novo_sanitizado,
            ip_origem=ip_origem,
            data_hora=ts,
        )

    def consultar_auditoria(
        self,
        usuario_id: Optional[int] = None,
        entidade_afetada: Optional[str] = None,
        acao: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        limite: int = 50,
        offset: int = 0,
    ) -> Tuple[int, List[LogAuditoriaItemResponse]]:
        total, itens_dict = self.repository.consultar_logs_auditoria(
            usuario_id=usuario_id,
            entidade_afetada=entidade_afetada,
            acao=acao,
            data_inicio=data_inicio,
            data_fim=data_fim,
            limite=limite,
            offset=offset,
        )

        itens_resp = [
            LogAuditoriaItemResponse(
                id_auditoria=item["id_auditoria"],
                usuario_id=item["usuario_id"],
                entidade_afetada=item["entidade_afetada"],
                id_registro_afetado=item["id_registro_afetado"],
                acao=item["acao"],
                dados_anteriores=item["dados_anteriores"],
                dados_novos=item["dados_novos"],
                ip_origem=item["ip_origem"],
                data_hora=str(item["data_hora"]),
            )
            for item in itens_dict
        ]

        return total, itens_resp

    def buscar_detalhe_por_id(self, id_auditoria: int) -> Optional[LogAuditoriaItemResponse]:
        item = self.repository.buscar_log_por_id(id_auditoria)
        if not item:
            return None
        return LogAuditoriaItemResponse(
            id_auditoria=item["id_auditoria"],
            usuario_id=item["usuario_id"],
            entidade_afetada=item["entidade_afetada"],
            id_registro_afetado=item["id_registro_afetado"],
            acao=item["acao"],
            dados_anteriores=item["dados_anteriores"],
            dados_novos=item["dados_novos"],
            ip_origem=item["ip_origem"],
            data_hora=str(item["data_hora"]),
        )
