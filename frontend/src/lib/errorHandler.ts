/**
 * Utilitários para tratamento padronizado de erros de API.
 *
 * O backend retorna erros de validação no formato:
 * { detail: string; erros?: Array<{ campo: string; mensagem: string }> }
 */

export interface ErroValidacao {
  campo: string;
  mensagem: string;
}

export interface ErroAPI {
  detail: string;
  erros?: ErroValidacao[];
}

/**
 * Extrai a mensagem geral e os erros por campo de uma resposta de erro Axios.
 *
 * @returns `{ mensagemGeral, errosPorCampo }` onde `errosPorCampo` é um
 *   Record<campo, mensagem> para facilitar a exibição nos formulários.
 */
export function extrairErrosAPI(err: unknown): {
  mensagemGeral: string;
  errosPorCampo: Record<string, string>;
} {
  const defaultMsg = "Ocorreu um erro inesperado. Tente novamente.";

  if (!err || typeof err !== "object") {
    return { mensagemGeral: defaultMsg, errosPorCampo: {} };
  }

  // Axios errors expose `response.data`
  const data = (err as { response?: { data?: ErroAPI } }).response?.data;

  if (!data) {
    return { mensagemGeral: defaultMsg, errosPorCampo: {} };
  }

  const mensagemGeral = data.detail ?? defaultMsg;
  const errosPorCampo: Record<string, string> = {};

  if (Array.isArray(data.erros)) {
    for (const e of data.erros) {
      if (e.campo) errosPorCampo[e.campo] = e.mensagem;
    }
  }

  return { mensagemGeral, errosPorCampo };
}
