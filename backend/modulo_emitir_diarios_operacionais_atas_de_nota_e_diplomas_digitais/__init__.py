"""Módulo SGA-25: Emitir diários operacionais, atas de nota e diplomas digitais."""

try:
    from .repository import DocumentoRepository, get_repository
    from .router import app, router
    from .service import DocumentoService
except ImportError:
    from repository import DocumentoRepository, get_repository
    from router import app, router
    from service import DocumentoService

__all__ = ["app", "router", "DocumentoRepository", "DocumentoService", "get_repository"]
