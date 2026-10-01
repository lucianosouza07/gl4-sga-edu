export type PerfilUsuario = "ADMIN" | "SECRETARIA" | "PROFESSOR" | "ALUNO";

export interface Usuario {
  id: string;
  nome: string;
  email: string;
  perfil: PerfilUsuario;
  ativo: boolean;
  criado_em: string;
}

export interface LoginRequest {
  identificador: string;
  senha: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  usuario: Usuario;
}
