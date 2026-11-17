"""
Roteador FastAPI para consulta da arquitetura de software e validação do banco de dados completo (SGA-18).
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from .database_manager import (
    DOMINIOS_BANCO_DADOS,
    listar_tabelas_esquema,
    obter_resumo_arquitetura,
    validar_esquema_completo,
)
from .schemas import (
    EspecificacaoTabela,
    RelatorioIntegridadeSchema,
    ResumoArquiteturaSGA,
)

router = APIRouter(prefix="/api/arquitetura-bd", tags=["Arquitetura e Modelagem de BD"])


@router.get("/resumo", response_model=ResumoArquiteturaSGA)
def consultar_resumo_arquitetura() -> ResumoArquiteturaSGA:
    """Retorna a definição estruturada das camadas da arquitetura e dos domínios do banco de dados."""
    return obter_resumo_arquitetura()


@router.get("/tabelas", response_model=List[EspecificacaoTabela])
def consultar_tabelas_esquema(
    dominio: Optional[str] = Query(default=None, description="Código opcional do domínio para filtragem")
) -> List[EspecificacaoTabela]:
    """Lista todas as tabelas modeladas no esquema completo com colunas, PK, FKs e índices."""
    if dominio is not None:
        codigos_validos = {d.codigo.lower() for d in DOMINIOS_BANCO_DADOS}
        if dominio.strip().lower() not in codigos_validos:
            raise HTTPException(
                status_code=404,
                detail=f"Domínio '{dominio}' não encontrado no esquema do SGA-Edu.",
            )
    return listar_tabelas_esquema(dominio=dominio)


@router.post("/validar-integridade", response_model=RelatorioIntegridadeSchema)
def executar_validacao_integridade() -> RelatorioIntegridadeSchema:
    """Provisiona o DDL e os seeds em banco relacional isolado e retorna o relatório de integridade."""
    return validar_esquema_completo()
