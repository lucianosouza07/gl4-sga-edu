export type PerfilUsuario = "ADMIN" | "SECRETARIA" | "PROFESSOR" | "ALUNO";

export interface Usuario {
  id: string;
  email: string;
  nome: string;
  perfil: PerfilUsuario;
  ativo: boolean;
  criado_em: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  usuario: Usuario;
}

export interface LoginPayload {
  identificador: string;
  senha: string;
}
