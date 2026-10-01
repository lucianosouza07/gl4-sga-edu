/**
 * Contrato de paginação padrão do GL4 SGA-EDU.
 * Espelha o schema `PaginaResponse[T]` do backend (backend/app/schemas/paginacao.py).
 */
export interface PaginaResponse<T> {
  itens: T[];
  total: number;
  pagina: number;
  tamanho_pagina: number;
  total_paginas: number;
}

/** Parâmetros de query comuns a todos os endpoints paginados. */
export interface PaginacaoParams {
  pagina?: number;
  tamanho_pagina?: number;
}
