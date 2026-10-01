import { api } from "@/services/api";
import type { Aluno, AlunoCreate, AlunoUpdate } from "@/types/aluno";
import type { PaginaResponse, PaginacaoParams } from "@/types/paginacao";

export interface ListarAlunosFiltros extends PaginacaoParams {
  busca?: string;
  apenas_ativos?: boolean;
}

export const alunosService = {
  async listar(filtros?: ListarAlunosFiltros): Promise<PaginaResponse<Aluno>> {
    const response = await api.get<PaginaResponse<Aluno>>("/alunos", {
      params: filtros,
    });
    return response.data;
  },

  async obterPorId(id: string): Promise<Aluno> {
    const response = await api.get<Aluno>(`/alunos/${id}`);
    return response.data;
  },

  async cadastrar(dados: AlunoCreate): Promise<Aluno> {
    const response = await api.post<Aluno>("/alunos", dados);
    return response.data;
  },

  async atualizar(id: string, dados: AlunoUpdate): Promise<Aluno> {
    const response = await api.put<Aluno>(`/alunos/${id}`, dados);
    return response.data;
  },

  async inativar(id: string): Promise<Aluno> {
    const response = await api.patch<Aluno>(`/alunos/${id}/inativar`);
    return response.data;
  },
};
