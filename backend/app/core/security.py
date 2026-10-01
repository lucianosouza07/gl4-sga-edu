from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Configuração de hash de senhas via Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configurações do JWT
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def gerar_hash_senha(senha: str) -> str:
    """Gera um hash seguro da senha fornecida utilizando bcrypt."""
    return pwd_context.hash(senha)


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Compara uma senha em texto plano com seu hash armazenado."""
    return pwd_context.verify(senha_plana, senha_hash)


def criar_token_jwt(data: dict, expires_delta: timedelta | None = None) -> str:
    """Cria um JSON Web Token (JWT) assinado contendo os dados do payload e expiração."""
    payload = data.copy()
    agora = datetime.now(timezone.utc)
    
    if expires_delta:
        expiracao = agora + expires_delta
    else:
        expiracao = agora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload.update({
        "exp": expiracao,
        "iat": agora
    })
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decodificar_token_jwt(token: str) -> dict:
    """
    Decodifica e valida a assinatura e expiração de um token JWT.
    Lança jwt.ExpiredSignatureError se expirado ou jwt.InvalidTokenError se inválido.
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
