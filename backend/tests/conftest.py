import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
import app.models  # Garante registro dos modelos Usuario e Aluno
from app.main import app
from app.models.usuario import Usuario, PerfilUsuario
from app.core.security import gerar_hash_senha, criar_token_jwt


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Cria um banco de dados SQLite isolado em memória para cada teste."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Retorna um TestClient do FastAPI conectado ao db_session isolado."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db_session: Session) -> Usuario:
    """Cria e retorna um usuário ADMIN persistido no banco de teste."""
    user = Usuario(
        nome="Admin Master",
        email="admin.teste@gl4.edu",
        senha_hash=gerar_hash_senha("admin123"),
        perfil=PerfilUsuario.ADMIN.value,
        ativo=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_headers(admin_user: Usuario) -> dict[str, str]:
    """Retorna os headers de autorização Bearer para o usuário ADMIN."""
    token = criar_token_jwt({
        "sub": str(admin_user.id),
        "email": admin_user.email,
        "perfil": admin_user.perfil,
        "nome": admin_user.nome
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def secretaria_user(db_session: Session) -> Usuario:
    """Cria e retorna um usuário SECRETARIA persistido no banco de teste."""
    user = Usuario(
        nome="Secretaria Ana",
        email="secretaria.teste@gl4.edu",
        senha_hash=gerar_hash_senha("sec123"),
        perfil=PerfilUsuario.SECRETARIA.value,
        ativo=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def secretaria_headers(secretaria_user: Usuario) -> dict[str, str]:
    """Retorna os headers de autorização Bearer para a SECRETARIA."""
    token = criar_token_jwt({
        "sub": str(secretaria_user.id),
        "email": secretaria_user.email,
        "perfil": secretaria_user.perfil,
        "nome": secretaria_user.nome
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def aluno_user(db_session: Session) -> Usuario:
    """Cria e retorna um usuário ALUNO persistido no banco de teste."""
    user = Usuario(
        nome="Aluno Gabriel",
        email="aluno.teste@gl4.edu",
        senha_hash=gerar_hash_senha("aluno123"),
        perfil=PerfilUsuario.ALUNO.value,
        ativo=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def aluno_headers(aluno_user: Usuario) -> dict[str, str]:
    """Retorna os headers de autorização Bearer para o perfil ALUNO."""
    token = criar_token_jwt({
        "sub": str(aluno_user.id),
        "email": aluno_user.email,
        "perfil": aluno_user.perfil,
        "nome": aluno_user.nome
    })
    return {"Authorization": f"Bearer {token}"}
