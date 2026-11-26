"""Persistência relacional SQLite transacional para emissão documental e Acervo Digital MEC (SGA-25)."""

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

CREATE TABLE IF NOT EXISTS AvaliacaoNota (
    id_avaliacao INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula_turma_id INTEGER NOT NULL,
    etapa VARCHAR(30) NOT NULL,
    nota DECIMAL(4,2) NOT NULL CHECK (nota >= 0.00 AND nota <= 10.00),
    peso DECIMAL(4,2) NOT NULL DEFAULT 1.00,
    data_lancamento DATETIME NOT NULL,
    observacao VARCHAR(255) NULL,
    UNIQUE (matricula_turma_id, etapa),
    CONSTRAINT fk_AvaliacaoNota_MatriculaTurma
        FOREIGN KEY (matricula_turma_id)
        REFERENCES MatriculaTurma (id_matricula_turma)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS RegistroFrequencia (
    id_frequencia INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula_turma_id INTEGER NOT NULL,
    data_aula DATE NOT NULL,
    presente BOOLEAN NOT NULL DEFAULT 1,
    quantidade_aulas INTEGER NOT NULL DEFAULT 2,
    justificativa VARCHAR(255) NULL,
    UNIQUE (matricula_turma_id, data_aula),
    CONSTRAINT fk_RegistroFrequencia_MatriculaTurma
        FOREIGN KEY (matricula_turma_id)
        REFERENCES MatriculaTurma (id_matricula_turma)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS DocumentoAcademico (
    id_documento INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_documento VARCHAR(40) NOT NULL
        CHECK (tipo_documento IN ('DIARIO_OPERACIONAL', 'ATA_NOTAS', 'DIPLOMA_DIGITAL')),
    aluno_matricula INTEGER NULL,
    turma_id INTEGER NULL,
    curso_id INTEGER NULL,
    numero_registro VARCHAR(60) NULL UNIQUE,
    codigo_verificacao VARCHAR(64) NOT NULL UNIQUE,
    hash_sha256 VARCHAR(64) NOT NULL,
    url_validacao_qrcode VARCHAR(255) NOT NULL,
    conteudo_json TEXT NOT NULL,
    emitido_por_usuario_id INTEGER NULL,
    emitido_em DATETIME NOT NULL,
    valido BOOLEAN NOT NULL DEFAULT 1,
    motivo_revogacao TEXT NULL,
    revogado_em DATETIME NULL,
    CONSTRAINT chk_documento_vinculo CHECK (
        (tipo_documento = 'DIPLOMA_DIGITAL' AND aluno_matricula IS NOT NULL AND curso_id IS NOT NULL)
        OR (tipo_documento IN ('DIARIO_OPERACIONAL', 'ATA_NOTAS') AND turma_id IS NOT NULL)
    ),
    CONSTRAINT fk_DocumentoAcademico_Aluno
        FOREIGN KEY (aluno_matricula)
        REFERENCES Aluno (matricula)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_DocumentoAcademico_Turma
        FOREIGN KEY (turma_id)
        REFERENCES Turma (id_turma)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_DocumentoAcademico_Curso
        FOREIGN KEY (curso_id)
        REFERENCES Curso (id_curso)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_DocumentoAcademico_Emissor
        FOREIGN KEY (emitido_por_usuario_id)
        REFERENCES Usuario (id_usuario)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_documento_aluno ON DocumentoAcademico (aluno_matricula);
CREATE INDEX IF NOT EXISTS idx_documento_turma ON DocumentoAcademico (turma_id);
CREATE INDEX IF NOT EXISTS idx_documento_codigo ON DocumentoAcademico (codigo_verificacao);
CREATE INDEX IF NOT EXISTS idx_documento_tipo_valido ON DocumentoAcademico (tipo_documento, valido);
CREATE UNIQUE INDEX IF NOT EXISTS uq_diploma_ativo_aluno_curso
    ON DocumentoAcademico (aluno_matricula, curso_id)
    WHERE tipo_documento = 'DIPLOMA_DIGITAL' AND valido = 1;

CREATE TABLE IF NOT EXISTS AcervoDigitalMEC (
    id_acervo INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id INTEGER NOT NULL UNIQUE,
    portaria_referencia VARCHAR(40) NOT NULL DEFAULT 'PORTARIA_MEC_360_2022'
        CHECK (portaria_referencia IN ('PORTARIA_MEC_360_2022', 'PORTARIA_MEC_315_2018')),
    formato_arquivo VARCHAR(30) NOT NULL DEFAULT 'PDF_A_ASSINADO',
    assinatura_icp_brasil VARCHAR(128) NOT NULL,
    carimbo_tempo DATETIME NOT NULL,
    prazo_guarda VARCHAR(30) NOT NULL DEFAULT 'PERMANENTE',
    status_custodia VARCHAR(25) NOT NULL DEFAULT 'INTEGRO'
        CHECK (status_custodia IN ('INTEGRO', 'REVOGADO', 'CORROMPIDO')),
    CONSTRAINT fk_AcervoDigitalMEC_Documento
        FOREIGN KEY (documento_id)
        REFERENCES DocumentoAcademico (id_documento)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_acervo_documento ON AcervoDigitalMEC (documento_id);

CREATE TRIGGER IF NOT EXISTS trg_bloquear_delete_documento_academico
BEFORE DELETE ON DocumentoAcademico
BEGIN
    SELECT RAISE(ABORT, 'Exclusao fisica de DocumentoAcademico proibida pela guarda permanente do MEC.');
END;

CREATE TRIGGER IF NOT EXISTS trg_bloquear_delete_acervo_mec
BEFORE DELETE ON AcervoDigitalMEC
BEGIN
    SELECT RAISE(ABORT, 'Exclusao fisica de AcervoDigitalMEC proibida pela guarda permanente do MEC.');
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
    """Abre conexão SQLite com chaves estrangeiras ativadas, transações explícitas e suporte multi-thread."""
    conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def inicializar_esquema(conn: sqlite3.Connection) -> None:
    """Cria tabelas, índices, triggers de guarda permanente MEC e semeia perfis RBAC."""
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
    conn.commit()


class DocumentoRepository:
    """Repositório transacional SQLite para documentos acadêmicos, Acervo MEC e auditoria."""

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
        dados_identificacao: Optional[str] = None,
    ) -> int:
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

    def inserir_departamento_seed(self, codigo: str, nome: str, sigla: str) -> int:
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO Departamento (codigo, nome, sigla, ativo) VALUES (?, ?, ?, 1)",
                (codigo, nome, sigla),
            )
            self.conn.commit()
            return int(cur.lastrowid)

    def inserir_professor_seed(
        self,
        nome: str,
        email: str,
        cpf: str,
        departamento: str,
        titulacao: str = "Doutorado",
        usuario_id: Optional[int] = None,
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Professor (nome, email, cpf, departamento, titulacao, Usuario_id_usuario)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (nome, email, cpf, departamento, titulacao, usuario_id),
            )
            self.conn.commit()
            return int(cur.lastrowid)

    def inserir_curso_seed(
        self,
        codigo_mec: str,
        nome: str,
        departamento_id: int,
        grau_academico: str = "Bacharelado",
        modalidade: str = "PRESENCIAL",
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    codigo_mec,
                    nome,
                    grau_academico,
                    modalidade,
                    carga_horaria_total,
                    duracao_semestres,
                    departamento_id,
                    coordenador_id,
                ),
            )
            self.conn.commit()
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
            self.conn.commit()
            return int(cur.lastrowid)

    def inserir_disciplina_seed(
        self,
        matriz_id: int,
        codigo: str,
        nome: str,
        semestre_ideal: int = 4,
        carga_horaria: int = 60,
        creditos: int = 4,
        natureza: str = "OBRIGATORIA",
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Disciplina (
                    matriz_id, codigo, nome, semestre_ideal, carga_horaria, creditos, natureza
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (matriz_id, codigo, nome, semestre_ideal, carga_horaria, creditos, natureza),
            )
            self.conn.commit()
            return int(cur.lastrowid)

    def inserir_periodo_seed(
        self,
        codigo: str,
        ano: int,
        semestre: int,
        data_inicio: str = "2026-08-01",
        data_fim: str = "2026-12-15",
        status_periodo: str = "EM_ANDAMENTO",
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO PeriodoLetivo (codigo, ano, semestre, data_inicio, data_fim, status_periodo)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (codigo, ano, semestre, data_inicio, data_fim, status_periodo),
            )
            self.conn.commit()
            return int(cur.lastrowid)

    def inserir_turma_seed(
        self,
        codigo_turma: str,
        disciplina_id: int,
        periodo_letivo_id: int,
        professor_id: Optional[int] = None,
        turno: str = "NOTURNO",
        vagas_totais: int = 40,
        status_turma: str = "ABERTA",
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO Turma (
                    codigo_turma, disciplina_id, periodo_letivo_id, professor_id,
                    turno, vagas_totais, vagas_ocupadas, status_turma
                )
                VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (codigo_turma, disciplina_id, periodo_letivo_id, professor_id, turno, vagas_totais, status_turma),
            )
            self.conn.commit()
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
        ira: float = 0.0,
        telefone: Optional[str] = "71999990000",
        data_nascimento: Optional[str] = "2002-05-10",
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
            self.conn.commit()
            return matricula

    def inserir_matricula_turma_seed(
        self,
        aluno_matricula: int,
        turma_id: int,
        media_final: Optional[float] = None,
        percentual_frequencia: float = 100.0,
        situacao: str = "CURSANDO",
        data_matricula: Optional[str] = None,
    ) -> int:
        ts = data_matricula or datetime.now(timezone.utc).isoformat()
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
            self.conn.commit()
            return int(cur.lastrowid)

    def inserir_avaliacao_seed(
        self,
        matricula_turma_id: int,
        etapa: str,
        nota: float,
        peso: float = 1.0,
        data_lancamento: Optional[str] = None,
        observacao: Optional[str] = None,
    ) -> int:
        ts = data_lancamento or datetime.now(timezone.utc).isoformat()
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO AvaliacaoNota (
                    matricula_turma_id, etapa, nota, peso, data_lancamento, observacao
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (matricula_turma_id, etapa, nota, peso, ts, observacao),
            )
            self.conn.commit()
            return int(cur.lastrowid)

    def inserir_frequencia_seed(
        self,
        matricula_turma_id: int,
        data_aula: str,
        presente: bool = True,
        quantidade_aulas: int = 2,
        justificativa: Optional[str] = None,
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """
                INSERT INTO RegistroFrequencia (
                    matricula_turma_id, data_aula, presente, quantidade_aulas, justificativa
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (matricula_turma_id, data_aula, 1 if presente else 0, quantidade_aulas, justificativa),
            )
            self.conn.commit()
            return int(cur.lastrowid)

    # ------------------------------------------------------------------
    # Consultas de Identidade, Turma e Aluno
    # ------------------------------------------------------------------

    def buscar_usuario_por_id(self, usuario_id: int) -> Optional[dict[str, Any]]:
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

    def buscar_turma_completa(self, turma_id: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT t.id_turma, t.codigo_turma, t.turno, t.vagas_totais, t.vagas_ocupadas, t.status_turma,
                       d.id_disciplina, d.codigo AS disciplina_codigo, d.nome AS disciplina_nome,
                       d.carga_horaria AS disciplina_carga_horaria, d.creditos AS disciplina_creditos,
                       p.id_periodo, p.codigo AS periodo_codigo, p.ano AS periodo_ano, p.semestre AS periodo_semestre,
                       pr.id AS professor_id, pr.nome AS professor_nome, pr.titulacao AS professor_titulacao
                FROM Turma t
                JOIN Disciplina d ON d.id_disciplina = t.disciplina_id
                JOIN PeriodoLetivo p ON p.id_periodo = t.periodo_letivo_id
                LEFT JOIN Professor pr ON pr.id = t.professor_id
                WHERE t.id_turma = ?
                """,
                (turma_id,),
            ).fetchone()
            return dict(row) if row else None

    def listar_matriculas_da_turma_com_notas_e_frequencias(self, turma_id: int) -> list[dict[str, Any]]:
        with self._lock:
            matriculas = self.conn.execute(
                """
                SELECT mt.id_matricula_turma, mt.aluno_matricula, mt.media_final,
                       mt.percentual_frequencia, mt.situacao, mt.data_matricula,
                       a.nome AS aluno_nome, a.status_academico
                FROM MatriculaTurma mt
                JOIN Aluno a ON a.matricula = mt.aluno_matricula
                WHERE mt.turma_id = ?
                ORDER BY LOWER(COALESCE(a.nome, '')), mt.aluno_matricula
                """,
                (turma_id,),
            ).fetchall()

            resultado: list[dict[str, Any]] = []
            for mat in matriculas:
                mt_id = int(mat["id_matricula_turma"])
                avaliacoes = self.conn.execute(
                    """
                    SELECT etapa, nota, peso, data_lancamento, observacao
                    FROM AvaliacaoNota
                    WHERE matricula_turma_id = ?
                    ORDER BY id_avaliacao ASC
                    """,
                    (mt_id,),
                ).fetchall()
                frequencias = self.conn.execute(
                    """
                    SELECT data_aula, presente, quantidade_aulas, justificativa
                    FROM RegistroFrequencia
                    WHERE matricula_turma_id = ?
                    ORDER BY data_aula ASC
                    """,
                    (mt_id,),
                ).fetchall()
                item = dict(mat)
                item["avaliacoes"] = [dict(av) for av in avaliacoes]
                item["frequencias"] = [dict(fr) for fr in frequencias]
                resultado.append(item)
            return resultado

    def buscar_aluno_com_curso(self, matricula: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT a.matricula, a.Usuario_id_usuario, a.nome, a.email, a.cpf,
                       a.telefone, a.data_nascimento, a.curso_id, a.status_academico, a.ira,
                       c.codigo_mec AS curso_codigo_mec, c.nome AS curso_nome,
                       c.grau_academico AS curso_grau_academico, c.modalidade AS curso_modalidade,
                       c.carga_horaria_total AS curso_carga_horaria_total,
                       c.duracao_semestres AS curso_duracao_semestres
                FROM Aluno a
                LEFT JOIN Curso c ON c.id_curso = a.curso_id
                WHERE a.matricula = ?
                """,
                (matricula,),
            ).fetchone()
            return dict(row) if row else None

    def buscar_diploma_ativo_por_aluno_e_curso(self, aluno_matricula: int, curso_id: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                """
                SELECT id_documento, codigo_verificacao, numero_registro, emitido_em
                FROM DocumentoAcademico
                WHERE tipo_documento = 'DIPLOMA_DIGITAL'
                  AND aluno_matricula = ?
                  AND curso_id = ?
                  AND valido = 1
                """,
                (aluno_matricula, curso_id),
            ).fetchone()
            return dict(row) if row else None

    def buscar_por_numero_registro(self, numero_registro: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                "SELECT id_documento, numero_registro FROM DocumentoAcademico WHERE numero_registro = ?",
                (numero_registro,),
            ).fetchone()
            return dict(row) if row else None

    def codigo_verificacao_existe(self, codigo_verificacao: str) -> bool:
        with self._lock:
            row = self.conn.execute(
                "SELECT 1 FROM DocumentoAcademico WHERE codigo_verificacao = ?",
                (codigo_verificacao,),
            ).fetchone()
            return row is not None

    def gerar_numero_registro_diploma(self, ano_base: Optional[int] = None) -> str:
        ano = ano_base or datetime.now(timezone.utc).year
        prefixo = f"DIP-{ano}-"
        with self._lock:
            row = self.conn.execute(
                "SELECT COUNT(*) AS total FROM DocumentoAcademico WHERE tipo_documento = 'DIPLOMA_DIGITAL'",
            ).fetchone()
            seq = int(row["total"]) + 1 if row else 1
            candidato = f"{prefixo}{seq:06d}"
            while self.conn.execute(
                "SELECT 1 FROM DocumentoAcademico WHERE numero_registro = ?",
                (candidato,),
            ).fetchone():
                seq += 1
                candidato = f"{prefixo}{seq:06d}"
            return candidato

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
    # Persistência Atômica de DocumentoAcademico + AcervoDigitalMEC
    # ------------------------------------------------------------------

    @staticmethod
    def _row_para_documento_completo(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id_documento": int(row["id_documento"]),
            "tipo_documento": str(row["tipo_documento"]),
            "aluno_matricula": int(row["aluno_matricula"]) if row["aluno_matricula"] is not None else None,
            "turma_id": int(row["turma_id"]) if row["turma_id"] is not None else None,
            "curso_id": int(row["curso_id"]) if row["curso_id"] is not None else None,
            "numero_registro": row["numero_registro"],
            "codigo_verificacao": str(row["codigo_verificacao"]),
            "hash_sha256": str(row["hash_sha256"]),
            "url_validacao_qrcode": str(row["url_validacao_qrcode"]),
            "conteudo_json_bruto": str(row["conteudo_json"]),
            "conteudo": json.loads(str(row["conteudo_json"])),
            "emitido_por_usuario_id": (
                int(row["emitido_por_usuario_id"]) if row["emitido_por_usuario_id"] is not None else None
            ),
            "emitido_em": str(row["emitido_em"]),
            "valido": bool(int(row["valido"]) == 1),
            "motivo_revogacao": row["motivo_revogacao"],
            "revogado_em": row["revogado_em"],
            "acervo_mec": {
                "id_acervo": int(row["id_acervo"]),
                "documento_id": int(row["documento_id"]),
                "portaria_referencia": str(row["portaria_referencia"]),
                "formato_arquivo": str(row["formato_arquivo"]),
                "assinatura_icp_brasil": str(row["assinatura_icp_brasil"]),
                "carimbo_tempo": str(row["carimbo_tempo"]),
                "prazo_guarda": str(row["prazo_guarda"]),
                "status_custodia": str(row["status_custodia"]),
            },
        }

    def criar_documento_com_acervo_e_auditoria(
        self,
        tipo_documento: str,
        aluno_matricula: Optional[int],
        turma_id: Optional[int],
        curso_id: Optional[int],
        numero_registro: Optional[str],
        codigo_verificacao: str,
        hash_sha256: str,
        url_validacao_qrcode: str,
        conteudo_json: str,
        emitido_por_usuario_id: int,
        emitido_em: str,
        portaria_referencia: str,
        formato_arquivo: str,
        assinatura_icp_brasil: str,
        carimbo_tempo: str,
        prazo_guarda: str,
        ip_origem: str,
        dados_novos_auditoria_json: str,
    ) -> dict[str, Any]:
        """Grava atomicamente DocumentoAcademico, AcervoDigitalMEC (1:1) e LogAuditoriaSistema."""
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                cur_doc = self.conn.execute(
                    """
                    INSERT INTO DocumentoAcademico (
                        tipo_documento, aluno_matricula, turma_id, curso_id, numero_registro,
                        codigo_verificacao, hash_sha256, url_validacao_qrcode, conteudo_json,
                        emitido_por_usuario_id, emitido_em, valido
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        tipo_documento,
                        aluno_matricula,
                        turma_id,
                        curso_id,
                        numero_registro,
                        codigo_verificacao,
                        hash_sha256,
                        url_validacao_qrcode,
                        conteudo_json,
                        emitido_por_usuario_id,
                        emitido_em,
                    ),
                )
                documento_id = int(cur_doc.lastrowid)

                self.conn.execute(
                    """
                    INSERT INTO AcervoDigitalMEC (
                        documento_id, portaria_referencia, formato_arquivo,
                        assinatura_icp_brasil, carimbo_tempo, prazo_guarda, status_custodia
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'INTEGRO')
                    """,
                    (
                        documento_id,
                        portaria_referencia,
                        formato_arquivo,
                        assinatura_icp_brasil,
                        carimbo_tempo,
                        prazo_guarda,
                    ),
                )

                self._inserir_auditoria_tx(
                    usuario_id=emitido_por_usuario_id,
                    entidade_afetada="DocumentoAcademico",
                    id_registro_afetado=str(documento_id),
                    acao="EMITIR",
                    dados_anteriores=None,
                    dados_novos=dados_novos_auditoria_json,
                    ip_origem=ip_origem,
                    data_hora=emitido_em,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

            criado = self.buscar_documento_por_id(documento_id)
            assert criado is not None
            return criado

    # ------------------------------------------------------------------
    # Consultas de Documentos, Integridade, Revogação e Auditoria
    # ------------------------------------------------------------------

    _SELECT_DOC_COMPLETO = """
        SELECT d.id_documento, d.tipo_documento, d.aluno_matricula, d.turma_id, d.curso_id,
               d.numero_registro, d.codigo_verificacao, d.hash_sha256, d.url_validacao_qrcode,
               d.conteudo_json, d.emitido_por_usuario_id, d.emitido_em, d.valido,
               d.motivo_revogacao, d.revogado_em,
               a.id_acervo, a.documento_id, a.portaria_referencia, a.formato_arquivo,
               a.assinatura_icp_brasil, a.carimbo_tempo, a.prazo_guarda, a.status_custodia
        FROM DocumentoAcademico d
        JOIN AcervoDigitalMEC a ON a.documento_id = d.id_documento
    """

    def buscar_documento_por_id(self, id_documento: int) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                f"{self._SELECT_DOC_COMPLETO} WHERE d.id_documento = ?",
                (id_documento,),
            ).fetchone()
            return self._row_para_documento_completo(row) if row else None

    def buscar_documento_por_codigo(self, codigo_verificacao: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self.conn.execute(
                f"{self._SELECT_DOC_COMPLETO} WHERE d.codigo_verificacao = ?",
                (codigo_verificacao,),
            ).fetchone()
            return self._row_para_documento_completo(row) if row else None

    def listar_documentos(
        self,
        tipo_documento: Optional[str] = None,
        aluno_matricula: Optional[int] = None,
        turma_id: Optional[int] = None,
        periodo_letivo_codigo: Optional[str] = None,
        valido: Optional[bool] = None,
    ) -> list[dict[str, Any]]:
        clausulas: list[str] = []
        params: list[Any] = []
        if tipo_documento is not None:
            clausulas.append("d.tipo_documento = ?")
            params.append(tipo_documento)
        if aluno_matricula is not None:
            clausulas.append("d.aluno_matricula = ?")
            params.append(aluno_matricula)
        if turma_id is not None:
            clausulas.append("d.turma_id = ?")
            params.append(turma_id)
        if periodo_letivo_codigo is not None and periodo_letivo_codigo.strip():
            clausulas.append("p.codigo = ?")
            params.append(periodo_letivo_codigo.strip())
        if valido is not None:
            clausulas.append("d.valido = ?")
            params.append(1 if valido else 0)

        where_sql = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""
        sql = f"""
            SELECT d.id_documento, d.tipo_documento, d.aluno_matricula, d.turma_id, d.curso_id,
                   d.numero_registro, d.codigo_verificacao, d.hash_sha256, d.url_validacao_qrcode,
                   d.emitido_por_usuario_id, d.emitido_em, d.valido, d.motivo_revogacao, d.revogado_em,
                   a.portaria_referencia, a.prazo_guarda, a.status_custodia
            FROM DocumentoAcademico d
            JOIN AcervoDigitalMEC a ON a.documento_id = d.id_documento
            LEFT JOIN Turma t ON t.id_turma = d.turma_id
            LEFT JOIN PeriodoLetivo p ON p.id_periodo = t.periodo_letivo_id
            {where_sql}
            ORDER BY d.id_documento DESC
        """
        with self._lock:
            rows = self.conn.execute(sql, params).fetchall()
            return [
                {
                    "id_documento": int(r["id_documento"]),
                    "tipo_documento": str(r["tipo_documento"]),
                    "aluno_matricula": int(r["aluno_matricula"]) if r["aluno_matricula"] is not None else None,
                    "turma_id": int(r["turma_id"]) if r["turma_id"] is not None else None,
                    "curso_id": int(r["curso_id"]) if r["curso_id"] is not None else None,
                    "numero_registro": r["numero_registro"],
                    "codigo_verificacao": str(r["codigo_verificacao"]),
                    "hash_sha256": str(r["hash_sha256"]),
                    "url_validacao_qrcode": str(r["url_validacao_qrcode"]),
                    "emitido_por_usuario_id": (
                        int(r["emitido_por_usuario_id"]) if r["emitido_por_usuario_id"] is not None else None
                    ),
                    "emitido_em": str(r["emitido_em"]),
                    "valido": bool(int(r["valido"]) == 1),
                    "motivo_revogacao": r["motivo_revogacao"],
                    "revogado_em": r["revogado_em"],
                    "portaria_referencia": str(r["portaria_referencia"]),
                    "prazo_guarda": str(r["prazo_guarda"]),
                    "status_custodia": str(r["status_custodia"]),
                }
                for r in rows
            ]

    def registrar_verificacao_integridade(
        self,
        id_documento: int,
        novo_status_custodia: str,
        atualizar_custodia: bool,
        operador_usuario_id: int,
        ip_origem: str,
        dados_anteriores_json: Optional[str],
        dados_novos_json: str,
        verificado_em: str,
    ) -> None:
        """Atualiza status de custódia (se corrompido) e registra auditoria VERIFICAR_INTEGRIDADE."""
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                if atualizar_custodia:
                    self.conn.execute(
                        "UPDATE AcervoDigitalMEC SET status_custodia = ? WHERE documento_id = ?",
                        (novo_status_custodia, id_documento),
                    )
                self._inserir_auditoria_tx(
                    usuario_id=operador_usuario_id,
                    entidade_afetada="DocumentoAcademico",
                    id_registro_afetado=str(id_documento),
                    acao="VERIFICAR_INTEGRIDADE",
                    dados_anteriores=dados_anteriores_json,
                    dados_novos=dados_novos_json,
                    ip_origem=ip_origem,
                    data_hora=verificado_em,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

    def revogar_documento_atomico(
        self,
        id_documento: int,
        motivo_revogacao: str,
        revogado_em: str,
        operador_usuario_id: int,
        ip_origem: str,
        dados_anteriores_json: str,
        dados_novos_json: str,
    ) -> dict[str, Any]:
        """Revoga o documento sem exclusão física, marca Acervo como REVOGADO e audita REVOGAR."""
        with self._lock:
            try:
                self.conn.execute("BEGIN")
                self.conn.execute(
                    """
                    UPDATE DocumentoAcademico
                    SET valido = 0, motivo_revogacao = ?, revogado_em = ?
                    WHERE id_documento = ?
                    """,
                    (motivo_revogacao, revogado_em, id_documento),
                )
                self.conn.execute(
                    "UPDATE AcervoDigitalMEC SET status_custodia = 'REVOGADO' WHERE documento_id = ?",
                    (id_documento,),
                )
                self._inserir_auditoria_tx(
                    usuario_id=operador_usuario_id,
                    entidade_afetada="DocumentoAcademico",
                    id_registro_afetado=str(id_documento),
                    acao="REVOGAR",
                    dados_anteriores=dados_anteriores_json,
                    dados_novos=dados_novos_json,
                    ip_origem=ip_origem,
                    data_hora=revogado_em,
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

            atualizado = self.buscar_documento_por_id(id_documento)
            assert atualizado is not None
            return atualizado

    def listar_auditoria(self, id_documento: Optional[str] = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM LogAuditoriaSistema WHERE entidade_afetada = 'DocumentoAcademico'"
        params: list[Any] = []
        if id_documento is not None and str(id_documento).strip():
            sql += " AND id_registro_afetado = ?"
            params.append(str(id_documento).strip())
        sql += " ORDER BY id_auditoria DESC"
        with self._lock:
            rows = self.conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]


_DEFAULT_REPO: Optional[DocumentoRepository] = None
_DEFAULT_REPO_LOCK = threading.Lock()


def get_repository() -> DocumentoRepository:
    """Dependência FastAPI que fornece o repositório configurado para o ambiente."""
    global _DEFAULT_REPO
    with _DEFAULT_REPO_LOCK:
        if _DEFAULT_REPO is None:
            db_path = os.getenv("SGA_DOCUMENTOS_DB_PATH", ":memory:")
            _DEFAULT_REPO = DocumentoRepository(db_path=db_path)
        return _DEFAULT_REPO
