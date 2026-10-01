/**
 * Utilitário centralizado para extração e tratamento de erros retornados pela API (FastAPI / Pydantic / HTTP).
 */

export interface ErroFormatado {
  mensagemGeral: string;
  errosPorCampo: Record<string, string>;
}

export function extrairErrosAPI(erro: unknown): ErroFormatado {
  const resultado: ErroFormatado = {
    mensagemGeral: "Ocorreu um erro inesperado. Tente novamente mais tarde.",
    errosPorCampo: {},
  };

  if (!erro || typeof erro !== "object") {
    return resultado;
  }

  const err = erro as {
    response?: {
      data?: {
        detail?: string | Array<{ loc?: (string | number)[]; msg?: string }>;
      };
      status?: number;
    };
    message?: string;
  };

  const detail = err.response?.data?.detail;

  // 1. Tratamento para erro de validação do Pydantic (Array de objetos de erro)
  if (Array.isArray(detail)) {
    resultado.mensagemGeral = "Verifique os campos destacados e tente novamente.";
    detail.forEach((item) => {
      if (item.loc && item.loc.length > 0) {
        // Pega o último elemento do loc (nome do campo)
        const campo = String(item.loc[item.loc.length - 1]);
        resultado.errosPorCampo[campo] = item.msg || "Valor inválido.";
      }
    });
    return resultado;
  }

  // 2. Tratamento para HTTPException simples do FastAPI (detail é string)
  if (typeof detail === "string") {
    resultado.mensagemGeral = detail;
    return resultado;
  }

  // 3. Fallback para mensagem padrão do Axios/JS se houver
  if (err.message && !err.response) {
    resultado.mensagemGeral = `Falha de conexão com o servidor: ${err.message}`;
  }

  return resultado;
}
