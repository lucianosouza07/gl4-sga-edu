from sqlalchemy.orm import Session
from app.models.usuario import Usuario, PerfilUsuario
from app.core.security import verificar_senha
from app.seeds.admin_seed import seed_admin_padrao


def test_seed_admin_cria_usuario_inicial(db_session: Session):
    """Verifica se o seed cria o usuário admin quando o banco está vazio."""
    admin = seed_admin_padrao(db_session)

    assert admin is not None
    assert admin.nome == "Administrador do Sistema"
    assert admin.email == "admin@gl4.edu"
    assert admin.perfil == PerfilUsuario.ADMIN.value
    assert admin.ativo is True
    # Senha padrão é 'admin123'
    assert verificar_senha("admin123", admin.senha_hash) is True


def test_seed_admin_eh_idempotente(db_session: Session):
    """Executar o seed repetidas vezes não pode duplicar nem causar erro de integridade."""
    admin1 = seed_admin_padrao(db_session)
    admin2 = seed_admin_padrao(db_session)

    assert admin1.id == admin2.id
    total_admins = db_session.query(Usuario).filter(Usuario.email == "admin@gl4.edu").count()
    assert total_admins == 1
