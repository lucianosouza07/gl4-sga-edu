import logging
import os
from sqlalchemy.orm import Session
from app.models.usuario import Usuario, PerfilUsuario
from app.core.security import gerar_hash_senha
from app.database.session import SessionLocal, init_db

logger = logging.getLogger("sga_edu.seeds")


def seed_admin_padrao(db: Session) -> Usuario:
    """
    Garante a existência do usuário Administrador padrão no banco de dados.
    Operação idempotente: se o usuário já existir, apenas retorna o registro sem duplicar.
    """
    admin_nome = os.getenv("DEFAULT_ADMIN_NAME", "Administrador do Sistema")
    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@gl4.edu")
    admin_senha = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

    admin = db.query(Usuario).filter(Usuario.email == admin_email).first()

    if not admin:
        logger.info(f"Criando usuário Administrador padrão: {admin_email}")
        admin = Usuario(
            nome=admin_nome,
            email=admin_email,
            senha_hash=gerar_hash_senha(admin_senha),
            perfil=PerfilUsuario.ADMIN.value,
            ativo=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        logger.info("Usuário Administrador padrão criado com sucesso!")
    else:
        logger.info(f"Usuário Administrador padrão ({admin_email}) já existe. Nenhuma ação necessária.")

    return admin


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Inicializando tabelas do banco de dados...")
    init_db()
    with SessionLocal() as session:
        usuario_admin = seed_admin_padrao(session)
        print(f"✅ Administrador verificado/criado: {usuario_admin.email} (Perfil: {usuario_admin.perfil})")
