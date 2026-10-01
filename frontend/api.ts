/**
 * SGA-Edu — Serviço de Integração com o Backend FastAPI (GL4-34 + GL4-30)
 */
import type { Professor, ProfessorEntrada } from "./professor";

// Base URL apontando para o FastAPI na porta 8000
const API_BASE = "http://127.0.0.1:8000/api";

/** Lista todos os professores cadastrados */
export async function listarProfessores(): Promise<Professor[]> {
  const resp = await fetch(`${API_BASE}/professores`, {
    headers: { Accept: "application/json" },
  });
  if (!resp.ok) {
    throw new Error(`Falha na API: status ${resp.status}`);
  }
  return resp.json();
}

/** Cadastra um novo professor */
export async function cadastrarProfessor(dados: ProfessorEntrada): Promise<Professor> {
  const resp = await fetch(`${API_BASE}/professores`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(dados),
  });

  const corpo = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    let mensagem = "Erro ao cadastrar professor.";
    if (typeof corpo.detail === "string") {
      mensagem = corpo.detail;
    } else if (Array.isArray(corpo.detail)) {
      mensagem = corpo.detail
        .map((item: { msg?: string }) => item.msg || "Campo inválido")
        .join(", ");
    }
    throw new Error(mensagem);
  }
  return corpo;
}

/** Atualiza um professor existente (PUT /api/professores/{id}) */
export async function atualizarProfessor(
  id: number,
  dados: ProfessorEntrada
): Promise<Professor> {
  const resp = await fetch(`${API_BASE}/professores/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(dados),
  });

  const corpo = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    let mensagem = "Erro ao atualizar professor.";
    if (typeof corpo.detail === "string") {
      mensagem = corpo.detail;
    } else if (Array.isArray(corpo.detail)) {
      mensagem = corpo.detail
        .map((item: { msg?: string }) => item.msg || "Campo inválido")
        .join(", ");
    }
    throw new Error(mensagem);
  }
  return corpo;
}

/** Remove um professor pelo ID (DELETE /api/professores/{id}) */
export async function excluirProfessor(id: number): Promise<void> {
  const resp = await fetch(`${API_BASE}/professores/${id}`, {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });
  if (!resp.ok) {
    const corpo = await resp.json().catch(() => ({}));
    const mensagem =
      typeof corpo.detail === "string" ? corpo.detail : "Erro ao excluir professor.";
    throw new Error(mensagem);
  }
}

/** Verifica se o backend FastAPI está acessível (timeout 3s) */
export async function checarStatusBackend(): Promise<{ online: boolean; rotulo: string }> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);
    const resp = await fetch(`${API_BASE}/professores`, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
    clearTimeout(timeoutId);
    if (resp.ok) {
      return { online: true, rotulo: "Sistema Online (FastAPI)" };
    }
    return { online: false, rotulo: "Sistema Operacional" };
  } catch {
    return { online: false, rotulo: "Sistema Operacional (Local)" };
  }
}
