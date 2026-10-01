from datetime import date, datetime, timezone
import math

from sqlalchemy.orm import Session

from app.models.aluno import Aluno, StatusAluno
from app.models.usuario import Usuario
from app.schemas.aluno import AlunoCreate
from app.services.aluno_service import AlunoService
from app.database.session import SessionLocal, init_db


NOMES_DEMO = (
    "Ana Beatriz Costa", "Bruno Henrique Lima", "Camila Ferreira Souza",
    "Daniel Oliveira Santos", "Eduarda Martins Rocha", "Felipe Alves Ribeiro",
    "Gabriela Nunes Cardoso", "Heitor Carvalho Mendes", "Isabela Gomes Freitas",
    "João Pedro Barros", "Karen Lopes Monteiro", "Lucas Araújo Teixeira",
    "Mariana Batista Correia", "Nicolas Moreira Campos", "Olivia Dias Fernandes",
    "Pedro Henrique Machado", "Quezia Silva Andrade", "Rafael Cunha Pereira",
    "Sofia Almeida Castro", "Thiago Melo Vieira", "Ursula Ramos Cavalcante",
    "Vinicius Reis Farias", "Wesley Pires Santana", "Yasmin Moura Peixoto",
    "Zeca Fonseca Brito", "Alice Ribeiro Dantas", "Caio Mendes Leal",
    "Fernanda Torres Macedo", "Igor Carvalho Neves", "Luana Prado Azevedo",
    "Marcos Vinicius Borges", "Natalia Correia Duarte", "Otavio Silveira Ramos",
    "Patricia Guimaraes Vale", "Renan Castro Nogueira", "Sabrina Fontes Dias",
    "Tomas Albuquerque Lins", "Vanessa Farias Paiva", "Wagner Siqueira Teles",
    "Beatriz Meireles Viana", "Claudio Roberto Moraes", "Debora Antunes Frota",
    "Eduardo Pimentel Rios", "Flavia Regina Guedes", "Guilherme Santos Maia",
    "Helena Vasconcelos Prado", "Juliana Portela Aguiar", "Leonardo Cunha Vasquez",
)

# Cronograma determinístico de criação cobrindo os últimos 12 meses (2025-10 até 2026-10)
CRONOGRAMA_CRIACAO = (
    # 2025 (ano anterior)
    (2025, 10, 14, 9, 30),
    (2025, 10, 22, 14, 15),
    (2025, 10, 29, 11, 45),
    (2025, 11, 8, 10, 20),
    (2025, 11, 18, 16, 50),
    (2025, 11, 25, 13, 10),
    (2025, 12, 5, 15, 30),
    (2025, 12, 15, 11, 0),
    # 2026 (ano corrente - distribuição mensal com picos de matrículas)
    (2026, 1, 10, 8, 30),
    (2026, 1, 15, 10, 15),
    (2026, 1, 19, 14, 40),
    (2026, 1, 22, 9, 20),
    (2026, 1, 26, 16, 10),
    (2026, 1, 29, 11, 35),
    (2026, 2, 3, 10, 0),
    (2026, 2, 9, 14, 25),
    (2026, 2, 16, 9, 50),
    (2026, 2, 20, 15, 15),
    (2026, 2, 25, 11, 40),
    (2026, 3, 4, 10, 30),
    (2026, 3, 12, 14, 10),
    (2026, 3, 19, 9, 15),
    (2026, 3, 27, 16, 45),
    (2026, 4, 7, 11, 20),
    (2026, 4, 15, 14, 35),
    (2026, 4, 24, 10, 50),
    (2026, 5, 5, 9, 30),
    (2026, 5, 13, 15, 45),
    (2026, 5, 20, 11, 10),
    (2026, 5, 28, 16, 25),
    (2026, 6, 8, 10, 15),
    (2026, 6, 17, 14, 50),
    (2026, 6, 25, 9, 40),
    (2026, 7, 3, 11, 30),
    (2026, 7, 10, 15, 15),
    (2026, 7, 16, 9, 20),
    (2026, 7, 23, 14, 45),
    (2026, 7, 30, 10, 10),
    (2026, 8, 6, 16, 30),
    (2026, 8, 14, 11, 15),
    (2026, 8, 21, 9, 50),
    (2026, 8, 28, 15, 40),
    (2026, 9, 4, 10, 25),
    (2026, 9, 11, 14, 10),
    (2026, 9, 18, 9, 35),
    (2026, 9, 25, 16, 0),
    (2026, 10, 1, 8, 15),
    (2026, 10, 1, 9, 30),
)

# Índices para distribuição realista de status
INDICES_INATIVOS = {5, 12, 19, 26, 33, 40, 44, 47}
INDICES_TRANCADOS = {8, 22, 36, 46}
INDICES_FORMADOS = {15, 30}


def _determinar_status(indice: int) -> StatusAluno:
    if indice in INDICES_INATIVOS:
        return StatusAluno.INATIVO
    if indice in INDICES_TRANCADOS:
        return StatusAluno.TRANCADO
    if indice in INDICES_FORMADOS:
        return StatusAluno.FORMADO
    return StatusAluno.ATIVO


def seed_alunos_teste(db: Session, *, force_refresh_existing: bool = False) -> int:
    """Cria alunos fictícios com dados temporais e status diversificados.

    Permite testar de forma completa o Dashboard institucional (gráficos de
    novas matrículas por mês, distribuição por status e últimos cadastros)
    e a paginação/busca de alunos.

    Quando `force_refresh_existing=True`, atualiza registros demo já existentes
    com as datas e status do cronograma, garantindo variedade imediata no banco local.
    Retorna o número de alunos novos inseridos.
    """
    service = AlunoService(db)
    criados = 0

    for indice, nome in enumerate(NOMES_DEMO, start=1):
        email = f"aluno.demo.{indice:04d}@example.com"
        cpf = f"900.000.{indice:03d}-{(indice % 90) + 10:02d}"
        cronograma = CRONOGRAMA_CRIACAO[indice - 1]
        data_criacao = datetime(*cronograma, tzinfo=timezone.utc).replace(tzinfo=None)
        status_desejado = _determinar_status(indice)

        aluno_existente = db.query(Aluno).filter(Aluno.email == email).first()
        if aluno_existente:
            if force_refresh_existing:
                aluno_existente.criado_em = data_criacao
                aluno_existente.status = status_desejado.value
                if aluno_existente.usuario:
                    aluno_existente.usuario.ativo = (status_desejado != StatusAluno.INATIVO)
            continue

        novo_aluno = service.criar_aluno(
            AlunoCreate(
                nome_completo=nome,
                cpf=cpf,
                email=email,
                data_nascimento=date(
                    1998 + (indice % 9),
                    (indice % 12) + 1,
                    (indice % 27) + 1,
                ),
                telefone=f"1190000{indice:04d}",
            )
        )

        # Aplica a data retroativa e o status definido no cronograma
        novo_aluno.criado_em = data_criacao
        novo_aluno.status = status_desejado.value
        if novo_aluno.usuario:
            novo_aluno.usuario.ativo = (status_desejado != StatusAluno.INATIVO)

        criados += 1

    db.commit()
    return criados


if __name__ == "__main__":
    init_db()
    with SessionLocal() as session:
        novos = seed_alunos_teste(session, force_refresh_existing=True)
        total_banco = session.query(Aluno).count()
        total_ativos = session.query(Aluno).filter(Aluno.status == StatusAluno.ATIVO.value).count()
        total_inativos = session.query(Aluno).filter(Aluno.status == StatusAluno.INATIVO.value).count()
        total_trancados = session.query(Aluno).filter(Aluno.status == StatusAluno.TRANCADO.value).count()
        total_formados = session.query(Aluno).filter(Aluno.status == StatusAluno.FORMADO.value).count()

        print(f"Seed de alunos executado:")
        print(f" - Novos inseridos: {novos}")
        print(f" - Total de alunos no banco: {total_banco}")
        print(f" - Ativos: {total_ativos} | Inativos: {total_inativos} | Trancados: {total_trancados} | Formados: {total_formados}")
