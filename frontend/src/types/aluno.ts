export type StatusAluno = "ATIVO" | "INATIVO" | "TRANCADO" | "FORMADO";

export interface Aluno {
  id: string;
  usuario_id: string;
  matricula: string;
  nome_completo: string;
  cpf: string;
  email: string;
  telefone?: string | null;
  data_nascimento: string;
  status: StatusAluno;
  criado_em: string;
  atualizado_em?: string | null;
}

export interface AlunoCreate {
  matricula: string;
  nome_completo: string;
  cpf: string;
  email: string;
  telefone?: string | null;
  data_nascimento: string;
  senha_inicial?: string | null;
}

export interface AlunoUpdate {
  nome_completo?: string | null;
  telefone?: string | null;
  data_nascimento?: string | null;
  status?: StatusAluno | null;
}
