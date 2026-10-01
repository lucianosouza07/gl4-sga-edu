from sqlalchemy.orm import Session
from app.models.usuario import Usuario, PerfilUsuario
from app.core.security import verificar_senha
from app.seeds.admin_seed import seed_admin_padrao
from app.seeds.alunos_teste import NOMES_DEMO, seed_alunos_teste
from app.models.aluno import Aluno, StatusAluno
from app.services.aluno_service import AlunoService


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


def test_seed_alunos_cria_registros_ativos_para_busca_e_paginacao(db_session: Session):
    total = seed_alunos_teste(db_session)
    service = AlunoService(db_session)
    primeira_pagina = service.listar_alunos(pagina=1, tamanho_pagina=10)
    busca_por_nome = service.listar_alunos(busca="Fernanda")
    busca_por_matricula = service.listar_alunos(busca="DEMO20260002")

    assert total == 30
    assert db_session.query(Aluno).filter(Aluno.status == StatusAluno.ATIVO.value).count() == len(NOMES_DEMO)
    assert db_session.query(Aluno).filter(Aluno.matricula == "DEMO20260001").one().nome_completo == NOMES_DEMO[0]
    assert db_session.query(Usuario).filter(Usuario.email == "aluno.demo.0001@example.com").one().perfil == PerfilUsuario.ALUNO.value
    assert len(primeira_pagina["itens"]) == 10
    assert primeira_pagina["total_paginas"] == 3
    assert [aluno.nome_completo for aluno in busca_por_nome["itens"]] == ["Fernanda Torres Macedo"]
    assert [aluno.matricula for aluno in busca_por_matricula["itens"]] == ["DEMO20260002"]


def test_seed_alunos_eh_idempotente_e_preserva_registros_existentes(db_session: Session):
    assert seed_alunos_teste(db_session) == len(NOMES_DEMO)
    primeira_matricula = db_session.query(Aluno).filter(Aluno.matricula == "DEMO20260001").one()
    primeira_matricula.nome_completo = "Nome alterado manualmente"
    db_session.commit()

    assert seed_alunos_teste(db_session) == 0
    assert db_session.query(Aluno).count() == len(NOMES_DEMO)
    assert db_session.query(Aluno).filter(Aluno.matricula == "DEMO20260001").one().nome_completo == "Nome alterado manualmente"
