"""Persistência relacional SQLite transacional para o painel administrativo da coordenação (SGA-27)."""

from datetime import datetime, timezone
import os
import sqlite3
import threading
from typing import Any, Optional

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

CREATE TABLE IF NOT EXISTS Professor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    telefone VARCHAR(20) NULL,
    departamento VARCHAR(80) NOT NULL,
    titulacao VARCHAR(50) NOT NULL,
    areaAtuacao VARCHAR(100) NULL,
    Usuario_id_usuario INTEGER NULL UNIQUE,
    CONSTRAINT fk_Professor_Usuario1
        FOREIGN KEY (Usuario_id_usuario)
        REFERENCES Usuario (id_usuario)
        ON DELETE SET NULL
        ON UPDATE CASCADE
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
        ON UPDATE CASCADE,
    CONSTRAINT fk_Curso_Coordenador
        FOREIGN KEY (coordenador_id)
        REFERENCES Professor (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS MatrizCurricular (
    id_matriz INTEGER PRIMARY KEY AUTOINCREMENT,
    curso_id INTEGER NOT NULL,
    codigo_matriz VARCHAR(30) NOT NULL UNIQUE,
    ano_vigencia INTEGER NOT NULL,
    semestre_vigencia INTEGER NOT NULL,
    carga_horaria_minima INTEGER NOT NULL,
    ativa BOOLEAN NOT NULL DEFAULT 1,
    CONSTRAINT fk_MatrizCurricular_Curso
        FOREIGN KEY (curso_id)
        REFERENCES Curso (id_curso)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Disciplina (
    id_disciplina INTEGER PRIMARY KEY AUTOINCREMENT,
    matriz_id INTEGER NOT NULL,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nome VARCHAR(120) NOT NULL,
    semestre_ideal INTEGER NOT NULL,
    carga_horaria INTEGER NOT NULL,
    creditos INTEGER NOT NULL,
    natureza VARCHAR(25) NOT NULL DEFAULT 'OBRIGATORIA',
    ementa TEXT NULL,
    CONSTRAINT fk_Disciplina_MatrizCurricular
        FOREIGN KEY (matriz_id)
        REFERENCES MatrizCurricular (id_matriz)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS PeriodoLetivo (
    id_periodo INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(15) NOT NULL UNIQUE,
    ano INTEGER NOT NULL,
    semestre INTEGER NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    status_periodo VARCHAR(25) NOT NULL DEFAULT 'EM_ANDAMENTO'
);

CREATE TABLE IF NOT EXISTS Sala (
    id_sala INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_sala VARCHAR(30) NOT NULL UNIQUE,
    bloco VARCHAR(40) NOT NULL,
    capacidade INTEGER NOT NULL,
    tipo_sala VARCHAR(30) NOT NULL DEFAULT 'SALA_AULA',
    ativa BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Turma (
    id_turma INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_turma VARCHAR(30) NOT NULL UNIQUE,
    disciplina_id INTEGER NOT NULL,
    periodo_letivo_id INTEGER NOT NULL,
    professor_id INTEGER NULL,
    sala_id INTEGER NULL,
    turno VARCHAR(20) NOT NULL,
    vagas_totais INTEGER NOT NULL,
    vagas_ocupadas INTEGER NOT NULL DEFAULT 0,
    status_turma VARCHAR(25) NOT NULL DEFAULT 'ABERTA',
    CONSTRAINT fk_Turma_Disciplina
        FOREIGN KEY (disciplina_id)
        REFERENCES Disciplina (id_disciplina)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_Turma_PeriodoLetivo
        FOREIGN KEY (periodo_letivo_id)
        REFERENCES PeriodoLetivo (id_periodo)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_Turma_Professor
        FOREIGN KEY (professor_id)
        REFERENCES Professor (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_Turma_Sala
        FOREIGN KEY (sala_id)
        REFERENCES Sala (id_sala)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS HorarioTurma (
    id_horario INTEGER PRIMARY KEY AUTOINCREMENT,
    turma_id INTEGER NOT NULL,
    dia_semana INTEGER NOT NULL CHECK (dia_semana >= 1 AND dia_semana <= 7),
    hora_inicio VARCHAR(5) NOT NULL,
    hora_fim VARCHAR(5) NOT NULL,
    UNIQUE (turma_id, dia_semana, hora_inicio),
    CONSTRAINT fk_HorarioTurma_Turma
        FOREIGN KEY (turma_id)
        REFERENCES Turma (id_turma)
        ON DELETE CASCADE
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

CREATE TABLE IF NOT EXISTS MatriculaTurma (
    id_matricula_turma INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_matricula INTEGER NOT NULL,
    turma_id INTEGER NOT NULL,
    data_matricula DATETIME NOT NULL,
    media_final DECIMAL(4,2) NULL,
    percentual_frequencia DECIMAL(5,2) NOT NULL DEFAULT 100.00,
    situacao VARCHAR(30) NOT NULL DEFAULT 'CURSANDO',
    UNIQUE (aluno_matricula, turma_id),
    CONSTRAINT fk_MatriculaTurma_Aluno
        FOREIGN KEY (aluno_matricula)
        REFERENCES Aluno (matricula)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_MatriculaTurma_Turma
        FOREIGN KEY (turma_id)
        REFERENCES Turma (id_turma)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS MovimentacaoAcademica (
    id_movimentacao INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_matricula INTEGER NOT NULL,
    periodo_letivo_id INTEGER NOT NULL,
    tipo_movimentacao VARCHAR(30) NOT NULL,
    motivo TEXT NOT NULL,
    status_movimentacao VARCHAR(25) NOT NULL DEFAULT 'DEFERIDO',
    data_registro DATETIME NOT NULL,
    CONSTRAINT fk_Movimentacao_Aluno
        FOREIGN KEY (aluno_matricula)
        REFERENCES Aluno (matricula)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_Movimentacao_PeriodoLetivo
        FOREIGN KEY (periodo_letivo_id)
        REFERENCES PeriodoLetivo (id_periodo)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS RequerimentoAcademico (
    id_requerimento INTEGER PRIMARY KEY AUTOINCREMENT,
    protocolo VARCHAR(30) NOT NULL UNIQUE,
    aluno_matricula INTEGER NOT NULL,
    periodo_letivo_id INTEGER NULL,
    tipo_requerimento VARCHAR(50) NOT NULL,
    descricao TEXT NOT NULL,
    status_requerimento VARCHAR(25) NOT NULL DEFAULT 'ABERTO'
        CHECK (status_requerimento IN ('ABERTO', 'EM_ANALISE', 'DEFERIDO', 'INDEFERIDO')),
    parecer_secretaria TEXT NULL,
    aberto_em DATETIME NOT NULL,
    atualizado_em DATETIME NULL,
    CONSTRAINT fk_Requerimento_Aluno
        FOREIGN KEY (aluno_matricula)
        REFERENCES Aluno (matricula)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_Requerimento_PeriodoLetivo
        FOREIGN KEY (periodo_letivo_id)
        REFERENCES PeriodoLetivo (id_periodo)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

CREATE TRIGGER IF NOT EXISTS trg_bloquear_delete_requerimento_academico
BEFORE DELETE ON RequerimentoAcademico
BEGIN
    SELECT RAISE(ABORT, 'Exclusao fisica de RequerimentoAcademico e proibida pela preservacao historica.');
END;

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

CREATE INDEX IF NOT EXISTS idx_auditoria_entidade_reg
    ON LogAuditoriaSistema (entidade_afetada, id_registro_afetado);
"""


def criar_conexao(db_path: str = ":memory:") -> sqlite3.Connection:
    """Abre conexão SQLite com chaves estrangeiras ativadas e transações explícitas."""
    conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def inicializar_esquema(conn: sqlite3.Connection) -> None:
    """Cria tabelas, índices, trigger de preservação histórica e semeia os 5 perfis RBAC."""
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
    conn.execute("PRAGMA foreign_keys = ON;")


class PainelCoordenacaoRepository:
    """Repositório transacional SQLite para indicadores, oferta, requerimentos, docentes e auditoria."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._lock = threading.RLock()
        self.conn = criar_conexao(db_path)
        inicializar_esquema(self.conn)

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    # ------------------------------------------------------------------
    # Helpers de Seed / Apoio (ambiente e testes)
    # ------------------------------------------------------------------

    def inserir_usuario_seed(
        self, login: str, senha_hash: str, perfil_id: int, status_conta: int = 1
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO Usuario (login, senha_hash, perfil_RBAC, statusCONTA) VALUES (?, ?, ?, ?)",
                (login, senha_hash, perfil_id, status_conta),
            )
            return int(cur.lastrowid)

    def inserir_departamento_seed(self, codigo: str, nome: str, sigla: str) -> int:
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO Departamento (codigo, nome, sigla, ativo) VALUES (?, ?, ?, 1)",
                (codigo, nome, sigla),
            )
            return int(cur.lastrowid)

    def inserir_professor_seed(
        self,
        nome: str,
        email: str,
        cpf: str,
        departamento: str,
        titulacao: str = "Doutorado",
        area_atuacao: Optional[str] = "Engenharia de Software",
        telefone: Optional[str] = "71977776666",
        usuario_id: Optional[int] = None,
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Professor (
                    nome, email, cpf, telefone, departamento, titulacao, areaAtuacao, Usuario_id_usuario
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (nome, email, cpf, telefone, departamento, titulacao, area_atuacao, usuario_id),
            )
            return int(cur.lastrowid)

    def inserir_curso_seed(
        self,
        codigo_mec: str,
        nome: str,
        departamento_id: int,
        grau_academico: str = "Bacharelado",
        carga_horaria_total: int = 3000,
        duracao_semestres: int = 8,
        coordenador_id: Optional[int] = None,
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Curso (
                    codigo_mec, nome, grau_academico, modalidade,
                    carga_horaria_total, duracao_semestres, departamento_id, coordenador_id, ativo
                )
                VALUES (?, ?, ?, 'PRESENCIAL', ?, ?, ?, ?, 1)
                """,
                (
                    codigo_mec,
                    nome,
                    grau_academico,
                    carga_horaria_total,
                    duracao_semestres,
                    departamento_id,
                    coordenador_id,
                ),
            )
            return int(cur.lastrowid)

    def inserir_matriz_seed(self, curso_id: int, codigo_matriz: str) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO MatrizCurricular (
                    curso_id, codigo_matriz, ano_vigencia, semestre_vigencia, carga_horaria_minima, ativa
                )
                VALUES (?, ?, 2026, 1, 3000, 1)
                """,
                (curso_id, codigo_matriz),
            )
            return int(cur.lastrowid)

    def inserir_disciplina_seed(
        self, matriz_id: int, codigo: str, nome: str, carga_horaria: int = 60, creditos: int = 4
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Disciplina (
                    matriz_id, codigo, nome, semestre_ideal, carga_horaria, creditos, natureza
                )
                VALUES (?, ?, ?, 1, ?, ?, 'OBRIGATORIA')
                """,
                (matriz_id, codigo, nome, carga_horaria, creditos),
            )
            return int(cur.lastrowid)

    def inserir_periodo_seed(self, codigo: str, ano: int, semestre: int) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO PeriodoLetivo (codigo, ano, semestre, data_inicio, data_fim, status_periodo)
                VALUES (?, ?, ?, '2026-08-01', '2026-12-15', 'EM_ANDAMENTO')
                """,
                (codigo, ano, semestre),
            )
            return int(cur.lastrowid)

    def inserir_sala_seed(self, codigo_sala: str, bloco: str, capacidade: int = 40) -> int:
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO Sala (codigo_sala, bloco, capacidade, tipo_sala, ativa) VALUES (?, ?, ?, 'SALA_AULA', 1)",
                (codigo_sala, bloco, capacidade),
            )
            return int(cur.lastrowid)

    def inserir_turma_seed(
        self,
        codigo_turma: str,
        disciplina_id: int,
        periodo_letivo_id: int,
        professor_id: Optional[int] = None,
        sala_id: Optional[int] = None,
        turno: str = "NOTURNO",
        vagas_totais: int = 40,
        vagas_ocupadas: int = 0,
        status_turma: str = "ABERTA",
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Turma (
                    codigo_turma, disciplina_id, periodo_letivo_id, professor_id, sala_id,
                    turno, vagas_totais, vagas_ocupadas, status_turma
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    codigo_turma,
                    disciplina_id,
                    periodo_letivo_id,
                    professor_id,
                    sala_id,
                    turno,
                    vagas_totais,
                    vagas_ocupadas,
                    status_turma,
                ),
            )
            return int(cur.lastrowid)

    def inserir_horario_turma_seed(
        self, turma_id: int, dia_semana: int, hora_inicio: str, hora_fim: str
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO HorarioTurma (turma_id, dia_semana, hora_inicio, hora_fim)
                VALUES (?, ?, ?, ?)
                """,
                (turma_id, dia_semana, hora_inicio, hora_fim),
            )
            return int(cur.lastrowid)

    def inserir_aluno_seed(
        self,
        matricula: int,
        usuario_id: int,
        nome: str,
        email: str,
        cpf: str,
        curso_id: Optional[int],
        status_academico: str = "ATIVO",
        ira: float = 8.0,
        telefone: str = "71999998888",
        data_nascimento: str = "2002-07-10",
    ) -> int:
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO Aluno (
                    matricula, Usuario_id_usuario, nome, email, cpf,
                    telefone, data_nascimento, curso_id, status_academico, ira
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    matricula,
                    usuario_id,
                    nome,
                    email,
                    cpf,
                    telefone,
                    data_nascimento,
                    curso_id,
                    status_academico,
                    ira,
                ),
            )
            return matricula

    def inserir_matricula_turma_seed(
        self,
        aluno_matricula: int,
        turma_id: int,
        percentual_frequencia: float = 95.0,
        situacao: str = "CURSANDO",
        media_final: Optional[float] = None,
    ) -> int:
        ts = datetime.now(timezone.utc).isoformat()
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO MatriculaTurma (
                    aluno_matricula, turma_id, data_matricula, media_final, percentual_frequencia, situacao
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (aluno_matricula, turma_id, ts, media_final, percentual_frequencia, situacao),
            )
            self.conn.execute(
                "UPDATE Turma SET vagas_ocupadas = vagas_ocupadas + 1 WHERE id_turma = ?",
                (turma_id,),
            )
            return int(cur.lastrowid)

    def inserir_movimentacao_seed(
        self,
        aluno_matricula: int,
        periodo_letivo_id: int,
        tipo_movimentacao: str,
        motivo: str = "Solicitação discente",
        status_movimentacao: str = "DEFERIDO",
    ) -> int:
        ts = datetime.now(timezone.utc).isoformat()
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO MovimentacaoAcademica (
                    aluno_matricula, periodo_letivo_id, tipo_movimentacao, motivo, status_movimentacao, data_registro
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (aluno_matricula, periodo_letivo_id, tipo_movimentacao, motivo, status_movimentacao, ts),
            )
            return int(cur.lastrowid)

    def inserir_requerimento_seed(
        self,
        protocolo: str,
        aluno_matricula: int,
        tipo_requerimento: str,
        descricao: str,
        periodo_letivo_id: Optional[int] = None,
        status_requerimento: str = "ABERTO",
        parecer_secretaria: Optional[str] = None,
    ) -> int:
        ts = datetime.now(timezone.utc).isoformat()
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO RequerimentoAcademico (
                    protocolo, aluno_matricula, periodo_letivo_id, tipo_requerimento,
                    descricao, status_requerimento, parecer_secretaria, aberto_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    protocolo,
                    aluno_matricula,
                    periodo_letivo_id,
                    tipo_requerimento,
                    descricao,
                    status_requerimento,
                    parecer_secretaria,
                    ts,
                ),
            )
            return int(cur.lastrowid)

    # ------------------------------------------------------------------
    # Consultas de Referência e Validação de Filtros
    # ------------------------------------------------------------------

    def buscar_usuario_por_id(self, usuario_id: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT u.id_usuario, u.login, u.senha_hash, u.perfil_RBAC,
                       u.statusCONTA, p.nome_perfil
                FROM Usuario u
                JOIN Perfil p ON p.id_perfil = u.perfil_RBAC
                WHERE u.id_usuario = ?
                """,
                (usuario_id,),
            ).fetchone()
            return dict(row) if row else None

    def buscar_curso_por_id(self, curso_id: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                "SELECT id_curso, codigo_mec, nome, grau_academico FROM Curso WHERE id_curso = ?",
                (curso_id,),
            ).fetchone()
            return dict(row) if row else None

    def buscar_periodo_por_id(self, periodo_letivo_id: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                "SELECT id_periodo, codigo, ano, semestre, status_periodo FROM PeriodoLetivo WHERE id_periodo = ?",
                (periodo_letivo_id,),
            ).fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------
    # US1: Consultas de KPIs, Evasão e Alertas de Risco
    # ------------------------------------------------------------------

    def listar_alunos_escopo(self, curso_id: Optional[int] = None) -> list[dict[str, Any]]:
        sql = """
            SELECT a.matricula, a.nome, a.curso_id, c.nome AS curso_nome,
                   a.status_academico, a.ira
            FROM Aluno a
            LEFT JOIN Curso c ON c.id_curso = a.curso_id
        """
        params: list[Any] = []
        if curso_id is not None:
            sql += " WHERE a.curso_id = ?"
            params.append(curso_id)
        sql += " ORDER BY a.matricula ASC"
        with self._lock:
            return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def contar_processos_abertos(
        self, curso_id: Optional[int] = None, periodo_letivo_id: Optional[int] = None
    ) -> int:
        clausulas = ["r.status_requerimento IN ('ABERTO', 'EM_ANALISE')"]
        params: list[Any] = []
        if curso_id is not None:
            clausulas.append("a.curso_id = ?")
            params.append(curso_id)
        if periodo_letivo_id is not None:
            clausulas.append("r.periodo_letivo_id = ?")
            params.append(periodo_letivo_id)
        where_sql = " AND ".join(clausulas)
        with self._lock:
            row = self.conn.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM RequerimentoAcademico r
                JOIN Aluno a ON a.matricula = r.aluno_matricula
                WHERE {where_sql}
                """,
                params,
            ).fetchone()
            return int(row["total"]) if row else 0

    def listar_movimentacoes_deferidas(
        self, curso_id: Optional[int] = None, periodo_letivo_id: Optional[int] = None
    ) -> list[dict[str, Any]]:
        clausulas = ["m.status_movimentacao = 'DEFERIDO'"]
        params: list[Any] = []
        if curso_id is not None:
            clausulas.append("a.curso_id = ?")
            params.append(curso_id)
        if periodo_letivo_id is not None:
            clausulas.append("m.periodo_letivo_id = ?")
            params.append(periodo_letivo_id)
        where_sql = " AND ".join(clausulas)
        with self._lock:
            rows = self.conn.execute(
                f"""
                SELECT m.id_movimentacao, m.aluno_matricula, m.periodo_letivo_id,
                       m.tipo_movimentacao, m.status_movimentacao
                FROM MovimentacaoAcademica m
                JOIN Aluno a ON a.matricula = m.aluno_matricula
                WHERE {where_sql}
                """,
                params,
            ).fetchall()
            return [dict(r) for r in rows]

    def listar_matriculas_escopo(
        self, curso_id: Optional[int] = None, periodo_letivo_id: Optional[int] = None
    ) -> list[dict[str, Any]]:
        clausulas = ["t.status_turma <> 'CANCELADA'"]
        params: list[Any] = []
        if curso_id is not None:
            clausulas.append("mc.curso_id = ?")
            params.append(curso_id)
        if periodo_letivo_id is not None:
            clausulas.append("t.periodo_letivo_id = ?")
            params.append(periodo_letivo_id)
        where_sql = " AND ".join(clausulas)
        with self._lock:
            rows = self.conn.execute(
                f"""
                SELECT mt.id_matricula_turma, mt.aluno_matricula, mt.turma_id,
                       mt.percentual_frequencia, mt.situacao
                FROM MatriculaTurma mt
                JOIN Turma t ON t.id_turma = mt.turma_id
                JOIN Disciplina d ON d.id_disciplina = t.disciplina_id
                JOIN MatrizCurricular mc ON mc.id_matriz = d.matriz_id
                WHERE {where_sql}
                """,
                params,
            ).fetchall()
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # US2: Oferta de Turmas e Horários
    # ------------------------------------------------------------------

    def listar_oferta_turmas(
        self,
        periodo_letivo_id: Optional[int] = None,
        curso_id: Optional[int] = None,
        turno: Optional[str] = None,
        status_turma: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        clausulas: list[str] = []
        params: list[Any] = []
        if periodo_letivo_id is not None:
            clausulas.append("t.periodo_letivo_id = ?")
            params.append(periodo_letivo_id)
        if curso_id is not None:
            clausulas.append("mc.curso_id = ?")
            params.append(curso_id)
        if turno is not None and turno.strip():
            clausulas.append("UPPER(t.turno) = UPPER(?)")
            params.append(turno.strip())
        if status_turma is not None and status_turma.strip():
            clausulas.append("UPPER(t.status_turma) = UPPER(?)")
            params.append(status_turma.strip())

        where_sql = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""
        with self._lock:
            rows = self.conn.execute(
                f"""
                SELECT t.id_turma, t.codigo_turma, t.turno, t.vagas_totais, t.vagas_ocupadas,
                       t.status_turma, t.professor_id, t.sala_id, t.periodo_letivo_id,
                       d.codigo AS disciplina_codigo, d.nome AS disciplina_nome, d.carga_horaria,
                       c.id_curso, c.nome AS curso_nome,
                       p.codigo AS periodo_letivo_codigo,
                       pr.nome AS professor_nome,
                       s.codigo_sala, s.bloco AS sala_bloco
                FROM Turma t
                JOIN Disciplina d ON d.id_disciplina = t.disciplina_id
                JOIN MatrizCurricular mc ON mc.id_matriz = d.matriz_id
                JOIN Curso c ON c.id_curso = mc.curso_id
                JOIN PeriodoLetivo p ON p.id_periodo = t.periodo_letivo_id
                LEFT JOIN Professor pr ON pr.id = t.professor_id
                LEFT JOIN Sala s ON s.id_sala = t.sala_id
                {where_sql}
                ORDER BY t.codigo_turma ASC
                """,
                params,
            ).fetchall()

            turmas: list[dict[str, Any]] = []
            for r in rows:
                item = dict(r)
                horarios = self.conn.execute(
                    """
                    SELECT dia_semana, hora_inicio, hora_fim
                    FROM HorarioTurma
                    WHERE turma_id = ?
                    ORDER BY dia_semana ASC, hora_inicio ASC
                    """,
                    (item["id_turma"],),
                ).fetchall()
                item["horarios"] = [dict(h) for h in horarios]
                turmas.append(item)
            return turmas

    # ------------------------------------------------------------------
    # US3: Requerimentos, Despachos Atômicos e Corpo Docente
    # ------------------------------------------------------------------

    _SELECT_REQ = """
        SELECT r.id_requerimento, r.protocolo, r.aluno_matricula, a.nome AS aluno_nome,
               a.curso_id, c.nome AS curso_nome,
               r.periodo_letivo_id, p.codigo AS periodo_letivo_codigo,
               r.tipo_requerimento, r.descricao, r.status_requerimento,
               r.parecer_secretaria, r.aberto_em, r.atualizado_em
        FROM RequerimentoAcademico r
        JOIN Aluno a ON a.matricula = r.aluno_matricula
        LEFT JOIN Curso c ON c.id_curso = a.curso_id
        LEFT JOIN PeriodoLetivo p ON p.id_periodo = r.periodo_letivo_id
    """

    @staticmethod
    def _row_para_requerimento(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id_requerimento": int(row["id_requerimento"]),
            "protocolo": str(row["protocolo"]),
            "aluno_matricula": int(row["aluno_matricula"]),
            "aluno_nome": str(row["aluno_nome"] or ""),
            "curso_id": int(row["curso_id"]) if row["curso_id"] is not None else None,
            "curso_nome": row["curso_nome"],
            "periodo_letivo_id": int(row["periodo_letivo_id"]) if row["periodo_letivo_id"] is not None else None,
            "periodo_letivo_codigo": row["periodo_letivo_codigo"],
            "tipo_requerimento": str(row["tipo_requerimento"]),
            "descricao": str(row["descricao"]),
            "status_requerimento": str(row["status_requerimento"]),
            "parecer_secretaria": row["parecer_secretaria"],
            "aberto_em": str(row["aberto_em"]),
            "atualizado_em": row["atualizado_em"],
        }

    def listar_requerimentos(
        self,
        curso_id: Optional[int] = None,
        periodo_letivo_id: Optional[int] = None,
        tipo_requerimento: Optional[str] = None,
        aluno_matricula: Optional[int] = None,
        status_requerimento: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        clausulas: list[str] = []
        params: list[Any] = []
        if curso_id is not None:
            clausulas.append("a.curso_id = ?")
            params.append(curso_id)
        if periodo_letivo_id is not None:
            clausulas.append("r.periodo_letivo_id = ?")
            params.append(periodo_letivo_id)
        if tipo_requerimento is not None and tipo_requerimento.strip():
            clausulas.append("UPPER(r.tipo_requerimento) = UPPER(?)")
            params.append(tipo_requerimento.strip())
        if aluno_matricula is not None:
            clausulas.append("r.aluno_matricula = ?")
            params.append(aluno_matricula)
        if status_requerimento is not None:
            clausulas.append("r.status_requerimento = ?")
            params.append(status_requerimento)
        where_sql = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""
        with self._lock:
            rows = self.conn.execute(
                f"{self._SELECT_REQ} {where_sql} ORDER BY r.id_requerimento DESC",
                params,
            ).fetchall()
            return [self._row_para_requerimento(r) for r in rows]

    def buscar_requerimento_por_id(self, id_requerimento: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                f"{self._SELECT_REQ} WHERE r.id_requerimento = ?",
                (id_requerimento,),
            ).fetchone()
            return self._row_para_requerimento(row) if row else None

    def despachar_requerimento_atomico(
        self,
        id_requerimento: int,
        protocolo: str,
        novo_status: str,
        parecer: str,
        atualizado_em: str,
        operador_usuario_id: int,
        ip_origem: str,
        dados_anteriores_json: str,
        dados_novos_json: str,
    ) -> dict[str, Any]:
        """Atualiza RequerimentoAcademico e grava LogAuditoriaSistema em uma única transação."""
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                self.conn.execute(
                    """
                    UPDATE RequerimentoAcademico
                    SET status_requerimento = ?, parecer_secretaria = ?, atualizado_em = ?
                    WHERE id_requerimento = ?
                    """,
                    (novo_status, parecer, atualizado_em, id_requerimento),
                )
                self.conn.execute(
                    """
                    INSERT INTO LogAuditoriaSistema (
                        usuario_id, entidade_afetada, id_registro_afetado,
                        acao, dados_anteriores, dados_novos, ip_origem, data_hora
                    )
                    VALUES (?, 'RequerimentoAcademico', ?, 'DESPACHAR', ?, ?, ?, ?)
                    """,
                    (
                        operador_usuario_id,
                        protocolo,
                        dados_anteriores_json,
                        dados_novos_json,
                        ip_origem,
                        atualizado_em,
                    ),
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

            atualizado = self.buscar_requerimento_por_id(id_requerimento)
            assert atualizado is not None
            return atualizado

    def listar_alocacao_docentes(
        self,
        departamento: Optional[str] = None,
        curso_id: Optional[int] = None,
        periodo_letivo_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Agrega turmas ativas, carga horária e alunos atendidos por docente sem expor dados sensíveis."""
        prof_clausulas: list[str] = []
        prof_params: list[Any] = []
        if departamento is not None and departamento.strip():
            prof_clausulas.append("UPPER(pr.departamento) = UPPER(?)")
            prof_params.append(departamento.strip())

        prof_where = f"WHERE {' AND '.join(prof_clausulas)}" if prof_clausulas else ""

        turma_clausulas = ["t.status_turma <> 'CANCELADA'", "t.professor_id = ?"]
        with self._lock:
            professores = self.conn.execute(
                f"""
                SELECT pr.id, pr.nome, pr.titulacao, pr.departamento, pr.areaAtuacao
                FROM Professor pr
                {prof_where}
                ORDER BY LOWER(pr.nome) ASC, pr.id ASC
                """,
                prof_params,
            ).fetchall()

            resultado: list[dict[str, Any]] = []
            for p in professores:
                pid = int(p["id"])
                t_clausulas = list(turma_clausulas)
                t_params: list[Any] = [pid]
                if curso_id is not None:
                    t_clausulas.append("mc.curso_id = ?")
                    t_params.append(curso_id)
                if periodo_letivo_id is not None:
                    t_clausulas.append("t.periodo_letivo_id = ?")
                    t_params.append(periodo_letivo_id)

                t_rows = self.conn.execute(
                    f"""
                    SELECT t.id_turma, d.carga_horaria, t.vagas_ocupadas
                    FROM Turma t
                    JOIN Disciplina d ON d.id_disciplina = t.disciplina_id
                    JOIN MatrizCurricular mc ON mc.id_matriz = d.matriz_id
                    WHERE {' AND '.join(t_clausulas)}
                    """,
                    t_params,
                ).fetchall()

                # Se filtrou por curso_id, exibe apenas docentes com alocação naquele curso
                if curso_id is not None and not t_rows:
                    continue

                resultado.append(
                    {
                        "professor_id": pid,
                        "nome": str(p["nome"]),
                        "titulacao": str(p["titulacao"]),
                        "departamento": str(p["departamento"]),
                        "area_atuacao": p["areaAtuacao"],
                        "total_turmas": len(t_rows),
                        "carga_horaria_total": sum(int(r["carga_horaria"]) for r in t_rows),
                        "total_alunos_atendidos": sum(int(r["vagas_ocupadas"]) for r in t_rows),
                    }
                )
            return resultado

    # ------------------------------------------------------------------
    # US4: Auditoria LGPD
    # ------------------------------------------------------------------

    def listar_auditoria(self, id_registro_afetado: Optional[str] = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM LogAuditoriaSistema WHERE entidade_afetada = 'RequerimentoAcademico'"
        params: list[Any] = []
        if id_registro_afetado is not None and id_registro_afetado.strip():
            sql += " AND id_registro_afetado = ?"
            params.append(id_registro_afetado.strip())
        sql += " ORDER BY id_auditoria DESC"
        with self._lock:
            return [dict(r) for r in self.conn.execute(sql, params).fetchall()]


_DEFAULT_REPO: Optional[PainelCoordenacaoRepository] = None
_DEFAULT_REPO_LOCK = threading.Lock()


def get_repository() -> PainelCoordenacaoRepository:
    """Dependência FastAPI que fornece o repositório configurado para o ambiente."""
    global _DEFAULT_REPO
    with _DEFAULT_REPO_LOCK:
        if _DEFAULT_REPO is None:
            db_path = os.getenv("SGA_COORDENACAO_DB_PATH", ":memory:")
            _DEFAULT_REPO = PainelCoordenacaoRepository(db_path=db_path)
        return _DEFAULT_REPO
