import type { PaginacaoParams } from "@/types/paginacao";

export type AlunoStatus = "ATIVO" | "INATIVO" | "TRANCADO" | "FORMADO";

export interface Aluno {
  id: string;
  usuario_id: string;
  nome_completo: string;
  matricula: string;
  cpf: string;
  email: string;
  telefone: string | null;
  data_nascimento: string;
  status: AlunoStatus;
  criado_em: string;
  atualizado_em: string;
}

export interface AlunoCreate {
  nome_completo: string;
  cpf: string;
  email: string;
  telefone?: string | null;
  data_nascimento: string;
  senha_inicial?: string | null;
}

export interface AlunoUpdate {
  nome_completo?: string;
  telefone?: string | null;
  data_nascimento?: string;
}

export interface ListarAlunosFiltros extends PaginacaoParams {
  busca?: string;
  apenas_ativos?: boolean;
}
