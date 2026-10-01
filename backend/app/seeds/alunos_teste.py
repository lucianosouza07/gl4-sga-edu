from datetime import date

from sqlalchemy.orm import Session

from app.models.aluno import Aluno
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
)


def seed_alunos_teste(db: Session) -> int:
    """Cria alunos fictícios ativos para exercitar paginação e busca.

    CPFs e e-mails usam identificadores de demonstração fixos. A matrícula é
    gerada pelo serviço e registros com e-mail já existente são preservados.
    Retorna o número de alunos criados nesta execução.
    """
    service = AlunoService(db)
    criados = 0

    for indice, nome in enumerate(NOMES_DEMO, start=1):
        email = f"aluno.demo.{indice:04d}@example.com"
        if db.query(Aluno).filter(Aluno.email == email).first():
            continue

        service.criar_aluno(
            AlunoCreate(
                nome_completo=nome,
                cpf=f"900.000.000-{indice:02d}",
                email=email,
                data_nascimento=date(
                    2000 + (indice % 8),
                    (indice % 12) + 1,
                    (indice % 27) + 1,
                ),
                telefone=f"1190000{indice:04d}",
            )
        )
        criados += 1

    return criados


if __name__ == "__main__":
    init_db()
    with SessionLocal() as session:
        total = seed_alunos_teste(session)
        print(
            f"Alunos de demonstração criados: {total} "
            f"(de {len(NOMES_DEMO)} previstos)."
        )
