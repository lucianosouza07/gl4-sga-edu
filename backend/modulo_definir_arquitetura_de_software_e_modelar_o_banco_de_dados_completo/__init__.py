"""
Módulo: Definir arquitetura de software e modelar o banco de dados completo (SGA-18).

Fornece a especificação estruturada da arquitetura multicamadas do SGA-Edu,
os scripts DDL e DML completos das 33 tabelas distribuídas em 6 domínios,
o motor de validação de integridade relacional e o roteador FastAPI de inspeção.
"""

from .database_manager import (
    DOMINIOS_BANCO_DADOS,
    TABELAS_CATALOGO,
    criar_conexao_validada,
    listar_tabelas_esquema,
    obter_resumo_arquitetura,
    validar_esquema_completo,
)
from .router import router
from .schemas import (
    CamadaArquitetural,
    DominioBancoDados,
    EspecificacaoChaveEstrangeira,
    EspecificacaoColuna,
    EspecificacaoTabela,
    RelatorioIntegridadeSchema,
    ResumoArquiteturaSGA,
)

__all__ = [
    "DOMINIOS_BANCO_DADOS",
    "TABELAS_CATALOGO",
    "CamadaArquitetural",
    "DominioBancoDados",
    "EspecificacaoChaveEstrangeira",
    "EspecificacaoColuna",
    "EspecificacaoTabela",
    "RelatorioIntegridadeSchema",
    "ResumoArquiteturaSGA",
    "criar_conexao_validada",
    "listar_tabelas_esquema",
    "obter_resumo_arquitetura",
    "router",
    "validar_esquema_completo",
]
