"""Módulo SGA-26: Validar aproveitamento de estudos e equivalências."""

try:
    from .repository import AproveitamentoRepository, get_repository
    from .router import app, router
    from .service import AproveitamentoService
except ImportError:
    from repository import AproveitamentoRepository, get_repository
    from router import app, router
    from service import AproveitamentoService

__all__ = ["app", "router", "AproveitamentoRepository", "AproveitamentoService", "get_repository"]
