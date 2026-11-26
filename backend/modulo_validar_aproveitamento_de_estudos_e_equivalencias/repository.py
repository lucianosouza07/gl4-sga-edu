"""Persistência relacional SQLite transacional para aproveitamento de estudos e equivalências (SGA-26)."""

from datetime import datetime, timezone
import json
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

ENTIDADES_AUDITORIA_MODULO: tuple[str, ...] = (
    "EquivalenciaDisciplina",
    "SolicitacaoAproveitamento",
    "DispensaDisciplina",
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

CREATE TABLE IF NOT EXISTS PreRequisito (
    id_prerequisito INTEGER PRIMARY KEY AUTOINCREMENT,
    disciplina_id INTEGER NOT NULL,
    requisito_disciplina_id INTEGER NOT NULL,
    tipo_requisito VARCHAR(20) NOT NULL DEFAULT 'PRE_REQUISITO',
    UNIQUE (disciplina_id, requisito_disciplina_id),
    CHECK (disciplina_id <> requisito_disciplina_id),
    CONSTRAINT fk_PreRequisito_Disciplina
        FOREIGN KEY (disciplina_id)
        REFERENCES Disciplina (id_disciplina)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_PreRequisito_Requisito
        FOREIGN KEY (requisito_disciplina_id)
        REFERENCES Disciplina (id_disciplina)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS EquivalenciaDisciplina (
    id_equivalencia INTEGER PRIMARY KEY AUTOINCREMENT,
    disciplina_origem_id INTEGER NOT NULL,
    disciplina_equivalente_id INTEGER NOT NULL,
    portaria_aprovacao VARCHAR(60) NULL,
    ativa BOOLEAN NOT NULL DEFAULT 1,
    UNIQUE (disciplina_origem_id, disciplina_equivalente_id),
    CHECK (disciplina_origem_id <> disciplina_equivalente_id),
    CONSTRAINT fk_Equivalencia_Origem
        FOREIGN KEY (disciplina_origem_id)
        REFERENCES Disciplina (id_disciplina)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_Equivalencia_Equivalente
        FOREIGN KEY (disciplina_equivalente_id)
        REFERENCES Disciplina (id_disciplina)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_equivalencia_origem ON EquivalenciaDisciplina (disciplina_origem_id);
CREATE INDEX IF NOT EXISTS idx_equivalencia_equiv ON EquivalenciaDisciplina (disciplina_equivalente_id);

CREATE TABLE IF NOT EXISTS PeriodoLetivo (
    id_periodo INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(15) NOT NULL UNIQUE,
    ano INTEGER NOT NULL,
    semestre INTEGER NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    status_periodo VARCHAR(25) NOT NULL DEFAULT 'EM_ANDAMENTO'
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

CREATE TABLE IF NOT EXISTS SolicitacaoAproveitamento (
    id_solicitacao INTEGER PRIMARY KEY AUTOINCREMENT,
    protocolo VARCHAR(40) NOT NULL UNIQUE,
    aluno_matricula INTEGER NOT NULL,
    disciplina_alvo_id INTEGER NOT NULL,
    modalidade VARCHAR(30) NOT NULL
        CHECK (modalidade IN ('EQUIVALENCIA_INTERNA', 'ESTUDOS_EXTERNOS')),
    disciplina_origem_id INTEGER NULL,
    equivalencia_id INTEGER NULL,
    instituicao_origem VARCHAR(150) NULL,
    disciplina_externa_nome VARCHAR(150) NULL,
    carga_horaria_cursada INTEGER NOT NULL CHECK (carga_horaria_cursada > 0),
    nota_obtida DECIMAL(4,2) NOT NULL CHECK (nota_obtida >= 0.00 AND nota_obtida <= 10.00),
    ementa_resumo TEXT NULL,
    documentacao_comprobatoria VARCHAR(255) NULL,
    pre_validacao_elegivel BOOLEAN NOT NULL,
    pre_validacao_detalhes_json TEXT NOT NULL,
    status_solicitacao VARCHAR(25) NOT NULL DEFAULT 'EM_ANALISE'
        CHECK (status_solicitacao IN ('EM_ANALISE', 'DEFERIDO', 'INDEFERIDO')),
    parecer_tecnico TEXT NULL,
    aberto_por_usuario_id INTEGER NULL,
    deliberado_por_usuario_id INTEGER NULL,
    aberto_em DATETIME NOT NULL,
    deliberado_em DATETIME NULL,
    CONSTRAINT chk_modalidade_campos CHECK (
        (modalidade = 'EQUIVALENCIA_INTERNA' AND disciplina_origem_id IS NOT NULL AND disciplina_origem_id <> disciplina_alvo_id)
        OR (modalidade = 'ESTUDOS_EXTERNOS' AND instituicao_origem IS NOT NULL AND disciplina_externa_nome IS NOT NULL)
    ),
    CONSTRAINT fk_Solicitacao_Aluno
        FOREIGN KEY (aluno_matricula)
        REFERENCES Aluno (matricula)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_Solicitacao_DisciplinaAlvo
        FOREIGN KEY (disciplina_alvo_id)
        REFERENCES Disciplina (id_disciplina)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_Solicitacao_DisciplinaOrigem
        FOREIGN KEY (disciplina_origem_id)
        REFERENCES Disciplina (id_disciplina)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_Solicitacao_Equivalencia
        FOREIGN KEY (equivalencia_id)
        REFERENCES EquivalenciaDisciplina (id_equivalencia)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_Solicitacao_AbertoPor
        FOREIGN KEY (aberto_por_usuario_id)
        REFERENCES Usuario (id_usuario)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_Solicitacao_DeliberadoPor
        FOREIGN KEY (deliberado_por_usuario_id)
        REFERENCES Usuario (id_usuario)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_solicitacao_aluno ON SolicitacaoAproveitamento (aluno_matricula);
CREATE INDEX IF NOT EXISTS idx_solicitacao_alvo ON SolicitacaoAproveitamento (disciplina_alvo_id);
CREATE INDEX IF NOT EXISTS idx_solicitacao_status ON SolicitacaoAproveitamento (status_solicitacao);
CREATE UNIQUE INDEX IF NOT EXISTS uq_solicitacao_em_analise_aluno_disciplina
    ON SolicitacaoAproveitamento (aluno_matricula, disciplina_alvo_id)
    WHERE status_solicitacao = 'EM_ANALISE';

CREATE TRIGGER IF NOT EXISTS trg_bloquear_delete_solicitacao_encerrada
BEFORE DELETE ON SolicitacaoAproveitamento
WHEN OLD.status_solicitacao IN ('DEFERIDO', 'INDEFERIDO')
BEGIN
    SELECT RAISE(ABORT, 'Exclusao fisica de solicitacao deliberada e proibida pela preservacao historica.');
END;

CREATE TABLE IF NOT EXISTS DispensaDisciplina (
    id_dispensa INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_matricula INTEGER NOT NULL,
    disciplina_id INTEGER NOT NULL,
    solicitacao_id INTEGER NOT NULL UNIQUE,
    modalidade VARCHAR(30) NOT NULL
        CHECK (modalidade IN ('EQUIVALENCIA_INTERNA', 'ESTUDOS_EXTERNOS')),
    nota_aproveitada DECIMAL(4,2) NOT NULL CHECK (nota_aproveitada >= 0.00 AND nota_aproveitada <= 10.00),
    carga_horaria_aproveitada INTEGER NOT NULL CHECK (carga_horaria_aproveitada > 0),
    reconhecido_em DATETIME NOT NULL,
    UNIQUE (aluno_matricula, disciplina_id),
    CONSTRAINT fk_Dispensa_Aluno
        FOREIGN KEY (aluno_matricula)
        REFERENCES Aluno (matricula)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_Dispensa_Disciplina
        FOREIGN KEY (disciplina_id)
        REFERENCES Disciplina (id_disciplina)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_Dispensa_Solicitacao
        FOREIGN KEY (solicitacao_id)
        REFERENCES SolicitacaoAproveitamento (id_solicitacao)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dispensa_aluno ON DispensaDisciplina (aluno_matricula);

CREATE TRIGGER IF NOT EXISTS trg_bloquear_delete_dispensa_disciplina
BEFORE DELETE ON DispensaDisciplina
BEGIN
    SELECT RAISE(ABORT, 'Exclusao fisica de dispensa consolidada e proibida pela preservacao historica.');
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
    """Cria tabelas, índices, triggers de preservação histórica e semeia os 5 perfis RBAC."""
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


class AproveitamentoRepository:
    """Repositório transacional SQLite para equivalências, protocolos, dispensas e auditoria."""

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
        self,
        login: str,
        senha_hash: str,
        perfil_id: int,
        status_conta: int = 1,
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

    def inserir_curso_seed(
        self,
        codigo_mec: str,
        nome: str,
        departamento_id: int,
        grau_academico: str = "Bacharelado",
        carga_horaria_total: int = 3000,
        duracao_semestres: int = 8,
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Curso (
                    codigo_mec, nome, grau_academico, modalidade,
                    carga_horaria_total, duracao_semestres, departamento_id, ativo
                )
                VALUES (?, ?, ?, 'PRESENCIAL', ?, ?, ?, 1)
                """,
                (codigo_mec, nome, grau_academico, carga_horaria_total, duracao_semestres, departamento_id),
            )
            return int(cur.lastrowid)

    def inserir_matriz_seed(
        self,
        curso_id: int,
        codigo_matriz: str,
        ano_vigencia: int = 2026,
        semestre_vigencia: int = 1,
        carga_horaria_minima: int = 3000,
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO MatrizCurricular (
                    curso_id, codigo_matriz, ano_vigencia, semestre_vigencia, carga_horaria_minima, ativa
                )
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (curso_id, codigo_matriz, ano_vigencia, semestre_vigencia, carga_horaria_minima),
            )
            return int(cur.lastrowid)

    def inserir_disciplina_seed(
        self,
        matriz_id: int,
        codigo: str,
        nome: str,
        semestre_ideal: int = 1,
        carga_horaria: int = 60,
        creditos: int = 4,
        ementa: Optional[str] = None,
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Disciplina (
                    matriz_id, codigo, nome, semestre_ideal, carga_horaria, creditos, natureza, ementa
                )
                VALUES (?, ?, ?, ?, ?, ?, 'OBRIGATORIA', ?)
                """,
                (matriz_id, codigo, nome, semestre_ideal, carga_horaria, creditos, ementa),
            )
            return int(cur.lastrowid)

    def inserir_prerequisito_seed(
        self,
        disciplina_id: int,
        requisito_disciplina_id: int,
        tipo_requisito: str = "PRE_REQUISITO",
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO PreRequisito (disciplina_id, requisito_disciplina_id, tipo_requisito)
                VALUES (?, ?, ?)
                """,
                (disciplina_id, requisito_disciplina_id, tipo_requisito),
            )
            return int(cur.lastrowid)

    def inserir_periodo_seed(self, codigo: str, ano: int, semestre: int) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO PeriodoLetivo (codigo, ano, semestre, data_inicio, data_fim, status_periodo)
                VALUES (?, ?, ?, '2026-02-01', '2026-06-30', 'ENCERRADO')
                """,
                (codigo, ano, semestre),
            )
            return int(cur.lastrowid)

    def inserir_turma_seed(self, codigo_turma: str, disciplina_id: int, periodo_letivo_id: int) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Turma (
                    codigo_turma, disciplina_id, periodo_letivo_id, turno, vagas_totais, status_turma
                )
                VALUES (?, ?, ?, 'NOTURNO', 40, 'ENCERRADA')
                """,
                (codigo_turma, disciplina_id, periodo_letivo_id),
            )
            return int(cur.lastrowid)

    def inserir_aluno_seed(
        self,
        matricula: int,
        usuario_id: int,
        nome: str,
        email: str,
        cpf: str,
        curso_id: Optional[int] = None,
        status_academico: str = "ATIVO",
        ira: float = 8.0,
        telefone: str = "71988887777",
        data_nascimento: str = "2003-04-15",
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
        media_final: float,
        situacao: str = "APROVADO",
        percentual_frequencia: float = 95.0,
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
            return int(cur.lastrowid)

    # ------------------------------------------------------------------
    # Auditoria Interna Transacional
    # ------------------------------------------------------------------

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
        ts = data_hora or datetime.now(timezone.utc).isoformat()
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
                ts,
            ),
        )
        return int(cur.lastrowid)

    # ------------------------------------------------------------------
    # Consultas de Identidade, Disciplina e Aluno
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

    def buscar_disciplina_por_id(self, disciplina_id: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT id_disciplina, matriz_id, codigo, nome, semestre_ideal,
                       carga_horaria, creditos, natureza, ementa
                FROM Disciplina
                WHERE id_disciplina = ?
                """,
                (disciplina_id,),
            ).fetchone()
            return dict(row) if row else None

    def buscar_aluno_por_matricula(self, matricula: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT matricula, Usuario_id_usuario, nome, email, cpf,
                       telefone, data_nascimento, curso_id, status_academico, ira
                FROM Aluno
                WHERE matricula = ?
                """,
                (matricula,),
            ).fetchone()
            return dict(row) if row else None

    def buscar_aprovacao_interna_em_disciplina(
        self, aluno_matricula: int, disciplina_id: int
    ) -> Optional[dict[str, Any]]:
        """Busca a maior nota de aprovação em turma já cursada pelo aluno para a disciplina."""
        with self._lock:
            row = self.conn.execute(
                """
                SELECT mt.id_matricula_turma, mt.media_final, mt.percentual_frequencia,
                       mt.situacao, t.id_turma, t.codigo_turma
                FROM MatriculaTurma mt
                JOIN Turma t ON t.id_turma = mt.turma_id
                WHERE mt.aluno_matricula = ?
                  AND t.disciplina_id = ?
                  AND mt.situacao = 'APROVADO'
                ORDER BY COALESCE(mt.media_final, 0) DESC, mt.id_matricula_turma DESC
                LIMIT 1
                """,
                (aluno_matricula, disciplina_id),
            ).fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------
    # US1: EquivalenciaDisciplina
    # ------------------------------------------------------------------

    _SELECT_EQUIV = """
        SELECT e.id_equivalencia, e.disciplina_origem_id, e.disciplina_equivalente_id,
               e.portaria_aprovacao, e.ativa,
               d1.codigo AS disciplina_origem_codigo, d1.nome AS disciplina_origem_nome,
               d1.carga_horaria AS disciplina_origem_carga_horaria,
               d2.codigo AS disciplina_equivalente_codigo, d2.nome AS disciplina_equivalente_nome,
               d2.carga_horaria AS disciplina_equivalente_carga_horaria
        FROM EquivalenciaDisciplina e
        JOIN Disciplina d1 ON d1.id_disciplina = e.disciplina_origem_id
        JOIN Disciplina d2 ON d2.id_disciplina = e.disciplina_equivalente_id
    """

    @staticmethod
    def _row_para_equivalencia(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id_equivalencia": int(row["id_equivalencia"]),
            "disciplina_origem_id": int(row["disciplina_origem_id"]),
            "disciplina_origem_codigo": str(row["disciplina_origem_codigo"]),
            "disciplina_origem_nome": str(row["disciplina_origem_nome"]),
            "disciplina_origem_carga_horaria": int(row["disciplina_origem_carga_horaria"]),
            "disciplina_equivalente_id": int(row["disciplina_equivalente_id"]),
            "disciplina_equivalente_codigo": str(row["disciplina_equivalente_codigo"]),
            "disciplina_equivalente_nome": str(row["disciplina_equivalente_nome"]),
            "disciplina_equivalente_carga_horaria": int(row["disciplina_equivalente_carga_horaria"]),
            "portaria_aprovacao": row["portaria_aprovacao"],
            "ativa": bool(int(row["ativa"]) == 1),
        }

    def buscar_equivalencia_por_id(self, id_equivalencia: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                f"{self._SELECT_EQUIV} WHERE e.id_equivalencia = ?",
                (id_equivalencia,),
            ).fetchone()
            return self._row_para_equivalencia(row) if row else None

    def buscar_equivalencia_por_par(
        self, disciplina_origem_id: int, disciplina_equivalente_id: int
    ) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                f"{self._SELECT_EQUIV} WHERE e.disciplina_origem_id = ? AND e.disciplina_equivalente_id = ?",
                (disciplina_origem_id, disciplina_equivalente_id),
            ).fetchone()
            return self._row_para_equivalencia(row) if row else None

    def listar_equivalencias(
        self,
        disciplina_origem_id: Optional[int] = None,
        disciplina_equivalente_id: Optional[int] = None,
        ativa: Optional[bool] = None,
    ) -> list[dict[str, Any]]:
        clausulas: list[str] = []
        params: list[Any] = []
        if disciplina_origem_id is not None:
            clausulas.append("e.disciplina_origem_id = ?")
            params.append(disciplina_origem_id)
        if disciplina_equivalente_id is not None:
            clausulas.append("e.disciplina_equivalente_id = ?")
            params.append(disciplina_equivalente_id)
        if ativa is not None:
            clausulas.append("e.ativa = ?")
            params.append(1 if ativa else 0)
        where_sql = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""
        with self._lock:
            rows = self.conn.execute(
                f"{self._SELECT_EQUIV} {where_sql} ORDER BY e.id_equivalencia DESC",
                params,
            ).fetchall()
            return [self._row_para_equivalencia(r) for r in rows]

    def criar_equivalencia_com_auditoria(
        self,
        disciplina_origem_id: int,
        disciplina_equivalente_id: int,
        portaria_aprovacao: Optional[str],
        operador_usuario_id: int,
        ip_origem: str,
        dados_novos_json: str,
    ) -> dict[str, Any]:
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                cur = self.conn.execute(
                    """
                    INSERT INTO EquivalenciaDisciplina (
                        disciplina_origem_id, disciplina_equivalente_id, portaria_aprovacao, ativa
                    )
                    VALUES (?, ?, ?, 1)
                    """,
                    (disciplina_origem_id, disciplina_equivalente_id, portaria_aprovacao),
                )
                id_eq = int(cur.lastrowid)
                self._inserir_auditoria_tx(
                    usuario_id=operador_usuario_id,
                    entidade_afetada="EquivalenciaDisciplina",
                    id_registro_afetado=str(id_eq),
                    acao="CRIAR",
                    dados_anteriores=None,
                    dados_novos=dados_novos_json,
                    ip_origem=ip_origem,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise
            criada = self.buscar_equivalencia_por_id(id_eq)
            assert criada is not None
            return criada

    def atualizar_equivalencia_com_auditoria(
        self,
        id_equivalencia: int,
        portaria_aprovacao: Optional[str],
        ativa: bool,
        operador_usuario_id: int,
        ip_origem: str,
        dados_anteriores_json: str,
        dados_novos_json: str,
    ) -> dict[str, Any]:
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                self.conn.execute(
                    """
                    UPDATE EquivalenciaDisciplina
                    SET portaria_aprovacao = ?, ativa = ?
                    WHERE id_equivalencia = ?
                    """,
                    (portaria_aprovacao, 1 if ativa else 0, id_equivalencia),
                )
                self._inserir_auditoria_tx(
                    usuario_id=operador_usuario_id,
                    entidade_afetada="EquivalenciaDisciplina",
                    id_registro_afetado=str(id_equivalencia),
                    acao="ATUALIZAR",
                    dados_anteriores=dados_anteriores_json,
                    dados_novos=dados_novos_json,
                    ip_origem=ip_origem,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise
            atualizada = self.buscar_equivalencia_por_id(id_equivalencia)
            assert atualizada is not None
            return atualizada

    # ------------------------------------------------------------------
    # US2: SolicitacaoAproveitamento
    # ------------------------------------------------------------------

    _SELECT_SOLICITACAO = """
        SELECT s.*, a.nome AS aluno_nome,
               da.codigo AS disciplina_alvo_codigo, da.nome AS disciplina_alvo_nome,
               da.carga_horaria AS disciplina_alvo_carga_horaria,
               do.codigo AS disciplina_origem_codigo, do.nome AS disciplina_origem_nome
        FROM SolicitacaoAproveitamento s
        JOIN Aluno a ON a.matricula = s.aluno_matricula
        JOIN Disciplina da ON da.id_disciplina = s.disciplina_alvo_id
        LEFT JOIN Disciplina do ON do.id_disciplina = s.disciplina_origem_id
    """

    @staticmethod
    def _row_para_solicitacao(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id_solicitacao": int(row["id_solicitacao"]),
            "protocolo": str(row["protocolo"]),
            "aluno_matricula": int(row["aluno_matricula"]),
            "aluno_nome": str(row["aluno_nome"] or ""),
            "disciplina_alvo_id": int(row["disciplina_alvo_id"]),
            "disciplina_alvo_codigo": str(row["disciplina_alvo_codigo"]),
            "disciplina_alvo_nome": str(row["disciplina_alvo_nome"]),
            "disciplina_alvo_carga_horaria": int(row["disciplina_alvo_carga_horaria"]),
            "modalidade": str(row["modalidade"]),
            "disciplina_origem_id": (
                int(row["disciplina_origem_id"]) if row["disciplina_origem_id"] is not None else None
            ),
            "disciplina_origem_codigo": row["disciplina_origem_codigo"],
            "disciplina_origem_nome": row["disciplina_origem_nome"],
            "equivalencia_id": int(row["equivalencia_id"]) if row["equivalencia_id"] is not None else None,
            "instituicao_origem": row["instituicao_origem"],
            "disciplina_externa_nome": row["disciplina_externa_nome"],
            "carga_horaria_cursada": int(row["carga_horaria_cursada"]),
            "nota_obtida": round(float(row["nota_obtida"]), 2),
            "ementa_resumo": row["ementa_resumo"],
            "documentacao_comprobatoria": row["documentacao_comprobatoria"],
            "pre_validacao": json.loads(str(row["pre_validacao_detalhes_json"])),
            "status_solicitacao": str(row["status_solicitacao"]),
            "parecer_tecnico": row["parecer_tecnico"],
            "aberto_por_usuario_id": (
                int(row["aberto_por_usuario_id"]) if row["aberto_por_usuario_id"] is not None else None
            ),
            "deliberado_por_usuario_id": (
                int(row["deliberado_por_usuario_id"]) if row["deliberado_por_usuario_id"] is not None else None
            ),
            "aberto_em": str(row["aberto_em"]),
            "deliberado_em": row["deliberado_em"],
        }

    def buscar_solicitacao_por_id(self, id_solicitacao: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                f"{self._SELECT_SOLICITACAO} WHERE s.id_solicitacao = ?",
                (id_solicitacao,),
            ).fetchone()
            return self._row_para_solicitacao(row) if row else None

    def buscar_solicitacao_em_analise(
        self, aluno_matricula: int, disciplina_alvo_id: int
    ) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT id_solicitacao, protocolo
                FROM SolicitacaoAproveitamento
                WHERE aluno_matricula = ? AND disciplina_alvo_id = ? AND status_solicitacao = 'EM_ANALISE'
                """,
                (aluno_matricula, disciplina_alvo_id),
            ).fetchone()
            return dict(row) if row else None

    def gerar_numero_protocolo(self, ano_base: Optional[int] = None) -> str:
        ano = ano_base or datetime.now(timezone.utc).year
        prefixo = f"APR-{ano}-"
        with self._lock:
            row = self.conn.execute("SELECT COUNT(*) AS total FROM SolicitacaoAproveitamento").fetchone()
            seq = int(row["total"]) + 1 if row else 1
            candidato = f"{prefixo}{seq:06d}"
            while self.conn.execute(
                "SELECT 1 FROM SolicitacaoAproveitamento WHERE protocolo = ?",
                (candidato,),
            ).fetchone():
                seq += 1
                candidato = f"{prefixo}{seq:06d}"
            return candidato

    def criar_solicitacao_com_auditoria(
        self,
        protocolo: str,
        aluno_matricula: int,
        disciplina_alvo_id: int,
        modalidade: str,
        disciplina_origem_id: Optional[int],
        equivalencia_id: Optional[int],
        instituicao_origem: Optional[str],
        disciplina_externa_nome: Optional[str],
        carga_horaria_cursada: int,
        nota_obtida: float,
        ementa_resumo: Optional[str],
        documentacao_comprobatoria: Optional[str],
        pre_validacao_elegivel: bool,
        pre_validacao_detalhes_json: str,
        aberto_por_usuario_id: int,
        aberto_em: str,
        ip_origem: str,
        dados_novos_auditoria_json: str,
    ) -> dict[str, Any]:
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                cur = self.conn.execute(
                    """
                    INSERT INTO SolicitacaoAproveitamento (
                        protocolo, aluno_matricula, disciplina_alvo_id, modalidade,
                        disciplina_origem_id, equivalencia_id, instituicao_origem,
                        disciplina_externa_nome, carga_horaria_cursada, nota_obtida,
                        ementa_resumo, documentacao_comprobatoria,
                        pre_validacao_elegivel, pre_validacao_detalhes_json,
                        status_solicitacao, aberto_por_usuario_id, aberto_em
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'EM_ANALISE', ?, ?)
                    """,
                    (
                        protocolo,
                        aluno_matricula,
                        disciplina_alvo_id,
                        modalidade,
                        disciplina_origem_id,
                        equivalencia_id,
                        instituicao_origem,
                        disciplina_externa_nome,
                        carga_horaria_cursada,
                        nota_obtida,
                        ementa_resumo,
                        documentacao_comprobatoria,
                        1 if pre_validacao_elegivel else 0,
                        pre_validacao_detalhes_json,
                        aberto_por_usuario_id,
                        aberto_em,
                    ),
                )
                id_sol = int(cur.lastrowid)
                self._inserir_auditoria_tx(
                    usuario_id=aberto_por_usuario_id,
                    entidade_afetada="SolicitacaoAproveitamento",
                    id_registro_afetado=str(id_sol),
                    acao="PROTOCOLAR",
                    dados_anteriores=None,
                    dados_novos=dados_novos_auditoria_json,
                    ip_origem=ip_origem,
                    data_hora=aberto_em,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise
            criada = self.buscar_solicitacao_por_id(id_sol)
            assert criada is not None
            return criada

    def listar_solicitacoes(
        self,
        aluno_matricula: Optional[int] = None,
        disciplina_alvo_id: Optional[int] = None,
        modalidade: Optional[str] = None,
        status_solicitacao: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        clausulas: list[str] = []
        params: list[Any] = []
        if aluno_matricula is not None:
            clausulas.append("s.aluno_matricula = ?")
            params.append(aluno_matricula)
        if disciplina_alvo_id is not None:
            clausulas.append("s.disciplina_alvo_id = ?")
            params.append(disciplina_alvo_id)
        if modalidade is not None:
            clausulas.append("s.modalidade = ?")
            params.append(modalidade)
        if status_solicitacao is not None:
            clausulas.append("s.status_solicitacao = ?")
            params.append(status_solicitacao)
        where_sql = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""
        with self._lock:
            rows = self.conn.execute(
                f"{self._SELECT_SOLICITACAO} {where_sql} ORDER BY s.id_solicitacao DESC",
                params,
            ).fetchall()
            return [self._row_para_solicitacao(r) for r in rows]

    # ------------------------------------------------------------------
    # US3: Deliberação Atômica, DispensaDisciplina e Pré-Requisitos
    # ------------------------------------------------------------------

    _SELECT_DISPENSA = """
        SELECT dp.id_dispensa, dp.aluno_matricula, dp.disciplina_id,
               d.codigo AS disciplina_codigo, d.nome AS disciplina_nome,
               dp.solicitacao_id, s.protocolo, dp.modalidade,
               dp.nota_aproveitada, dp.carga_horaria_aproveitada, dp.reconhecido_em
        FROM DispensaDisciplina dp
        JOIN Disciplina d ON d.id_disciplina = dp.disciplina_id
        JOIN SolicitacaoAproveitamento s ON s.id_solicitacao = dp.solicitacao_id
    """

    @staticmethod
    def _row_para_dispensa(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id_dispensa": int(row["id_dispensa"]),
            "aluno_matricula": int(row["aluno_matricula"]),
            "disciplina_id": int(row["disciplina_id"]),
            "disciplina_codigo": str(row["disciplina_codigo"]),
            "disciplina_nome": str(row["disciplina_nome"]),
            "solicitacao_id": int(row["solicitacao_id"]),
            "protocolo": str(row["protocolo"]),
            "modalidade": str(row["modalidade"]),
            "nota_aproveitada": round(float(row["nota_aproveitada"]), 2),
            "carga_horaria_aproveitada": int(row["carga_horaria_aproveitada"]),
            "reconhecido_em": str(row["reconhecido_em"]),
        }

    def buscar_dispensa_por_aluno_e_disciplina(
        self, aluno_matricula: int, disciplina_id: int
    ) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                f"{self._SELECT_DISPENSA} WHERE dp.aluno_matricula = ? AND dp.disciplina_id = ?",
                (aluno_matricula, disciplina_id),
            ).fetchone()
            return self._row_para_dispensa(row) if row else None

    def buscar_dispensa_por_id(self, id_dispensa: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                f"{self._SELECT_DISPENSA} WHERE dp.id_dispensa = ?",
                (id_dispensa,),
            ).fetchone()
            return self._row_para_dispensa(row) if row else None

    def listar_dispensas_por_aluno(self, aluno_matricula: int) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                f"{self._SELECT_DISPENSA} WHERE dp.aluno_matricula = ? ORDER BY dp.id_dispensa DESC",
                (aluno_matricula,),
            ).fetchall()
            return [self._row_para_dispensa(r) for r in rows]

    def listar_pre_requisitos_da_disciplina(self, disciplina_id: int) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                """
                SELECT pr.requisito_disciplina_id, d.codigo, d.nome, pr.tipo_requisito
                FROM PreRequisito pr
                JOIN Disciplina d ON d.id_disciplina = pr.requisito_disciplina_id
                WHERE pr.disciplina_id = ? AND pr.tipo_requisito = 'PRE_REQUISITO'
                ORDER BY d.codigo ASC
                """,
                (disciplina_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def deliberar_solicitacao_atomico(
        self,
        id_solicitacao: int,
        decisao: str,
        parecer_tecnico: str,
        deliberado_por_usuario_id: int,
        deliberado_em: str,
        ip_origem: str,
        dados_anteriores_sol_json: str,
        dados_novos_sol_json: str,
        criar_dispensa: bool,
        aluno_matricula: int,
        disciplina_id: int,
        modalidade: str,
        nota_aproveitada: float,
        carga_horaria_aproveitada: int,
        dados_novos_dispensa_json: Optional[str] = None,
    ) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
        """Executa deliberação e eventual consolidação de DispensaDisciplina em única transação."""
        with self._lock:
            dispensa_id: Optional[int] = None
            try:
                self.conn.execute("BEGIN")
                self.conn.execute(
                    """
                    UPDATE SolicitacaoAproveitamento
                    SET status_solicitacao = ?, parecer_tecnico = ?,
                        deliberado_por_usuario_id = ?, deliberado_em = ?
                    WHERE id_solicitacao = ?
                    """,
                    (decisao, parecer_tecnico, deliberado_por_usuario_id, deliberado_em, id_solicitacao),
                )
                self._inserir_auditoria_tx(
                    usuario_id=deliberado_por_usuario_id,
                    entidade_afetada="SolicitacaoAproveitamento",
                    id_registro_afetado=str(id_solicitacao),
                    acao=decisao,
                    dados_anteriores=dados_anteriores_sol_json,
                    dados_novos=dados_novos_sol_json,
                    ip_origem=ip_origem,
                    data_hora=deliberado_em,
                )

                if criar_dispensa:
                    cur_dp = self.conn.execute(
                        """
                        INSERT INTO DispensaDisciplina (
                            aluno_matricula, disciplina_id, solicitacao_id,
                            modalidade, nota_aproveitada, carga_horaria_aproveitada, reconhecido_em
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            aluno_matricula,
                            disciplina_id,
                            id_solicitacao,
                            modalidade,
                            nota_aproveitada,
                            carga_horaria_aproveitada,
                            deliberado_em,
                        ),
                    )
                    dispensa_id = int(cur_dp.lastrowid)
                    self._inserir_auditoria_tx(
                        usuario_id=deliberado_por_usuario_id,
                        entidade_afetada="DispensaDisciplina",
                        id_registro_afetado=str(dispensa_id),
                        acao="CONSOLIDAR_DISPENSA",
                        dados_anteriores=None,
                        dados_novos=dados_novos_dispensa_json,
                        ip_origem=ip_origem,
                        data_hora=deliberado_em,
                    )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

            sol_atualizada = self.buscar_solicitacao_por_id(id_solicitacao)
            assert sol_atualizada is not None
            dispensa = self.buscar_dispensa_por_id(dispensa_id) if dispensa_id is not None else None
            return sol_atualizada, dispensa

    # ------------------------------------------------------------------
    # US4: Auditoria LGPD
    # ------------------------------------------------------------------

    def listar_auditoria(
        self,
        entidade_afetada: Optional[str] = None,
        id_registro_afetado: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        placeholders = ", ".join("?" for _ in ENTIDADES_AUDITORIA_MODULO)
        clausulas = [f"entidade_afetada IN ({placeholders})"]
        params: list[Any] = list(ENTIDADES_AUDITORIA_MODULO)
        if entidade_afetada is not None and entidade_afetada.strip():
            clausulas.append("entidade_afetada = ?")
            params.append(entidade_afetada.strip())
        if id_registro_afetado is not None and str(id_registro_afetado).strip():
            clausulas.append("id_registro_afetado = ?")
            params.append(str(id_registro_afetado).strip())
        where_sql = " AND ".join(clausulas)
        with self._lock:
            rows = self.conn.execute(
                f"SELECT * FROM LogAuditoriaSistema WHERE {where_sql} ORDER BY id_auditoria DESC",
                params,
            ).fetchall()
            return [dict(r) for r in rows]


_DEFAULT_REPO: Optional[AproveitamentoRepository] = None
_DEFAULT_REPO_LOCK = threading.Lock()


def get_repository() -> AproveitamentoRepository:
    """Dependência FastAPI que fornece o repositório configurado para o ambiente."""
    global _DEFAULT_REPO
    with _DEFAULT_REPO_LOCK:
        if _DEFAULT_REPO is None:
            db_path = os.getenv("SGA_APROVEITAMENTO_DB_PATH", ":memory:")
            _DEFAULT_REPO = AproveitamentoRepository(db_path=db_path)
        return _DEFAULT_REPO
