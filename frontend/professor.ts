/**
 * SGA-Edu — Tipagens TypeScript do Domínio de Professores (GL4-34)
 */

export type Titulacao = "Graduação" | "Especialização" | "Mestrado" | "Doutorado";

export interface Professor {
  id: number;
  nome: string;
  email: string;
  cpf: string;
  telefone?: string | null;
  departamento: string;
  titulacao: Titulacao | string;
}

export interface ProfessorEntrada {
  nome: string;
  email: string;
  cpf: string;
  telefone?: string | null;
  departamento: string;
  titulacao: string;
}

/** Métricas exibidas no hero dashboard (GL4-30) */
export interface ResumoMetricas {
  totalProfessores: number;
  modulosAtivos: number;
}
