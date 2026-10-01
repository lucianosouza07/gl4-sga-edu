import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models.aluno import Aluno, StatusAluno
from app.models.usuario import Usuario, PerfilUsuario
from app.schemas.aluno import AlunoCreate, AlunoUpdate
from app.core.security import gerar_hash_senha
from app.core.exceptions import RegistroJaExisteError, EntidadeNaoEncontradaError


class AlunoService:
    """Serviço com regras de negócio e persistência para a entidade Aluno."""

    def __init__(self, db: Session):
        self.db = db

    def criar_aluno(self, dados: AlunoCreate) -> Aluno:
        """
        Cria atômica e conjuntamente o Usuario (IAM) e o Aluno (domínio pedagógico).
        Valida previamente unicidade de matrícula, CPF e e-mail.
        """
        # 1. Validar se a matrícula já existe
        if self.db.query(Aluno).filter(Aluno.matricula == dados.matricula).first():
            raise RegistroJaExisteError(f"A matrícula '{dados.matricula}' já está cadastrada no sistema.")

        # 2. Validar se CPF já existe
        if self.db.query(Aluno).filter(Aluno.cpf == dados.cpf).first():
            raise RegistroJaExisteError("O CPF informado já está cadastrado.")

        # 3. Validar se E-mail de usuário já existe
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

            # 5. Criação do Aluno vinculado ao Usuario
            novo_aluno = Aluno(
                usuario_id=novo_usuario.id,
                matricula=dados.matricula,
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

    def listar_alunos(
        self,
        busca: Optional[str] = None,
        apenas_ativos: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> list[Aluno]:
        """Lista alunos com suporte a filtro de busca por nome ou matrícula e paginação."""
        query = self.db.query(Aluno)
        if apenas_ativos:
            query = query.filter(Aluno.status == StatusAluno.ATIVO.value)
        if busca:
            termo = f"%{busca}%"
            query = query.filter(
                (Aluno.nome_completo.ilike(termo)) | (Aluno.matricula.ilike(termo))
            )
        return query.order_by(Aluno.nome_completo).offset(skip).limit(limit).all()

    def obter_aluno_por_id(self, aluno_id: uuid.UUID | str) -> Aluno:
        """Obtém um aluno pelo seu identificador único UUID."""
        if isinstance(aluno_id, str):
            aluno_id = uuid.UUID(aluno_id)

        aluno = self.db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not aluno:
            raise EntidadeNaoEncontradaError(f"Aluno com ID '{aluno_id}' não encontrado.")
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
