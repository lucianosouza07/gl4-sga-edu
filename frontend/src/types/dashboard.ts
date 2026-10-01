export type PeriodoDashboard = "3" | "6" | "ano";

export interface MatriculasPorMes {
  mes: string;
  total: number;
  parcial: boolean;
}

export interface AlunosPorStatus {
  status: string;
  total: number;
}

export interface CadastroRecente {
  id: string;
  nome_completo: string;
  matricula: string;
  status: string;
  criado_em: string;
}

export interface Dashboard {
  gerado_em: string;
  ano: number;
  semestre: number;
  periodo: { chave: PeriodoDashboard; inicio: string; fim: string };
  totais: { alunos: number; ativos: number; inativos: number; novas_matriculas: number };
  matriculas_por_mes: MatriculasPorMes[];
  alunos_por_status: AlunosPorStatus[];
  ultimos_cadastros: CadastroRecente[];
}
