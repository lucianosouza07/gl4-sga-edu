"""Modelos de dados e repositório de persistência para recuperação de senha."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Usuario:
    id_usuario: int
    login: str
    email: str
    senha_hash: str
    token_versao: int = 1
    statusCONTA: int = 1


@dataclass
class TokenRecuperacao:
    id_token: int
    usuario_id: int
    token_hash: str
    criado_em: datetime
    expira_em: datetime
    utilizado: bool = False
    utilizado_em: Optional[datetime] = None
    revogado: bool = False
    ip_solicitacao: str = ""
    ip_utilizacao: Optional[str] = None


@dataclass
class LogAuditoriaRecuperacao:
    id_log: int
    usuario_id: Optional[int]
    data_hora: datetime
    ip_origem: str
    user_agent: Optional[str]
    acao: str
    status_resultado: str
    detalhes: Optional[str] = None


class Database:
    """Repositório de persistência thread-safe em memória simulando o banco relacional."""

    usuarios: Dict[int, Usuario] = {}
    tokens: Dict[int, TokenRecuperacao] = {}
    auditoria: List[LogAuditoriaRecuperacao] = []
    _next_token_id: int = 1
    _next_log_id: int = 1

    @classmethod
    def reset(cls):
        cls.usuarios.clear()
        cls.tokens.clear()
        cls.auditoria.clear()
        cls._next_token_id = 1
        cls._next_log_id = 1

    @classmethod
    def buscar_usuario_por_email(cls, email: str) -> Optional[Usuario]:
        email_norm = email.strip().lower()
        for u in cls.usuarios.values():
            if u.email.strip().lower() == email_norm and u.statusCONTA == 1:
                return u
        return None

    @classmethod
    def buscar_usuario_por_id(cls, usuario_id: int) -> Optional[Usuario]:
        return cls.usuarios.get(usuario_id)

    @classmethod
    def revogar_tokens_pendentes(cls, usuario_id: int) -> int:
        revogados = 0
        for token in cls.tokens.values():
            if token.usuario_id == usuario_id and not token.utilizado and not token.revogado:
                token.revogado = True
                revogados += 1
        return revogados

    @classmethod
    def salvar_token(cls, usuario_id: int, token_hash: str, criado_em: datetime, expira_em: datetime, ip_solicitacao: str) -> TokenRecuperacao:
        token_id = cls._next_token_id
        cls._next_token_id += 1
        registro = TokenRecuperacao(
            id_token=token_id,
            usuario_id=usuario_id,
            token_hash=token_hash,
            criado_em=criado_em,
            expira_em=expira_em,
            utilizado=False,
            revogado=False,
            ip_solicitacao=ip_solicitacao,
        )
        cls.tokens[token_id] = registro
        return registro

    @classmethod
    def buscar_token_por_hash(cls, token_hash: str) -> Optional[TokenRecuperacao]:
        for token in cls.tokens.values():
            if token.token_hash == token_hash:
                return token
        return None

    @classmethod
    def consumir_token(cls, id_token: int, ip_utilizacao: str, momento: datetime) -> bool:
        token = cls.tokens.get(id_token)
        if not token:
            return False
        token.utilizado = True
        token.utilizado_em = momento
        token.ip_utilizacao = ip_utilizacao
        return True

    @classmethod
    def atualizar_senha(cls, usuario_id: int, novo_hash: str) -> bool:
        usuario = cls.usuarios.get(usuario_id)
        if not usuario:
            return False
        usuario.senha_hash = novo_hash
        usuario.token_versao += 1
        return True

    @classmethod
    def registrar_log(
        cls,
        acao: str,
        status_resultado: str,
        ip_origem: str,
        usuario_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        detalhes: Optional[str] = None,
        data_hora: Optional[datetime] = None,
    ) -> LogAuditoriaRecuperacao:
        log_id = cls._next_log_id
        cls._next_log_id += 1
        registro = LogAuditoriaRecuperacao(
            id_log=log_id,
            usuario_id=usuario_id,
            data_hora=data_hora or datetime.now(timezone.utc),
            ip_origem=ip_origem,
            user_agent=user_agent,
            acao=acao,
            status_resultado=status_resultado,
            detalhes=detalhes,
        )
        cls.auditoria.append(registro)
        return registro
