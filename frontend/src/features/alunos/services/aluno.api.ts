import { apiClient } from "@/api/client";
import type { Aluno, AlunoCreate, AlunoUpdate, ListarAlunosFiltros } from "../data/aluno.types";
import type { PaginaResponse } from "@/types/paginacao";

export const alunoApi = {
  async listar(filtros?: ListarAlunosFiltros): Promise<PaginaResponse<Aluno>> {
    const response = await apiClient.get<PaginaResponse<Aluno>>("/alunos", {
      params: filtros,
    });
    return response.data;
  },

  async obterPorId(id: string): Promise<Aluno> {
    const response = await apiClient.get<Aluno>(`/alunos/${id}`);
    return response.data;
  },

  async cadastrar(dados: AlunoCreate): Promise<Aluno> {
    const response = await apiClient.post<Aluno>("/alunos", dados);
    return response.data;
  },

  async atualizar(id: string, dados: AlunoUpdate): Promise<Aluno> {
    const response = await apiClient.put<Aluno>(`/alunos/${id}`, dados);
    return response.data;
  },

  async inativar(id: string): Promise<Aluno> {
    const response = await apiClient.patch<Aluno>(`/alunos/${id}/inativar`);
    return response.data;
  },

  async reativar(id: string): Promise<Aluno> {
    const response = await apiClient.patch<Aluno>(`/alunos/${id}/reativar`);
    return response.data;
  },
};
