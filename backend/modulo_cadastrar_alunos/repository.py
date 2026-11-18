"""Persistência relacional SQLite transacional para cadastro e gestão de alunos (SGA-15)."""

from datetime import datetime, timezone
import json
import os
import sqlite3
import threading
from typing import Any, Optional

try:
    from .schemas import PERFIL_ALUNO_ID, PERFIL_ALUNO_NOME
except ImportError:
    from schemas import PERFIL_ALUNO_ID, PERFIL_ALUNO_NOME

PERFIS_INICIAIS: tuple[tuple[int, str, str], ...] = (
    (1, "Aluno", "Acesso ao portal discente, matrícula online, consulta de notas, frequência, requerimentos e financeiro"),
    (2, "Professor", "Acesso ao portal docente, lançamento de notas, frequência, plano de ensino, materiais e comunicados"),
    (3, "Secretaria", "Gestão acadêmica, matrizes curriculares, turmas, salas, movimentação discente e acervo digital MEC"),
    (4, "Financeiro", "Gestão de contratos educacionais, emissão de boletos/Pix, bolsas, descontos e conciliação bancária"),
    (5, "Admin", "Governança de TI, administração de perfis RBAC, MFA, consentimento LGPD e trilhas de auditoria"),
)

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Perfil (
    id_perfil INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_perfil VARCHAR(50) NOT NULL UNIQUE,
    descricao VARCHAR(255) NULL
);

CREATE TABLE IF NOT EXISTS Usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    login VARCHAR(255) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    perfil_RBAC INTEGER NOT NULL,
    tokenMFA VARCHAR(45) NULL,
    statusCONTA INTEGER NOT NULL DEFAULT 1,
    dadosIdentificacao VARCHAR(255) NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_Usuario_Perfil
        FOREIGN KEY (perfil_RBAC)
        REFERENCES Perfil (id_perfil)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Departamento (
    id_departamento INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL UNIQUE,
    sigla VARCHAR(15) NOT NULL UNIQUE,
    ativo BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Curso (
    id_curso INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_mec VARCHAR(30) NOT NULL UNIQUE,
    nome VARCHAR(120) NOT NULL UNIQUE,
    grau_academico VARCHAR(40) NOT NULL,
    modalidade VARCHAR(30) NOT NULL DEFAULT 'PRESENCIAL',
    carga_horaria_total INTEGER NOT NULL,
    duracao_semestres INTEGER NOT NULL,
    departamento_id INTEGER NOT NULL,
    coordenador_id INTEGER NULL,
    ativo BOOLEAN NOT NULL DEFAULT 1,
    CONSTRAINT fk_Curso_Departamento
        FOREIGN KEY (departamento_id)
        REFERENCES Departamento (id_departamento)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Aluno (
    matricula INTEGER PRIMARY KEY,
    Usuario_id_usuario INTEGER NOT NULL UNIQUE,
    nome VARCHAR(120) NULL,
    email VARCHAR(120) NULL UNIQUE,
    cpf VARCHAR(14) NULL UNIQUE,
    telefone VARCHAR(20) NULL,
    data_nascimento DATE NULL,
    curso_id INTEGER NULL,
    status_academico VARCHAR(30) NOT NULL DEFAULT 'ATIVO',
    ira DECIMAL(4,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT fk_Aluno_Usuario
        FOREIGN KEY (Usuario_id_usuario)
        REFERENCES Usuario (id_usuario)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_Aluno_Curso
        FOREIGN KEY (curso_id)
        REFERENCES Curso (id_curso)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS LogAuditoriaSistema (
    id_auditoria INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NULL,
    entidade_afetada VARCHAR(80) NOT NULL,
    id_registro_afetado VARCHAR(64) NULL,
    acao VARCHAR(50) NOT NULL,
    dados_anteriores TEXT NULL,
    dados_novos TEXT NULL,
    ip_origem VARCHAR(45) NOT NULL,
    data_hora DATETIME NOT NULL,
    CONSTRAINT fk_LogAuditoriaSistema_Usuario
        FOREIGN KEY (usuario_id)
        REFERENCES Usuario (id_usuario)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);
"""


def criar_conexao(db_path: str = ":memory:") -> sqlite3.Connection:
    """Abre conexão SQLite com chaves estrangeiras ativadas e suporte multi-thread."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def inicializar_esquema(conn: sqlite3.Connection) -> None:
    """Cria as tabelas relacionais do domínio e semeia os 5 perfis RBAC e curso padrão."""
    conn.executescript(SCHEMA_SQL)
    conn.executemany(
        """
        INSERT INTO Perfil (id_perfil, nome_perfil, descricao)
        VALUES (?, ?, ?)
        ON CONFLICT(id_perfil) DO UPDATE SET
            nome_perfil = excluded.nome_perfil,
            descricao = excluded.descricao;
        """,
        PERFIS_INICIAIS,
    )
    conn.execute(
        """
        INSERT INTO Departamento (id_departamento, codigo, nome, sigla, ativo)
        VALUES (1, 'DCET-I', 'Departamento de Ciências Exatas e da Terra I', 'DCET1', 1)
        ON CONFLICT(id_departamento) DO NOTHING;
        """
    )
    conn.execute(
        """
        INSERT INTO Curso (
            id_curso, codigo_mec, nome, grau_academico, modalidade,
            carga_horaria_total, duracao_semestres, departamento_id, ativo
        )
        VALUES (1, 'MEC-SI-2026', 'Sistemas de Informação', 'Bacharelado', 'PRESENCIAL', 3000, 8, 1, 1)
        ON CONFLICT(id_curso) DO NOTHING;
        """
    )
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.commit()


def _parse_senha_provisoria(dados_identificacao: Optional[str]) -> bool:
    if not dados_identificacao:
        return False
    try:
        parsed = json.loads(dados_identificacao)
        return bool(parsed.get("senha_provisoria", False))
    except (ValueError, TypeError, AttributeError):
        return False


class AlunoRepository:
    """Repositório transacional SQLite para cadastro de alunos e trilha de auditoria."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._lock = threading.RLock()
        self.conn = criar_conexao(db_path)
        inicializar_esquema(self.conn)

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    def buscar_usuario_por_id(self, usuario_id: int) -> Optional[dict[str, Any]]:
        """Busca usuário por ID com o nome do perfil RBAC associado."""
        with self._lock:
            row = self.conn.execute(
                """
                SELECT u.id_usuario, u.login, u.senha_hash, u.perfil_RBAC,
                       u.statusCONTA, u.dadosIdentificacao, u.criado_em,
                       p.nome_perfil
                FROM Usuario u
                JOIN Perfil p ON p.id_perfil = u.perfil_RBAC
                WHERE u.id_usuario = ?
                """,
                (usuario_id,),
            ).fetchone()
            return dict(row) if row else None

    def inserir_usuario_seed(
        self,
        login: str,
        senha_hash: str,
        perfil_id: int,
        status_conta: int = 1,
        dados_identificacao: Optional[str] = None,
    ) -> int:
        """Insere conta de usuário diretamente (útil para seed de operadores e testes)."""
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Usuario (login, senha_hash, perfil_RBAC, statusCONTA, dadosIdentificacao)
                VALUES (?, ?, ?, ?, ?)
                """,
                (login, senha_hash, perfil_id, status_conta, dados_identificacao),
            )
            self.conn.commit()
            return int(cur.lastrowid)

    def inserir_curso_seed(
        self,
        codigo_mec: str,
        nome: str,
        grau_academico: str = "Bacharelado",
        modalidade: str = "PRESENCIAL",
        carga_horaria_total: int = 3000,
        duracao_semestres: int = 8,
        departamento_id: int = 1,
    ) -> int:
        """Insere um curso para vínculos discentes em testes ou inicialização."""
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Curso (
                    codigo_mec, nome, grau_academico, modalidade,
                    carga_horaria_total, duracao_semestres, departamento_id, ativo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    codigo_mec,
                    nome,
                    grau_academico,
                    modalidade,
                    carga_horaria_total,
                    duracao_semestres,
                    departamento_id,
                ),
            )
            self.conn.commit()
            return int(cur.lastrowid)

    def buscar_curso_por_id(self, curso_id: int) -> Optional[dict[str, Any]]:
        """Busca curso pelo identificador primário."""
        with self._lock:
            row = self.conn.execute(
                "SELECT id_curso, codigo_mec, nome, grau_academico, ativo FROM Curso WHERE id_curso = ?",
                (curso_id,),
            ).fetchone()
            return dict(row) if row else None

    def _inserir_auditoria_tx(
        self,
        usuario_id: Optional[int],
        entidade_afetada: str,
        id_registro_afetado: Optional[str],
        acao: str,
        dados_anteriores: Optional[str],
        dados_novos: Optional[str],
        ip_origem: str,
        data_hora: Optional[str] = None,
    ) -> int:
        timestamp = data_hora or datetime.now(timezone.utc).isoformat()
        cur = self.conn.execute(
            """
            INSERT INTO LogAuditoriaSistema (
                usuario_id, entidade_afetada, id_registro_afetado,
                acao, dados_anteriores, dados_novos, ip_origem, data_hora
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                usuario_id,
                entidade_afetada,
                id_registro_afetado,
                acao,
                dados_anteriores,
                dados_novos,
                ip_origem,
                timestamp,
            ),
        )
        return int(cur.lastrowid)

    def inserir_auditoria(
        self,
        usuario_id: Optional[int],
        entidade_afetada: str,
        id_registro_afetado: Optional[str],
        acao: str,
        dados_anteriores: Optional[str],
        dados_novos: Optional[str],
        ip_origem: str,
        data_hora: Optional[str] = None,
    ) -> dict[str, Any]:
        """Insere um evento imutável em LogAuditoriaSistema."""
        with self._lock:
            log_id = self._inserir_auditoria_tx(
                usuario_id=usuario_id,
                entidade_afetada=entidade_afetada,
                id_registro_afetado=id_registro_afetado,
                acao=acao,
                dados_anteriores=dados_anteriores,
                dados_novos=dados_novos,
                ip_origem=ip_origem,
                data_hora=data_hora,
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT * FROM LogAuditoriaSistema WHERE id_auditoria = ?",
                (log_id,),
            ).fetchone()
            return dict(row)

    @staticmethod
    def _row_para_resposta(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "matricula": int(row["matricula"]),
            "usuario_id": int(row["Usuario_id_usuario"]),
            "nome": str(row["nome"]),
            "cpf": str(row["cpf"]),
            "email": str(row["email"]),
            "telefone": row["telefone"],
            "data_nascimento": row["data_nascimento"],
            "curso_id": int(row["curso_id"]) if row["curso_id"] is not None else None,
            "curso_nome": row["curso_nome"],
            "status_academico": str(row["status_academico"]),
            "ira": float(row["ira"]),
            "login": str(row["login"]),
            "perfil_id": PERFIL_ALUNO_ID,
            "perfil": PERFIL_ALUNO_NOME,
            "ativo": int(row["statusCONTA"]) == 1,
            "senha_provisoria": _parse_senha_provisoria(row["dadosIdentificacao"]),
            "criado_em": row["criado_em"],
        }

    def _gerar_proxima_matricula_tx(self, ano_base: Optional[int] = None) -> int:
        """Gera número de matrícula único no padrão <ANO><SEQUENCIAL_4_DIGITOS> (ex.: 20260001)."""
        ano = ano_base or datetime.now(timezone.utc).year
        faixa_min = ano * 10000
        faixa_max = (ano + 1) * 10000 - 1
        row = self.conn.execute(
            "SELECT MAX(matricula) AS max_mat FROM Aluno WHERE matricula BETWEEN ? AND ?",
            (faixa_min, faixa_max),
        ).fetchone()
        if row and row["max_mat"] is not None:
            candidata = int(row["max_mat"]) + 1
        else:
            candidata = faixa_min + 1

        while self.conn.execute("SELECT 1 FROM Aluno WHERE matricula = ?", (candidata,)).fetchone():
            candidata += 1
        return candidata

    def gerar_proxima_matricula(self, ano_base: Optional[int] = None) -> int:
        """Calcula a próxima matrícula institucional disponível de forma thread-safe."""
        with self._lock:
            return self._gerar_proxima_matricula_tx(ano_base=ano_base)

    def buscar_por_matricula(self, matricula: int) -> Optional[dict[str, Any]]:
        """Busca aluno e conta de usuário associada pelo número de matrícula."""
        with self._lock:
            row = self.conn.execute(
                """
                SELECT a.matricula, a.Usuario_id_usuario, a.nome, a.email, a.cpf,
                       a.telefone, a.data_nascimento, a.curso_id, a.status_academico, a.ira,
                       u.login, u.perfil_RBAC, u.statusCONTA, u.dadosIdentificacao, u.criado_em,
                       c.nome AS curso_nome
                FROM Aluno a
                JOIN Usuario u ON u.id_usuario = a.Usuario_id_usuario
                LEFT JOIN Curso c ON c.id_curso = a.curso_id
                WHERE a.matricula = ?
                """,
                (matricula,),
            ).fetchone()
            return self._row_para_resposta(row) if row else None

    def buscar_por_cpf(self, cpf: str) -> Optional[dict[str, Any]]:
        """Busca aluno pelo CPF normalizado (11 dígitos)."""
        with self._lock:
            row = self.conn.execute(
                "SELECT matricula, cpf, Usuario_id_usuario FROM Aluno WHERE cpf = ?",
                (cpf,),
            ).fetchone()
            return dict(row) if row else None

    def buscar_por_email(self, email: str) -> Optional[dict[str, Any]]:
        """Busca aluno pelo endereço de e-mail normalizado."""
        with self._lock:
            row = self.conn.execute(
                "SELECT matricula, email, Usuario_id_usuario FROM Aluno WHERE LOWER(email) = LOWER(?)",
                (email,),
            ).fetchone()
            return dict(row) if row else None

    def buscar_usuario_por_login(self, login: str) -> Optional[dict[str, Any]]:
        """Busca conta de usuário pelo login exato."""
        with self._lock:
            row = self.conn.execute(
                "SELECT id_usuario, login, perfil_RBAC, statusCONTA FROM Usuario WHERE login = ?",
                (login,),
            ).fetchone()
            return dict(row) if row else None

    def criar_aluno_e_usuario(
        self,
        nome: str,
        cpf: str,
        email: str,
        telefone: Optional[str],
        data_nascimento: Optional[str],
        curso_id: Optional[int],
        matricula: Optional[int],
        login: str,
        senha_hash: str,
        operador_usuario_id: int,
        ip_origem: str,
        snapshot_base: dict[str, Any],
    ) -> dict[str, Any]:
        """Cria atomicamente Usuario (perfil Aluno), Aluno e registro de auditoria CRIAR."""
        dados_id = json.dumps({"senha_provisoria": True}, ensure_ascii=False)
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                matricula_final = (
                    int(matricula) if matricula is not None else self._gerar_proxima_matricula_tx()
                )
                cur_user = self.conn.execute(
                    """
                    INSERT INTO Usuario (login, senha_hash, perfil_RBAC, statusCONTA, dadosIdentificacao)
                    VALUES (?, ?, ?, 1, ?)
                    """,
                    (login, senha_hash, PERFIL_ALUNO_ID, dados_id),
                )
                usuario_id = int(cur_user.lastrowid)

                self.conn.execute(
                    """
                    INSERT INTO Aluno (
                        matricula, Usuario_id_usuario, nome, email, cpf,
                        telefone, data_nascimento, curso_id, status_academico, ira
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ATIVO', 0.00)
                    """,
                    (
                        matricula_final,
                        usuario_id,
                        nome,
                        email,
                        cpf,
                        telefone,
                        data_nascimento,
                        curso_id,
                    ),
                )

                snapshot_com_ids = {
                    **snapshot_base,
                    "matricula": matricula_final,
                    "usuario_id": usuario_id,
                }
                dados_novos_json = json.dumps(snapshot_com_ids, ensure_ascii=False, sort_keys=True)

                self._inserir_auditoria_tx(
                    usuario_id=operador_usuario_id,
                    entidade_afetada="Aluno",
                    id_registro_afetado=str(matricula_final),
                    acao="CRIAR",
                    dados_anteriores=None,
                    dados_novos=dados_novos_json,
                    ip_origem=ip_origem,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

            criado = self.buscar_por_matricula(matricula_final)
            assert criado is not None
            return criado

    def listar_alunos(
        self,
        status_academico: Optional[str] = None,
        curso_id: Optional[int] = None,
        ativo: Optional[bool] = None,
        busca: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Lista alunos ordenados alfabeticamente por nome com filtros opcionais."""
        clausulas: list[str] = []
        params: list[Any] = []
        if status_academico is not None:
            clausulas.append("a.status_academico = ?")
            params.append(status_academico)
        if curso_id is not None:
            clausulas.append("a.curso_id = ?")
            params.append(curso_id)
        if ativo is not None:
            clausulas.append("u.statusCONTA = ?")
            params.append(1 if ativo else 0)
        if busca is not None and busca.strip():
            termo = f"%{busca.strip().lower()}%"
            clausulas.append(
                "(LOWER(a.nome) LIKE ? OR LOWER(a.email) LIKE ? OR a.cpf LIKE ? "
                "OR LOWER(u.login) LIKE ? OR CAST(a.matricula AS TEXT) LIKE ?)"
            )
            params.extend([termo, termo, termo, termo, termo])

        where_sql = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""
        with self._lock:
            rows = self.conn.execute(
                f"""
                SELECT a.matricula, a.Usuario_id_usuario, a.nome, a.email, a.cpf,
                       a.telefone, a.data_nascimento, a.curso_id, a.status_academico, a.ira,
                       u.login, u.perfil_RBAC, u.statusCONTA, u.dadosIdentificacao, u.criado_em,
                       c.nome AS curso_nome
                FROM Aluno a
                JOIN Usuario u ON u.id_usuario = a.Usuario_id_usuario
                LEFT JOIN Curso c ON c.id_curso = a.curso_id
                {where_sql}
                """,
                params,
            ).fetchall()
            itens = [self._row_para_resposta(r) for r in rows]
            return sorted(itens, key=lambda item: (item["nome"].casefold(), item["matricula"]))

    def atualizar_aluno(
        self,
        matricula: int,
        usuario_id: int,
        nome: str,
        cpf: str,
        email: str,
        telefone: Optional[str],
        data_nascimento: Optional[str],
        curso_id: Optional[int],
        login: str,
        status_academico: str,
        operador_usuario_id: int,
        ip_origem: str,
        dados_anteriores_json: Optional[str],
        dados_novos_json: Optional[str],
    ) -> dict[str, Any]:
        """Atualiza atomicamente Usuario, Aluno e registra evento ATUALIZAR."""
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                self.conn.execute(
                    "UPDATE Usuario SET login = ? WHERE id_usuario = ?",
                    (login, usuario_id),
                )
                self.conn.execute(
                    """
                    UPDATE Aluno
                    SET nome = ?, cpf = ?, email = ?, telefone = ?,
                        data_nascimento = ?, curso_id = ?, status_academico = ?
                    WHERE matricula = ?
                    """,
                    (
                        nome,
                        cpf,
                        email,
                        telefone,
                        data_nascimento,
                        curso_id,
                        status_academico,
                        matricula,
                    ),
                )
                self._inserir_auditoria_tx(
                    usuario_id=operador_usuario_id,
                    entidade_afetada="Aluno",
                    id_registro_afetado=str(matricula),
                    acao="ATUALIZAR",
                    dados_anteriores=dados_anteriores_json,
                    dados_novos=dados_novos_json,
                    ip_origem=ip_origem,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

            atualizado = self.buscar_por_matricula(matricula)
            assert atualizado is not None
            return atualizado

    def alterar_status_aluno(
        self,
        matricula: int,
        usuario_id: int,
        ativo: bool,
        operador_usuario_id: int,
        ip_origem: str,
        dados_anteriores_json: Optional[str],
        dados_novos_json: Optional[str],
    ) -> dict[str, Any]:
        """Ativa ou inativa a conta do aluno em Usuario e registra evento ALTERAR_STATUS."""
        novo_status = 1 if ativo else 0
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                self.conn.execute(
                    "UPDATE Usuario SET statusCONTA = ? WHERE id_usuario = ?",
                    (novo_status, usuario_id),
                )
                self._inserir_auditoria_tx(
                    usuario_id=operador_usuario_id,
                    entidade_afetada="Aluno",
                    id_registro_afetado=str(matricula),
                    acao="ALTERAR_STATUS",
                    dados_anteriores=dados_anteriores_json,
                    dados_novos=dados_novos_json,
                    ip_origem=ip_origem,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

            atualizado = self.buscar_por_matricula(matricula)
            assert atualizado is not None
            return atualizado

    def listar_auditoria(self, id_registro_afetado: Optional[str] = None) -> list[dict[str, Any]]:
        """Consulta eventos de auditoria do módulo ordenados do mais recente para o mais antigo."""
        sql = "SELECT * FROM LogAuditoriaSistema WHERE entidade_afetada = 'Aluno'"
        params: list[Any] = []
        if id_registro_afetado is not None and id_registro_afetado.strip():
            sql += " AND id_registro_afetado = ?"
            params.append(id_registro_afetado.strip())
        sql += " ORDER BY id_auditoria DESC"
        with self._lock:
            rows = self.conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]


_DEFAULT_REPO: Optional[AlunoRepository] = None
_DEFAULT_REPO_LOCK = threading.Lock()


def get_repository() -> AlunoRepository:
    """Dependência FastAPI que fornece o repositório configurado para o ambiente."""
    global _DEFAULT_REPO
    with _DEFAULT_REPO_LOCK:
        if _DEFAULT_REPO is None:
            db_path = os.getenv("SGA_ALUNOS_DB_PATH", ":memory:")
            _DEFAULT_REPO = AlunoRepository(db_path=db_path)
        return _DEFAULT_REPO
