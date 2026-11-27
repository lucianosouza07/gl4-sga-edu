"""Módulo SGA-27: Desenvolver painel administrativo para coordenação."""

try:
    from .repository import PainelCoordenacaoRepository, get_repository
    from .router import app, router
    from .service import PainelCoordenacaoService
except ImportError:
    from repository import PainelCoordenacaoRepository, get_repository
    from router import app, router
    from service import PainelCoordenacaoService

__all__ = ["app", "router", "PainelCoordenacaoRepository", "PainelCoordenacaoService", "get_repository"]
