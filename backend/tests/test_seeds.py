from datetime import datetime
import math
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
    segundo_aluno = db_session.query(Aluno).filter(Aluno.email == "aluno.demo.0002@example.com").one()
    busca_por_matricula = service.listar_alunos(busca=segundo_aluno.matricula)

    assert total == len(NOMES_DEMO)
    ativos = db_session.query(Aluno).filter(Aluno.status == StatusAluno.ATIVO.value).count()
    inativos = db_session.query(Aluno).filter(Aluno.status == StatusAluno.INATIVO.value).count()
    trancados = db_session.query(Aluno).filter(Aluno.status == StatusAluno.TRANCADO.value).count()
    formados = db_session.query(Aluno).filter(Aluno.status == StatusAluno.FORMADO.value).count()

    assert ativos == 34
    assert inativos == 8
    assert trancados == 4
    assert formados == 2
    assert ativos + inativos + trancados + formados == len(NOMES_DEMO)

    # Valida distribuição temporal nos anos de 2025 e 2026 para os gráficos do dashboard
    registros_2025 = db_session.query(Aluno).filter(Aluno.criado_em < datetime(2026, 1, 1)).count()
    registros_2026 = db_session.query(Aluno).filter(Aluno.criado_em >= datetime(2026, 1, 1)).count()
    assert registros_2025 == 8
    assert registros_2026 == 40

    primeira_matricula = db_session.query(Aluno).filter(Aluno.email == "aluno.demo.0001@example.com").one()
    assert primeira_matricula.nome_completo == NOMES_DEMO[0]
    assert len(primeira_matricula.matricula) >= 9
    assert db_session.query(Usuario).filter(Usuario.email == "aluno.demo.0001@example.com").one().perfil == PerfilUsuario.ALUNO.value
    assert len(primeira_pagina["itens"]) == 10
    assert primeira_pagina["total_paginas"] == math.ceil(ativos / 10)
    assert [aluno.nome_completo for aluno in busca_por_nome["itens"]] == ["Fernanda Torres Macedo"]
    assert [aluno.matricula for aluno in busca_por_matricula["itens"]] == [segundo_aluno.matricula]


def test_seed_alunos_eh_idempotente_e_preserva_registros_existentes(db_session: Session):
    assert seed_alunos_teste(db_session) == len(NOMES_DEMO)
    primeira_matricula = db_session.query(Aluno).filter(Aluno.email == "aluno.demo.0001@example.com").one()
    primeira_matricula.nome_completo = "Nome alterado manualmente"
    db_session.commit()

    assert seed_alunos_teste(db_session) == 0
    assert db_session.query(Aluno).count() == len(NOMES_DEMO)
    assert db_session.query(Aluno).filter(Aluno.email == "aluno.demo.0001@example.com").one().nome_completo == "Nome alterado manualmente"
