import math
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from app.models.aluno import Aluno, StatusAluno
from app.models.sequencia_matricula import SequenciaMatricula
from app.models.usuario import Usuario, PerfilUsuario
from app.schemas.aluno import AlunoCreate, AlunoUpdate
from app.core.security import gerar_hash_senha
from app.core.exceptions import RegistroJaExisteError, EntidadeNaoEncontradaError


def periodo_matricula_atual() -> tuple[int, int]:
    """Obtém o ano e o semestre civil no fuso horário da instituição."""
    agora = datetime.now(ZoneInfo("America/Bahia"))
    return agora.year, 1 if agora.month <= 6 else 2


class AlunoService:
    """Serviço com regras de negócio e persistência para a entidade Aluno."""

    def __init__(self, db: Session):
        self.db = db

    def criar_aluno(self, dados: AlunoCreate) -> Aluno:
        """
        Cria atômica e conjuntamente o Usuario (IAM) e o Aluno (domínio pedagógico).
        Gera a matrícula e valida previamente a unicidade de CPF e e-mail.
        """
        # 1. Validar se CPF já existe
        if self.db.query(Aluno).filter(Aluno.cpf == dados.cpf).first():
            raise RegistroJaExisteError("O CPF informado já está cadastrado.")

        # 2. Validar se E-mail de usuário já existe
        if self.db.query(Usuario).filter(Usuario.email.ilike(dados.email)).first():
            raise RegistroJaExisteError("O e-mail informado já possui uma conta de acesso.")

        try:
            # 4. Criação do Usuario (com perfil ALUNO e senha inicial)
            senha_inicial = dados.senha_inicial if dados.senha_inicial else "Mudar@123"
            novo_usuario = Usuario(
                nome=dados.nome_completo,
                email=dados.email,
                senha_hash=gerar_hash_senha(senha_inicial),
                perfil=PerfilUsuario.ALUNO.value,
                ativo=True
            )
            self.db.add(novo_usuario)
            self.db.flush()  # Gera novo_usuario.id sem comitar a transação

            ano, semestre = periodo_matricula_atual()
            numero = self._proximo_numero_matricula(ano, semestre)
            matricula = f"{ano}{semestre}{numero:04d}"

            # 5. Criação do Aluno vinculado ao Usuario
            novo_aluno = Aluno(
                usuario_id=novo_usuario.id,
                matricula=matricula,
                nome_completo=dados.nome_completo,
                cpf=dados.cpf,
                email=dados.email,
                telefone=dados.telefone,
                data_nascimento=dados.data_nascimento,
                status=StatusAluno.ATIVO.value
            )
            self.db.add(novo_aluno)

            # 6. Commit atômico
            self.db.commit()
            self.db.refresh(novo_aluno)
            return novo_aluno

        except Exception:
            self.db.rollback()
            raise

    def _proximo_numero_matricula(self, ano: int, semestre: int) -> int:
        """Reserva atomicamente o próximo número, preservando matrículas anteriores."""
        dialect = self.db.get_bind().dialect.name
        if dialect == "sqlite":
            insert = sqlite_insert
        elif dialect == "postgresql":
            insert = postgresql_insert
        else:
            raise RuntimeError(f"Geração de matrícula não suportada para o banco '{dialect}'.")

        numero_inicial = 1
        if self.db.get(SequenciaMatricula, (ano, semestre)) is None:
            prefixo = f"{ano}{semestre}"
            matriculas = self.db.query(Aluno.matricula).filter(
                Aluno.matricula.startswith(prefixo)
            ).all()
            numeros = [
                int(matricula[len(prefixo):])
                for (matricula,) in matriculas
                if matricula[len(prefixo):].isascii() and matricula[len(prefixo):].isdigit()
            ]
            numero_inicial = max(numeros, default=0) + 1

        comando = insert(SequenciaMatricula).values(
            ano=ano,
            semestre=semestre,
            ultimo_numero=numero_inicial,
        )
        comando = comando.on_conflict_do_update(
            index_elements=[SequenciaMatricula.ano, SequenciaMatricula.semestre],
            set_={
                "ultimo_numero": SequenciaMatricula.ultimo_numero + 1,
            },
        ).returning(SequenciaMatricula.ultimo_numero)
        return self.db.execute(comando).scalar_one()

    def listar_alunos(
        self,
        busca: Optional[str] = None,
        apenas_ativos: bool = True,
        pagina: int = 1,
        tamanho_pagina: int = 10,
    ) -> Dict[str, Any]:
        """Lista alunos com suporte a filtro de busca por nome ou matrícula e paginação padrão."""
        if pagina < 1:
            pagina = 1
        if tamanho_pagina < 1:
            tamanho_pagina = 10

        query = self.db.query(Aluno)
        if apenas_ativos:
            query = query.filter(Aluno.status == StatusAluno.ATIVO.value)
        if busca:
            termo = f"%{busca}%"
            query = query.filter(
                (Aluno.nome_completo.ilike(termo)) | (Aluno.matricula.ilike(termo))
            )

        total = query.count()
        total_paginas = math.ceil(total / tamanho_pagina) if total > 0 else 0
        offset = (pagina - 1) * tamanho_pagina
        itens = query.order_by(Aluno.nome_completo).offset(offset).limit(tamanho_pagina).all()

        return {
            "itens": itens,
            "total": total,
            "pagina": pagina,
            "tamanho_pagina": tamanho_pagina,
            "total_paginas": total_paginas,
        }

    def obter_aluno_por_id(self, aluno_id: uuid.UUID | str) -> Aluno:
        """Obtém um aluno pelo seu identificador único UUID."""
        if isinstance(aluno_id, str):
            aluno_id = uuid.UUID(aluno_id)

        aluno = self.db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not aluno:
            raise EntidadeNaoEncontradaError(f"Aluno com ID '{aluno_id}' não encontrado.")
        return aluno

    def obter_aluno_por_usuario_id(self, usuario_id: uuid.UUID) -> Aluno:
        """Obtém exclusivamente o Aluno vinculado ao Usuário informado."""
        aluno = self.db.query(Aluno).filter(Aluno.usuario_id == usuario_id).first()
        if not aluno:
            raise EntidadeNaoEncontradaError("Aluno vinculado ao usuário não encontrado.")
        return aluno

    def inativar_aluno(self, aluno_id: uuid.UUID | str) -> Aluno:
        """
        Executa soft delete: altera status do Aluno para INATIVO e desativa o login do Usuario.
        """
        aluno = self.obter_aluno_por_id(aluno_id)
        aluno.status = StatusAluno.INATIVO.value
        if aluno.usuario:
            aluno.usuario.ativo = False

        self.db.commit()
        self.db.refresh(aluno)
        return aluno

    def reativar_aluno(self, aluno_id: uuid.UUID | str) -> Aluno:
        """Reativa o Aluno e restaura o acesso do Usuario vinculado."""
        aluno = self.obter_aluno_por_id(aluno_id)
        aluno.status = StatusAluno.ATIVO.value
        if aluno.usuario:
            aluno.usuario.ativo = True

        self.db.commit()
        self.db.refresh(aluno)
        return aluno

    def atualizar_aluno(self, aluno_id: uuid.UUID | str, dados: AlunoUpdate) -> Aluno:
        """Atualiza informações cadastrais do aluno."""
        aluno = self.obter_aluno_por_id(aluno_id)

        if dados.nome_completo is not None:
            aluno.nome_completo = dados.nome_completo
            if aluno.usuario:
                aluno.usuario.nome = dados.nome_completo
        if dados.telefone is not None:
            aluno.telefone = dados.telefone
        if dados.data_nascimento is not None:
            aluno.data_nascimento = dados.data_nascimento
        if dados.status is not None:
            aluno.status = dados.status

        self.db.commit()
        self.db.refresh(aluno)
        return aluno
