import { apiClient } from "@/api/client";
import type { AlunoPerfil, AlunoMeUpdatePayload } from "../data/portal-aluno.types";

export const portalAlunoApi = {
  /**
   * Obtém os dados cadastrais do aluno autenticado (Self-Service).
   */
  async obterMeuPerfil(): Promise<AlunoPerfil> {
    const response = await apiClient.get<AlunoPerfil>("/alunos/me");
    return response.data;
  },

  /**
   * Atualiza os dados permitidos do próprio perfil (telefone e/ou senha).
   */
  async atualizarMeuPerfil(payload: AlunoMeUpdatePayload): Promise<AlunoPerfil> {
    const response = await apiClient.put<AlunoPerfil>("/alunos/me", payload);
    return response.data;
  },
};
