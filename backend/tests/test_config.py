import os
from app.core.config import Settings, settings


def test_settings_carrega_valores_padrao_ou_ativos():
    """Valida se a instância padrão de Settings carrega propriedades válidas."""
    assert settings.ENVIRONMENT in ("development", "production", "test")
    assert isinstance(settings.BACKEND_PORT, int)
    assert settings.BACKEND_PORT > 0
    assert settings.DATABASE_URL != ""
    assert settings.JWT_SECRET_KEY != ""
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    assert settings.DEFAULT_ADMIN_EMAIL == "admin@gl4.edu"
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0


def test_settings_cors_origins_e_regex_customizados(monkeypatch):
    """Valida comportamento do parser de CORS com variáveis de ambiente customizadas."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.gl4.edu, https://painel.gl4.edu , ")
    monkeypatch.setenv("CORS_ORIGIN_REGEX", r"^https://.*\.gl4\.edu$")

    custom_settings = Settings()
    assert custom_settings.CORS_ORIGINS == ["https://app.gl4.edu", "https://painel.gl4.edu"]
    assert custom_settings.CORS_ORIGIN_REGEX == r"^https://.*\.gl4\.edu$"


def test_settings_cors_origin_regex_vazio(monkeypatch):
    """Valida que regex vazio resulta em None."""
    monkeypatch.setenv("CORS_ORIGIN_REGEX", "   ")
    custom_settings = Settings()
    assert custom_settings.CORS_ORIGIN_REGEX is None
