/**
 * Tipos e interfaces de dados para o Portal do Aluno (Self-Service).
 */

export interface AlunoPerfil {
  id: string;
  usuario_id: string;
  matricula: string;
  nome_completo: string;
  cpf: string;
  email: string;
  telefone?: string | null;
  data_nascimento: string;
  status: "ATIVO" | "INATIVO" | string;
  criado_em: string;
  atualizado_em?: string | null;
}

export interface AlunoMeUpdatePayload {
  telefone?: string | null;
  senha_atual?: string;
  nova_senha?: string;
}

export interface FormAlterarSenhaData {
  senhaAtual: string;
  novaSenha: string;
  confirmarNovaSenha: string;
}
