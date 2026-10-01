from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginaResponse(BaseModel, Generic[T]):
    """
    Schema genérico e universal para respostas paginadas na API do GL4 SGA-EDU.
    """
    itens: List[T] = Field(..., description="Lista de registros da página atual")
    total: int = Field(..., description="Quantidade total de registros encontrados")
    pagina: int = Field(..., ge=1, description="Número da página atual (iniciando em 1)")
    tamanho_pagina: int = Field(..., ge=1, description="Quantidade de registros por página")
    total_paginas: int = Field(..., ge=0, description="Total de páginas disponíveis")
