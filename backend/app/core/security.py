from passlib.context import CryptContext

# Configuração do contexto de hash utilizando Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def gerar_hash_senha(senha: str) -> str:
    """Gera um hash seguro da senha fornecida utilizando bcrypt."""
    return pwd_context.hash(senha)


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Compara uma senha em texto plano com seu hash armazenado."""
    return pwd_context.verify(senha_plana, senha_hash)
