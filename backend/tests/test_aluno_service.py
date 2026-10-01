import pytest
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from app.models.usuario import Usuario, PerfilUsuario
from app.models.aluno import StatusAluno
from app.models.sequencia_matricula import SequenciaMatricula
from app.schemas.aluno import AlunoCreate, AlunoUpdate
from app.core.security import verificar_senha
from app.core.exceptions import RegistroJaExisteError, EntidadeNaoEncontradaError
from app.services.aluno_service import AlunoService, periodo_matricula_atual


@pytest.mark.parametrize("instante, esperado", [
    (datetime(2026, 1, 1, 3, tzinfo=timezone.utc), (2026, 1)),
    (datetime(2026, 7, 1, 2, 59, tzinfo=timezone.utc), (2026, 1)),
    (datetime(2026, 7, 1, 3, tzinfo=timezone.utc), (2026, 2)),
    (datetime(2027, 1, 1, 2, 59, tzinfo=timezone.utc), (2026, 2)),
])
def test_periodo_matricula_segue_calendario_local(monkeypatch, instante, esperado):
    class DataFixa(datetime):
        @classmethod
        def now(cls, tz=None):
            return instante.astimezone(tz)

    monkeypatch.setattr("app.services.aluno_service.datetime", DataFixa)
    assert periodo_matricula_atual() == esperado


def test_criar_aluno_com_sucesso_transacao_atomica(db_session: Session, monkeypatch):
    monkeypatch.setattr("app.services.aluno_service.periodo_matricula_atual", lambda: (2026, 2))
    service = AlunoService(db_session)
    dados = AlunoCreate(
        nome_completo="Carlos Eduardo",
        cpf="12345678901",
        email="carlos@gl4.edu",
        telefone="11999998888",
        data_nascimento=date(2004, 3, 15)
    )

    novo_aluno = service.criar_aluno(dados)

    assert novo_aluno.id is not None
    assert novo_aluno.matricula == "202620001"
    assert novo_aluno.status == StatusAluno.ATIVO.value
    assert novo_aluno.usuario_id is not None

    # Verifica se a entidade Usuario correspondente foi criada com os dados corretos
    usuario = db_session.query(Usuario).filter(Usuario.id == novo_aluno.usuario_id).first()
    assert usuario is not None
    assert usuario.email == "carlos@gl4.edu"
    assert usuario.nome == "Carlos Eduardo"
    assert usuario.perfil == PerfilUsuario.ALUNO.value
    assert usuario.ativo is True
    # Senha padrão Mudar@123
    assert verificar_senha("Mudar@123", usuario.senha_hash) is True


def test_criar_aluno_com_senha_inicial_customizada(db_session: Session, monkeypatch):
    monkeypatch.setattr("app.services.aluno_service.periodo_matricula_atual", lambda: (2026, 2))
    service = AlunoService(db_session)
    dados = AlunoCreate(
        nome_completo="Beatriz Ramos",
        cpf="98765432100",
        email="beatriz@gl4.edu",
        data_nascimento=date(2005, 7, 20),
        senha_inicial="MinhaSenhaForte#2026"
    )

    novo_aluno = service.criar_aluno(dados)
    usuario = db_session.query(Usuario).filter(Usuario.id == novo_aluno.usuario_id).first()
    assert usuario is not None
    assert verificar_senha("MinhaSenhaForte#2026", usuario.senha_hash) is True


def test_criar_alunos_incrementa_matricula_gerada(db_session: Session, monkeypatch):
    monkeypatch.setattr("app.services.aluno_service.periodo_matricula_atual", lambda: (2026, 2))
    service = AlunoService(db_session)
    dados1 = AlunoCreate(
        nome_completo="Aluno Um",
        cpf="11111111111",
        email="aluno1@gl4.edu",
        data_nascimento=date(2002, 1, 1)
    )
    service.criar_aluno(dados1)

    dados2 = AlunoCreate(
        nome_completo="Aluno Dois",
        cpf="22222222222",
        email="aluno2@gl4.edu",
        data_nascimento=date(2002, 1, 1)
    )
    segundo_aluno = service.criar_aluno(dados2)
    assert segundo_aluno.matricula == "202620002"


def test_sequencia_reinicia_por_semestre_e_nao_reutiliza_matricula_removida(
    db_session: Session, monkeypatch
):
    periodo = [2026, 1]
    monkeypatch.setattr("app.services.aluno_service.periodo_matricula_atual", lambda: tuple(periodo))
    service = AlunoService(db_session)

    primeiro_semestre = service.criar_aluno(AlunoCreate(
        nome_completo="Aluno Primeiro Semestre",
        cpf="10111111111",
        email="segundo.semestre@gl4.edu",
        data_nascimento=date(2002, 1, 1),
    ))
    assert primeiro_semestre.matricula == "202610001"

    periodo[:] = [2026, 2]
    segundo_semestre = service.criar_aluno(AlunoCreate(
        nome_completo="Aluno Segundo Semestre",
        cpf="20222222222",
        email="primeiro.semestre@gl4.edu",
        data_nascimento=date(2002, 1, 1),
    ))
    assert segundo_semestre.matricula == "202620001"

    db_session.delete(segundo_semestre)
    db_session.commit()
    proximo_aluno = service.criar_aluno(AlunoCreate(
        nome_completo="Aluno Após Remoção",
        cpf="30333333333",
        email="apos.remocao@gl4.edu",
        data_nascimento=date(2002, 1, 1),
    ))
    assert proximo_aluno.matricula == "202620002"

    periodo[:] = [2027, 1]
    novo_ano = service.criar_aluno(AlunoCreate(
        nome_completo="Aluno Novo Ano",
        cpf="31333333333",
        email="novo.ano@gl4.edu",
        data_nascimento=date(2002, 1, 1),
    ))
    assert novo_ano.matricula == "202710001"


def test_inicia_contador_apos_matriculas_preexistentes(db_session: Session, monkeypatch):
    monkeypatch.setattr("app.services.aluno_service.periodo_matricula_atual", lambda: (2026, 2))
    service = AlunoService(db_session)
    anterior = service.criar_aluno(AlunoCreate(
        nome_completo="Aluno Anterior",
        cpf="41444444444",
        email="anterior@gl4.edu",
        data_nascimento=date(2002, 1, 1),
    ))
    # Simula um banco anterior à introdução da tabela de sequências.
    db_session.query(SequenciaMatricula).delete()
    db_session.commit()

    novo = service.criar_aluno(AlunoCreate(
        nome_completo="Aluno Posterior",
        cpf="42444444444",
        email="posterior@gl4.edu",
        data_nascimento=date(2002, 1, 1),
    ))

    assert anterior.matricula == "202620001"
    assert novo.matricula == "202620002"


def test_matricula_expande_sufixo_sem_limite_de_quatro_digitos(db_session: Session, monkeypatch):
    monkeypatch.setattr("app.services.aluno_service.periodo_matricula_atual", lambda: (2026, 2))
    db_session.add(SequenciaMatricula(ano=2026, semestre=2, ultimo_numero=9999))
    db_session.commit()

    aluno = AlunoService(db_session).criar_aluno(AlunoCreate(
        nome_completo="Aluno Acima do Limite Inicial",
        cpf="40444444444",
        email="acima.limite@gl4.edu",
        data_nascimento=date(2002, 1, 1),
    ))

    assert aluno.matricula == "2026210000"


def test_criar_aluno_cpf_duplicado_lanca_excecao(db_session: Session):
    service = AlunoService(db_session)
    dados1 = AlunoCreate(
        nome_completo="Aluno Três",
        cpf="33333333333",
        email="aluno3@gl4.edu",
        data_nascimento=date(2002, 1, 1)
    )
    service.criar_aluno(dados1)

    dados2 = AlunoCreate(
        nome_completo="Aluno Quatro",
        cpf="33333333333",  # Mesmo CPF
        email="aluno4@gl4.edu",
        data_nascimento=date(2002, 1, 1)
    )
    with pytest.raises(RegistroJaExisteError, match="O CPF informado já está cadastrado"):
        service.criar_aluno(dados2)


def test_criar_aluno_email_duplicado_lanca_excecao(db_session: Session):
    service = AlunoService(db_session)
    dados1 = AlunoCreate(
        nome_completo="Aluno Cinco",
        cpf="55555555555",
        email="alunocomum@gl4.edu",
        data_nascimento=date(2002, 1, 1)
    )
    service.criar_aluno(dados1)

    dados2 = AlunoCreate(
        nome_completo="Aluno Seis",
        cpf="66666666666",
        email="alunocomum@gl4.edu",  # Mesmo E-mail
        data_nascimento=date(2002, 1, 1)
    )
    with pytest.raises(RegistroJaExisteError, match="O e-mail informado já possui uma conta de acesso"):
        service.criar_aluno(dados2)


def test_listar_alunos_com_filtro_busca(db_session: Session, monkeypatch):
    monkeypatch.setattr("app.services.aluno_service.periodo_matricula_atual", lambda: (2026, 1))
    service = AlunoService(db_session)
    service.criar_aluno(AlunoCreate(
        nome_completo="Fernanda Silva",
        cpf="10101010101",
        email="fernanda@gl4.edu",
        data_nascimento=date(2001, 1, 1)
    ))
    service.criar_aluno(AlunoCreate(
        nome_completo="Gabriel Souza",
        cpf="20202020202",
        email="gabriel@gl4.edu",
        data_nascimento=date(2001, 2, 2)
    ))

    # Busca por nome
    resultados = service.listar_alunos(busca="Fernanda")
    assert resultados["total"] == 1
    assert len(resultados["itens"]) == 1
    assert resultados["itens"][0].matricula == "202610001"

    # Busca por matrícula
    resultados_matr = service.listar_alunos(busca="002")
    assert resultados_matr["total"] == 1
    assert len(resultados_matr["itens"]) == 1
    assert resultados_matr["itens"][0].nome_completo == "Gabriel Souza"


def test_listar_alunos_paginacao(db_session: Session, monkeypatch):
    monkeypatch.setattr("app.services.aluno_service.periodo_matricula_atual", lambda: (2026, 1))
    service = AlunoService(db_session)
    for i in range(1, 16):
        service.criar_aluno(AlunoCreate(
            nome_completo=f"Aluno Teste {i:02d}",
            cpf=f"{i:011d}",
            email=f"aluno{i}@gl4.edu",
            data_nascimento=date(2000, 1, 1)
        ))

    # Página 1 com 10 por página
    p1 = service.listar_alunos(pagina=1, tamanho_pagina=10)
    assert p1["total"] == 15
    assert len(p1["itens"]) == 10
    assert p1["pagina"] == 1
    assert p1["tamanho_pagina"] == 10
    assert p1["total_paginas"] == 2

    # Página 2 com 10 por página
    p2 = service.listar_alunos(pagina=2, tamanho_pagina=10)
    assert p2["total"] == 15
    assert len(p2["itens"]) == 5
    assert p2["pagina"] == 2
    assert p2["total_paginas"] == 2


def test_inativar_aluno_soft_delete(db_session: Session):
    service = AlunoService(db_session)
    aluno = service.criar_aluno(AlunoCreate(
        nome_completo="Marcos Vinicius",
        cpf="30303030303",
        email="marcos@gl4.edu",
        data_nascimento=date(2000, 5, 10)
    ))

    # Inativa o aluno
    aluno_inativado = service.inativar_aluno(aluno.id)
    assert aluno_inativado.status == StatusAluno.INATIVO.value

    # Verifica se o login associado também foi inativado
    usuario = db_session.query(Usuario).filter(Usuario.id == aluno.usuario_id).first()
    assert usuario.ativo is False

    # Na listagem padrão (apenas ativos), não deve aparecer
    ativos = service.listar_alunos(apenas_ativos=True)
    assert not any(a.id == aluno.id for a in ativos["itens"])

    # Na listagem com apenas_ativos=False, deve aparecer
    todos = service.listar_alunos(apenas_ativos=False)
    assert any(a.id == aluno.id for a in todos["itens"])


def test_obter_aluno_inexistente_lanca_excecao(db_session: Session):
    import uuid
    service = AlunoService(db_session)
    id_inexistente = uuid.uuid4()

    with pytest.raises(EntidadeNaoEncontradaError, match="não encontrado"):
        service.obter_aluno_por_id(id_inexistente)


def test_atualizar_aluno_com_sucesso(db_session: Session):
    service = AlunoService(db_session)
    aluno = service.criar_aluno(AlunoCreate(
        nome_completo="Nome Antigo",
        cpf="40404040404",
        email="antigo@gl4.edu",
        data_nascimento=date(2001, 1, 1)
    ))

    atualizado = service.atualizar_aluno(
        aluno.id,
        AlunoUpdate(nome_completo="Nome Atualizado", telefone="11988887777")
    )

    assert atualizado.nome_completo == "Nome Atualizado"
    assert atualizado.telefone == "11988887777"
    assert atualizado.usuario.nome == "Nome Atualizado"
