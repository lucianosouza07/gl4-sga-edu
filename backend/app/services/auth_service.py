from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.models.aluno import Aluno
from app.schemas.auth import TokenResponse, UsuarioResponse
from app.core.security import verificar_senha, criar_token_jwt
from app.core.exceptions import CredenciaisInvalidasError


class AuthService:
    """Serviço de autenticação e emissão de tokens JWT."""

    def __init__(self, db: Session):
        self.db = db

    def autenticar_usuario(self, identificador: str, senha: str) -> Usuario:
        """
        Autentica o usuário por identificador flexível (E-mail ou Matrícula) e senha.
        Lança CredenciaisInvalidasError caso não encontre ou a senha esteja incorreta.
        """
        identificador_limpo = identificador.strip()
        usuario: Usuario | None = None

        # 1. Tentar localizar usuário diretamente pelo e-mail
        usuario = self.db.query(Usuario).filter(Usuario.email.ilike(identificador_limpo)).first()

        # 2. Se não encontrar, tentar localizar por matrícula de aluno
        if not usuario:
            aluno = self.db.query(Aluno).filter(Aluno.matricula == identificador_limpo).first()
            if aluno and aluno.usuario:
                usuario = aluno.usuario

        # 3. Validar existência e se a conta está ativa
        if not usuario or not usuario.ativo:
            raise CredenciaisInvalidasError("Credenciais inválidas. Verifique seu login e senha.")

        # 4. Validar hash de senha
        if not verificar_senha(senha, usuario.senha_hash):
            raise CredenciaisInvalidasError("Credenciais inválidas. Verifique seu login e senha.")

        return usuario

    def gerar_token_para_usuario(self, usuario: Usuario) -> TokenResponse:
        """Emite token JWT assinado para o usuário autenticado."""
        payload = {
            "sub": str(usuario.id),
            "email": usuario.email,
            "perfil": usuario.perfil,
            "nome": usuario.nome
        }
        token = criar_token_jwt(payload)
        usuario_dto = UsuarioResponse.model_validate(usuario)

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            usuario=usuario_dto
        )

    def autenticar_e_gerar_token(self, identificador: str, senha: str) -> TokenResponse:
        """Convenience method que autentica e já retorna a resposta do token."""
        usuario = self.autenticar_usuario(identificador, senha)
        return self.gerar_token_para_usuario(usuario)
