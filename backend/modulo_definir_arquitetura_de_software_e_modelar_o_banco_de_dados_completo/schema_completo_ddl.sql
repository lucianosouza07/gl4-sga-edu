-- =============================================================================
-- SGA-EDU: DDL Completo do Banco de Dados Institucional (SGA-18)
-- Módulo: Definir arquitetura de software e modelar o banco de dados completo
-- SGBD Alvo: MySQL 8.0+ (InnoDB, utf8mb4_unicode_ci) / Compatível com SQLite 3
-- Total de Entidades: 33 tabelas distribuídas em 6 domínios
-- =============================================================================

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- =============================================================================
-- DOMÍNIO 1 & 2 (BASE): IDENTIDADE, RBAC, ATORES, DEPARTAMENTO E CURSO
-- =============================================================================

-- 1. Tabela Perfil (RBAC)
CREATE TABLE IF NOT EXISTS `Perfil` (
  `id_perfil` INT NOT NULL AUTO_INCREMENT,
  `nome_perfil` VARCHAR(50) NOT NULL UNIQUE,
  `descricao` VARCHAR(255) NULL,
  PRIMARY KEY (`id_perfil`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 2. Tabela Usuario (Identidade Central e Autenticação)
CREATE TABLE IF NOT EXISTS `Usuario` (
  `id_usuario` INT NOT NULL AUTO_INCREMENT,
  `login` VARCHAR(255) NOT NULL UNIQUE,
  `senha_hash` VARCHAR(255) NOT NULL,
  `perfil_RBAC` INT NOT NULL,
  `tokenMFA` VARCHAR(45) NULL,
  `statusCONTA` INT NOT NULL DEFAULT 1,
  `dadosIdentificacao` VARCHAR(255) NULL,
  `criado_em` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_usuario`),
  INDEX `fk_Usuario_Perfil_idx` (`perfil_RBAC` ASC) VISIBLE,
  CONSTRAINT `fk_Usuario_Perfil`
    FOREIGN KEY (`perfil_RBAC`)
    REFERENCES `Perfil` (`id_perfil`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 3. Tabela Departamento (Unidades Acadêmicas)
CREATE TABLE IF NOT EXISTS `Departamento` (
  `id_departamento` INT NOT NULL AUTO_INCREMENT,
  `codigo` VARCHAR(20) NOT NULL UNIQUE,
  `nome` VARCHAR(100) NOT NULL UNIQUE,
  `sigla` VARCHAR(15) NOT NULL UNIQUE,
  `ativo` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`id_departamento`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 4. Tabela Professor (Especialização Docente - compatível com GL4-34 / SGA-16)
CREATE TABLE IF NOT EXISTS `Professor` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(120) NOT NULL,
  `email` VARCHAR(120) NOT NULL UNIQUE,
  `cpf` VARCHAR(14) NOT NULL UNIQUE,
  `telefone` VARCHAR(20) NULL,
  `departamento` VARCHAR(80) NOT NULL,
  `titulacao` VARCHAR(50) NOT NULL,
  `areaAtuacao` VARCHAR(100) NULL,
  `Usuario_id_usuario` INT NULL UNIQUE,
  PRIMARY KEY (`id`),
  INDEX `fk_Professor_Usuario1_idx` (`Usuario_id_usuario` ASC) VISIBLE,
  CONSTRAINT `fk_Professor_Usuario1`
    FOREIGN KEY (`Usuario_id_usuario`)
    REFERENCES `Usuario` (`id_usuario`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 5. Tabela Curso (Cursos de Graduação / Pós-Graduação)
CREATE TABLE IF NOT EXISTS `Curso` (
  `id_curso` INT NOT NULL AUTO_INCREMENT,
  `codigo_mec` VARCHAR(30) NOT NULL UNIQUE,
  `nome` VARCHAR(120) NOT NULL UNIQUE,
  `grau_academico` VARCHAR(40) NOT NULL,
  `modalidade` VARCHAR(30) NOT NULL DEFAULT 'PRESENCIAL',
  `carga_horaria_total` INT NOT NULL,
  `duracao_semestres` INT NOT NULL,
  `departamento_id` INT NOT NULL,
  `coordenador_id` INT NULL,
  `ativo` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`id_curso`),
  INDEX `idx_curso_departamento` (`departamento_id` ASC) VISIBLE,
  INDEX `idx_curso_coordenador` (`coordenador_id` ASC) VISIBLE,
  CONSTRAINT `fk_Curso_Departamento`
    FOREIGN KEY (`departamento_id`)
    REFERENCES `Departamento` (`id_departamento`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Curso_Coordenador`
    FOREIGN KEY (`coordenador_id`)
    REFERENCES `Professor` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 6. Tabela Aluno (Especialização Discente)
CREATE TABLE IF NOT EXISTS `Aluno` (
  `matricula` INT NOT NULL,
  `Usuario_id_usuario` INT NOT NULL UNIQUE,
  `nome` VARCHAR(120) NULL,
  `email` VARCHAR(120) NULL UNIQUE,
  `cpf` VARCHAR(14) NULL UNIQUE,
  `telefone` VARCHAR(20) NULL,
  `data_nascimento` DATE NULL,
  `curso_id` INT NULL,
  `status_academico` VARCHAR(30) NOT NULL DEFAULT 'ATIVO',
  `ira` DECIMAL(4,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`matricula`),
  INDEX `fk_Aluno_Usuario_idx` (`Usuario_id_usuario` ASC) VISIBLE,
  INDEX `fk_Aluno_Curso_idx` (`curso_id` ASC) VISIBLE,
  CONSTRAINT `fk_Aluno_Usuario`
    FOREIGN KEY (`Usuario_id_usuario`)
    REFERENCES `Usuario` (`id_usuario`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Aluno_Curso`
    FOREIGN KEY (`curso_id`)
    REFERENCES `Curso` (`id_curso`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 7. Tabela FuncionarioAdministrativo (Secretaria / Financeiro / Admin TI)
CREATE TABLE IF NOT EXISTS `FuncionarioAdministrativo` (
  `id_funcionario` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(120) NULL,
  `cpf` VARCHAR(14) NULL UNIQUE,
  `cargo` VARCHAR(80) NULL,
  `setor` VARCHAR(100) NOT NULL,
  `Usuario_id_usuario` INT NOT NULL UNIQUE,
  PRIMARY KEY (`id_funcionario`),
  INDEX `fk_FuncionarioAdministrativo_Usuario1_idx` (`Usuario_id_usuario` ASC) VISIBLE,
  CONSTRAINT `fk_FuncionarioAdministrativo_Usuario1`
    FOREIGN KEY (`Usuario_id_usuario`)
    REFERENCES `Usuario` (`id_usuario`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 8. Tabela TokenRecuperacao (Recuperação de Senha via E-mail)
CREATE TABLE IF NOT EXISTS `TokenRecuperacao` (
  `id_token` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NOT NULL,
  `token_hash` VARCHAR(64) NOT NULL,
  `criado_em` DATETIME NOT NULL,
  `expira_em` DATETIME NOT NULL,
  `utilizado` BOOLEAN NOT NULL DEFAULT FALSE,
  `utilizado_em` DATETIME NULL,
  `revogado` BOOLEAN NOT NULL DEFAULT FALSE,
  `ip_solicitacao` VARCHAR(45) NOT NULL,
  `ip_utilizacao` VARCHAR(45) NULL,
  PRIMARY KEY (`id_token`),
  INDEX `idx_token_hash` (`token_hash` ASC) VISIBLE,
  INDEX `idx_usuario_token` (`usuario_id` ASC, `utilizado` ASC, `revogado` ASC) VISIBLE,
  CONSTRAINT `fk_TokenRecuperacao_Usuario`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `Usuario` (`id_usuario`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 9. Tabela LogAuditoriaRecuperacao (Trilha de Auditoria de Recuperação de Senha)
CREATE TABLE IF NOT EXISTS `LogAuditoriaRecuperacao` (
  `id_log` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NULL,
  `data_hora` DATETIME NOT NULL,
  `ip_origem` VARCHAR(45) NOT NULL,
  `user_agent` VARCHAR(255) NULL,
  `acao` VARCHAR(50) NOT NULL,
  `status_resultado` VARCHAR(20) NOT NULL,
  `detalhes` VARCHAR(255) NULL,
  PRIMARY KEY (`id_log`),
  INDEX `idx_auditoria_usuario` (`usuario_id` ASC) VISIBLE,
  INDEX `idx_auditoria_data` (`data_hora` ASC) VISIBLE,
  CONSTRAINT `fk_LogAuditoria_Usuario`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `Usuario` (`id_usuario`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 10. Tabela TermoConsentimentoLGPD (Gestão de Consentimento LGPD - SGA-22)
CREATE TABLE IF NOT EXISTS `TermoConsentimentoLGPD` (
  `id_consentimento` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NOT NULL,
  `versao_termo` VARCHAR(20) NOT NULL,
  `finalidade` VARCHAR(120) NOT NULL,
  `aceito` BOOLEAN NOT NULL DEFAULT TRUE,
  `data_aceite` DATETIME NOT NULL,
  `data_revogacao` DATETIME NULL,
  `ip_origem` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id_consentimento`),
  INDEX `idx_consentimento_usuario` (`usuario_id` ASC, `versao_termo` ASC) VISIBLE,
  CONSTRAINT `fk_ConsentimentoLGPD_Usuario`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `Usuario` (`id_usuario`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 11. Tabela LogAuditoriaSistema (Trilha Geral de Auditoria - SGA-22)
CREATE TABLE IF NOT EXISTS `LogAuditoriaSistema` (
  `id_auditoria` INT NOT NULL AUTO_INCREMENT,
  `usuario_id` INT NULL,
  `entidade_afetada` VARCHAR(80) NOT NULL,
  `id_registro_afetado` VARCHAR(64) NULL,
  `acao` VARCHAR(50) NOT NULL,
  `dados_anteriores` TEXT NULL,
  `dados_novos` TEXT NULL,
  `ip_origem` VARCHAR(45) NOT NULL,
  `data_hora` DATETIME NOT NULL,
  PRIMARY KEY (`id_auditoria`),
  INDEX `idx_auditoria_sis_usuario` (`usuario_id` ASC) VISIBLE,
  INDEX `idx_auditoria_sis_data` (`data_hora` ASC) VISIBLE,
  CONSTRAINT `fk_LogAuditoriaSistema_Usuario`
    FOREIGN KEY (`usuario_id`)
    REFERENCES `Usuario` (`id_usuario`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- =============================================================================
-- DOMÍNIO 2: ESTRUTURA ACADÊMICA E MATRIZ CURRICULAR
-- =============================================================================

-- 12. Tabela MatrizCurricular (Grades Curriculares / PPC)
CREATE TABLE IF NOT EXISTS `MatrizCurricular` (
  `id_matriz` INT NOT NULL AUTO_INCREMENT,
  `curso_id` INT NOT NULL,
  `codigo_matriz` VARCHAR(30) NOT NULL UNIQUE,
  `ano_vigencia` INT NOT NULL,
  `semestre_vigencia` INT NOT NULL,
  `carga_horaria_minima` INT NOT NULL,
  `ativa` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`id_matriz`),
  INDEX `idx_matriz_curso` (`curso_id` ASC) VISIBLE,
  CONSTRAINT `fk_MatrizCurricular_Curso`
    FOREIGN KEY (`curso_id`)
    REFERENCES `Curso` (`id_curso`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 13. Tabela Disciplina (Componentes Curriculares)
CREATE TABLE IF NOT EXISTS `Disciplina` (
  `id_disciplina` INT NOT NULL AUTO_INCREMENT,
  `matriz_id` INT NOT NULL,
  `codigo` VARCHAR(20) NOT NULL UNIQUE,
  `nome` VARCHAR(120) NOT NULL,
  `semestre_ideal` INT NOT NULL,
  `carga_horaria` INT NOT NULL,
  `creditos` INT NOT NULL,
  `natureza` VARCHAR(25) NOT NULL DEFAULT 'OBRIGATORIA',
  `ementa` TEXT NULL,
  PRIMARY KEY (`id_disciplina`),
  INDEX `idx_disciplina_matriz` (`matriz_id` ASC) VISIBLE,
  CONSTRAINT `fk_Disciplina_MatrizCurricular`
    FOREIGN KEY (`matriz_id`)
    REFERENCES `MatrizCurricular` (`id_matriz`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 14. Tabela PreRequisito (Pré-requisitos e Correquisitos entre Disciplinas)
CREATE TABLE IF NOT EXISTS `PreRequisito` (
  `id_prerequisito` INT NOT NULL AUTO_INCREMENT,
  `disciplina_id` INT NOT NULL,
  `requisito_disciplina_id` INT NOT NULL,
  `tipo_requisito` VARCHAR(20) NOT NULL DEFAULT 'PRE_REQUISITO',
  PRIMARY KEY (`id_prerequisito`),
  UNIQUE (`disciplina_id`, `requisito_disciplina_id`),
  INDEX `idx_prerequisito_disciplina` (`disciplina_id` ASC) VISIBLE,
  INDEX `idx_prerequisito_req` (`requisito_disciplina_id` ASC) VISIBLE,
  CONSTRAINT `fk_PreRequisito_Disciplina`
    FOREIGN KEY (`disciplina_id`)
    REFERENCES `Disciplina` (`id_disciplina`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_PreRequisito_Requisito`
    FOREIGN KEY (`requisito_disciplina_id`)
    REFERENCES `Disciplina` (`id_disciplina`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CHECK (`disciplina_id` <> `requisito_disciplina_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 15. Tabela EquivalenciaDisciplina (Equivalências e Aproveitamento de Estudos)
CREATE TABLE IF NOT EXISTS `EquivalenciaDisciplina` (
  `id_equivalencia` INT NOT NULL AUTO_INCREMENT,
  `disciplina_origem_id` INT NOT NULL,
  `disciplina_equivalente_id` INT NOT NULL,
  `portaria_aprovacao` VARCHAR(60) NULL,
  `ativa` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`id_equivalencia`),
  UNIQUE (`disciplina_origem_id`, `disciplina_equivalente_id`),
  INDEX `idx_equivalencia_origem` (`disciplina_origem_id` ASC) VISIBLE,
  INDEX `idx_equivalencia_equiv` (`disciplina_equivalente_id` ASC) VISIBLE,
  CONSTRAINT `fk_Equivalencia_Origem`
    FOREIGN KEY (`disciplina_origem_id`)
    REFERENCES `Disciplina` (`id_disciplina`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Equivalencia_Equivalente`
    FOREIGN KEY (`disciplina_equivalente_id`)
    REFERENCES `Disciplina` (`id_disciplina`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CHECK (`disciplina_origem_id` <> `disciplina_equivalente_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- =============================================================================
-- DOMÍNIO 3: PLANEJAMENTO LETIVO, SALAS E TURMAS
-- =============================================================================

-- 16. Tabela PeriodoLetivo (Calendário Semestral)
CREATE TABLE IF NOT EXISTS `PeriodoLetivo` (
  `id_periodo` INT NOT NULL AUTO_INCREMENT,
  `codigo` VARCHAR(15) NOT NULL UNIQUE,
  `ano` INT NOT NULL,
  `semestre` INT NOT NULL,
  `data_inicio` DATE NOT NULL,
  `data_fim` DATE NOT NULL,
  `status_periodo` VARCHAR(25) NOT NULL DEFAULT 'EM_ANDAMENTO',
  PRIMARY KEY (`id_periodo`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 17. Tabela Sala (Espaços Físicos, Laboratórios e Ambientes Virtuais)
CREATE TABLE IF NOT EXISTS `Sala` (
  `id_sala` INT NOT NULL AUTO_INCREMENT,
  `codigo_sala` VARCHAR(30) NOT NULL UNIQUE,
  `bloco` VARCHAR(40) NOT NULL,
  `capacidade` INT NOT NULL,
  `tipo_sala` VARCHAR(30) NOT NULL DEFAULT 'SALA_AULA',
  `ativa` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`id_sala`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 18. Tabela Turma (Oferta Semestral de Disciplina)
CREATE TABLE IF NOT EXISTS `Turma` (
  `id_turma` INT NOT NULL AUTO_INCREMENT,
  `codigo_turma` VARCHAR(30) NOT NULL UNIQUE,
  `disciplina_id` INT NOT NULL,
  `periodo_letivo_id` INT NOT NULL,
  `professor_id` INT NULL,
  `sala_id` INT NULL,
  `turno` VARCHAR(20) NOT NULL,
  `vagas_totais` INT NOT NULL,
  `vagas_ocupadas` INT NOT NULL DEFAULT 0,
  `status_turma` VARCHAR(25) NOT NULL DEFAULT 'ABERTA',
  PRIMARY KEY (`id_turma`),
  INDEX `idx_turma_disciplina_periodo` (`disciplina_id` ASC, `periodo_letivo_id` ASC) VISIBLE,
  INDEX `idx_turma_professor` (`professor_id` ASC) VISIBLE,
  INDEX `idx_turma_sala` (`sala_id` ASC) VISIBLE,
  CONSTRAINT `fk_Turma_Disciplina`
    FOREIGN KEY (`disciplina_id`)
    REFERENCES `Disciplina` (`id_disciplina`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Turma_PeriodoLetivo`
    FOREIGN KEY (`periodo_letivo_id`)
    REFERENCES `PeriodoLetivo` (`id_periodo`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Turma_Professor`
    FOREIGN KEY (`professor_id`)
    REFERENCES `Professor` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Turma_Sala`
    FOREIGN KEY (`sala_id`)
    REFERENCES `Sala` (`id_sala`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 19. Tabela HorarioTurma (Alocação de Dias e Horários de Aula)
CREATE TABLE IF NOT EXISTS `HorarioTurma` (
  `id_horario` INT NOT NULL AUTO_INCREMENT,
  `turma_id` INT NOT NULL,
  `dia_semana` INT NOT NULL,
  `hora_inicio` VARCHAR(5) NOT NULL,
  `hora_fim` VARCHAR(5) NOT NULL,
  PRIMARY KEY (`id_horario`),
  UNIQUE (`turma_id`, `dia_semana`, `hora_inicio`),
  INDEX `idx_horario_turma` (`turma_id` ASC) VISIBLE,
  CONSTRAINT `fk_HorarioTurma_Turma`
    FOREIGN KEY (`turma_id`)
    REFERENCES `Turma` (`id_turma`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CHECK (`dia_semana` >= 1 AND `dia_semana` <= 7)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- =============================================================================
-- DOMÍNIO 4: VIDA ACADÊMICA, DIÁRIO DE CLASSE E MOVIMENTAÇÃO
-- =============================================================================

-- 20. Tabela MatriculaTurma (Vínculo do Aluno na Turma Ofertada)
CREATE TABLE IF NOT EXISTS `MatriculaTurma` (
  `id_matricula_turma` INT NOT NULL AUTO_INCREMENT,
  `aluno_matricula` INT NOT NULL,
  `turma_id` INT NOT NULL,
  `data_matricula` DATETIME NOT NULL,
  `media_final` DECIMAL(4,2) NULL,
  `percentual_frequencia` DECIMAL(5,2) NOT NULL DEFAULT 100.00,
  `situacao` VARCHAR(30) NOT NULL DEFAULT 'CURSANDO',
  PRIMARY KEY (`id_matricula_turma`),
  UNIQUE (`aluno_matricula`, `turma_id`),
  INDEX `idx_matricula_aluno` (`aluno_matricula` ASC) VISIBLE,
  INDEX `idx_matricula_turma` (`turma_id` ASC) VISIBLE,
  CONSTRAINT `fk_MatriculaTurma_Aluno`
    FOREIGN KEY (`aluno_matricula`)
    REFERENCES `Aluno` (`matricula`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_MatriculaTurma_Turma`
    FOREIGN KEY (`turma_id`)
    REFERENCES `Turma` (`id_turma`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 21. Tabela AvaliacaoNota (Lançamento de Notas por Etapa)
CREATE TABLE IF NOT EXISTS `AvaliacaoNota` (
  `id_avaliacao` INT NOT NULL AUTO_INCREMENT,
  `matricula_turma_id` INT NOT NULL,
  `etapa` VARCHAR(30) NOT NULL,
  `nota` DECIMAL(4,2) NOT NULL,
  `peso` DECIMAL(4,2) NOT NULL DEFAULT 1.00,
  `data_lancamento` DATETIME NOT NULL,
  `observacao` VARCHAR(255) NULL,
  PRIMARY KEY (`id_avaliacao`),
  UNIQUE (`matricula_turma_id`, `etapa`),
  INDEX `idx_avaliacao_matricula` (`matricula_turma_id` ASC) VISIBLE,
  CONSTRAINT `fk_AvaliacaoNota_MatriculaTurma`
    FOREIGN KEY (`matricula_turma_id`)
    REFERENCES `MatriculaTurma` (`id_matricula_turma`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CHECK (`nota` >= 0.00 AND `nota` <= 10.00)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 22. Tabela RegistroFrequencia (Chamada e Presença por Aula)
CREATE TABLE IF NOT EXISTS `RegistroFrequencia` (
  `id_frequencia` INT NOT NULL AUTO_INCREMENT,
  `matricula_turma_id` INT NOT NULL,
  `data_aula` DATE NOT NULL,
  `presente` BOOLEAN NOT NULL DEFAULT TRUE,
  `quantidade_aulas` INT NOT NULL DEFAULT 2,
  `justificativa` VARCHAR(255) NULL,
  PRIMARY KEY (`id_frequencia`),
  UNIQUE (`matricula_turma_id`, `data_aula`),
  INDEX `idx_frequencia_matricula` (`matricula_turma_id` ASC) VISIBLE,
  CONSTRAINT `fk_RegistroFrequencia_MatriculaTurma`
    FOREIGN KEY (`matricula_turma_id`)
    REFERENCES `MatriculaTurma` (`id_matricula_turma`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 23. Tabela PlanoEnsino (Plano de Ensino da Turma)
CREATE TABLE IF NOT EXISTS `PlanoEnsino` (
  `id_plano` INT NOT NULL AUTO_INCREMENT,
  `turma_id` INT NOT NULL UNIQUE,
  `objetivos` TEXT NOT NULL,
  `metodologia` TEXT NOT NULL,
  `criterios_avaliacao` TEXT NOT NULL,
  `bibliografia` TEXT NOT NULL,
  `status_aprovacao` VARCHAR(25) NOT NULL DEFAULT 'PUBLICADO',
  `atualizado_em` DATETIME NOT NULL,
  PRIMARY KEY (`id_plano`),
  INDEX `idx_plano_turma` (`turma_id` ASC) VISIBLE,
  CONSTRAINT `fk_PlanoEnsino_Turma`
    FOREIGN KEY (`turma_id`)
    REFERENCES `Turma` (`id_turma`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 24. Tabela MaterialAula (Materiais Didáticos e Atividades da Turma)
CREATE TABLE IF NOT EXISTS `MaterialAula` (
  `id_material` INT NOT NULL AUTO_INCREMENT,
  `turma_id` INT NOT NULL,
  `titulo` VARCHAR(120) NOT NULL,
  `descricao` VARCHAR(255) NULL,
  `url_recurso` VARCHAR(255) NOT NULL,
  `data_publicacao` DATETIME NOT NULL,
  PRIMARY KEY (`id_material`),
  INDEX `idx_material_turma` (`turma_id` ASC) VISIBLE,
  CONSTRAINT `fk_MaterialAula_Turma`
    FOREIGN KEY (`turma_id`)
    REFERENCES `Turma` (`id_turma`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 25. Tabela ComunicadoTurma (Avisos e Comunicados Docentes)
CREATE TABLE IF NOT EXISTS `ComunicadoTurma` (
  `id_comunicado` INT NOT NULL AUTO_INCREMENT,
  `turma_id` INT NOT NULL,
  `professor_id` INT NULL,
  `titulo` VARCHAR(120) NOT NULL,
  `mensagem` TEXT NOT NULL,
  `enviado_em` DATETIME NOT NULL,
  PRIMARY KEY (`id_comunicado`),
  INDEX `idx_comunicado_turma` (`turma_id` ASC) VISIBLE,
  INDEX `idx_comunicado_professor` (`professor_id` ASC) VISIBLE,
  CONSTRAINT `fk_ComunicadoTurma_Turma`
    FOREIGN KEY (`turma_id`)
    REFERENCES `Turma` (`id_turma`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_ComunicadoTurma_Professor`
    FOREIGN KEY (`professor_id`)
    REFERENCES `Professor` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 26. Tabela MovimentacaoAcademica (Trancamento, Transferência, Cancelamento, Jubilamento)
CREATE TABLE IF NOT EXISTS `MovimentacaoAcademica` (
  `id_movimentacao` INT NOT NULL AUTO_INCREMENT,
  `aluno_matricula` INT NOT NULL,
  `periodo_letivo_id` INT NOT NULL,
  `tipo_movimentacao` VARCHAR(30) NOT NULL,
  `motivo` TEXT NOT NULL,
  `status_movimentacao` VARCHAR(25) NOT NULL DEFAULT 'DEFERIDO',
  `data_registro` DATETIME NOT NULL,
  PRIMARY KEY (`id_movimentacao`),
  INDEX `idx_movimentacao_aluno` (`aluno_matricula` ASC) VISIBLE,
  INDEX `idx_movimentacao_periodo` (`periodo_letivo_id` ASC) VISIBLE,
  CONSTRAINT `fk_Movimentacao_Aluno`
    FOREIGN KEY (`aluno_matricula`)
    REFERENCES `Aluno` (`matricula`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Movimentacao_PeriodoLetivo`
    FOREIGN KEY (`periodo_letivo_id`)
    REFERENCES `PeriodoLetivo` (`id_periodo`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 27. Tabela RequerimentoAcademico (Solicitações e Protocolos Discentes)
CREATE TABLE IF NOT EXISTS `RequerimentoAcademico` (
  `id_requerimento` INT NOT NULL AUTO_INCREMENT,
  `protocolo` VARCHAR(30) NOT NULL UNIQUE,
  `aluno_matricula` INT NOT NULL,
  `periodo_letivo_id` INT NULL,
  `tipo_requerimento` VARCHAR(50) NOT NULL,
  `descricao` TEXT NOT NULL,
  `status_requerimento` VARCHAR(25) NOT NULL DEFAULT 'ABERTO',
  `parecer_secretaria` TEXT NULL,
  `aberto_em` DATETIME NOT NULL,
  `atualizado_em` DATETIME NULL,
  PRIMARY KEY (`id_requerimento`),
  INDEX `idx_requerimento_aluno` (`aluno_matricula` ASC) VISIBLE,
  INDEX `idx_requerimento_periodo` (`periodo_letivo_id` ASC) VISIBLE,
  CONSTRAINT `fk_Requerimento_Aluno`
    FOREIGN KEY (`aluno_matricula`)
    REFERENCES `Aluno` (`matricula`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Requerimento_PeriodoLetivo`
    FOREIGN KEY (`periodo_letivo_id`)
    REFERENCES `PeriodoLetivo` (`id_periodo`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- =============================================================================
-- DOMÍNIO 5: GESTÃO FINANCEIRA INTEGRADA
-- =============================================================================

-- 28. Tabela ContratoFinanceiro (Contrato Educacional Semestral)
CREATE TABLE IF NOT EXISTS `ContratoFinanceiro` (
  `id_contrato` INT NOT NULL AUTO_INCREMENT,
  `numero_contrato` VARCHAR(30) NOT NULL UNIQUE,
  `aluno_matricula` INT NOT NULL,
  `periodo_letivo_id` INT NOT NULL,
  `valor_semestral_bruto` DECIMAL(10,2) NOT NULL,
  `quantidade_parcelas` INT NOT NULL DEFAULT 6,
  `situacao_adimplencia` VARCHAR(25) NOT NULL DEFAULT 'ADIMPLENTE',
  `assinado_em` DATETIME NOT NULL,
  PRIMARY KEY (`id_contrato`),
  UNIQUE (`aluno_matricula`, `periodo_letivo_id`),
  INDEX `idx_contrato_aluno` (`aluno_matricula` ASC) VISIBLE,
  INDEX `idx_contrato_periodo` (`periodo_letivo_id` ASC) VISIBLE,
  CONSTRAINT `fk_Contrato_Aluno`
    FOREIGN KEY (`aluno_matricula`)
    REFERENCES `Aluno` (`matricula`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Contrato_PeriodoLetivo`
    FOREIGN KEY (`periodo_letivo_id`)
    REFERENCES `PeriodoLetivo` (`id_periodo`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 29. Tabela BolsaDesconto (Bolsas, Convênios e Descontos Concedidos)
CREATE TABLE IF NOT EXISTS `BolsaDesconto` (
  `id_beneficio` INT NOT NULL AUTO_INCREMENT,
  `contrato_id` INT NOT NULL,
  `tipo_beneficio` VARCHAR(40) NOT NULL,
  `percentual_desconto` DECIMAL(5,2) NOT NULL,
  `ativo` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`id_beneficio`),
  INDEX `idx_bolsa_contrato` (`contrato_id` ASC) VISIBLE,
  CONSTRAINT `fk_BolsaDesconto_Contrato`
    FOREIGN KEY (`contrato_id`)
    REFERENCES `ContratoFinanceiro` (`id_contrato`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CHECK (`percentual_desconto` >= 0.00 AND `percentual_desconto` <= 100.00)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 30. Tabela CobrancaMensalidade (Títulos, Boletos e Pix)
CREATE TABLE IF NOT EXISTS `CobrancaMensalidade` (
  `id_cobranca` INT NOT NULL AUTO_INCREMENT,
  `nosso_numero` VARCHAR(40) NOT NULL UNIQUE,
  `contrato_id` INT NOT NULL,
  `numero_parcela` INT NOT NULL,
  `competencia` VARCHAR(7) NOT NULL,
  `valor_nominal` DECIMAL(10,2) NOT NULL,
  `valor_desconto` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `valor_final` DECIMAL(10,2) NOT NULL,
  `data_vencimento` DATE NOT NULL,
  `linha_digitavel_boleto` VARCHAR(120) NULL,
  `payload_pix_copia_cola` TEXT NULL,
  `status_cobranca` VARCHAR(25) NOT NULL DEFAULT 'PENDENTE',
  PRIMARY KEY (`id_cobranca`),
  UNIQUE (`contrato_id`, `numero_parcela`),
  INDEX `idx_cobranca_contrato` (`contrato_id` ASC) VISIBLE,
  INDEX `idx_cobranca_vencimento` (`data_vencimento` ASC, `status_cobranca` ASC) VISIBLE,
  CONSTRAINT `fk_Cobranca_Contrato`
    FOREIGN KEY (`contrato_id`)
    REFERENCES `ContratoFinanceiro` (`id_contrato`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 31. Tabela PagamentoConciliacao (Liquidação e Conciliação Bancária)
CREATE TABLE IF NOT EXISTS `PagamentoConciliacao` (
  `id_pagamento` INT NOT NULL AUTO_INCREMENT,
  `cobranca_id` INT NOT NULL,
  `identificador_transacao` VARCHAR(64) NOT NULL UNIQUE,
  `meio_pagamento` VARCHAR(20) NOT NULL,
  `valor_pago` DECIMAL(10,2) NOT NULL,
  `data_pagamento` DATETIME NOT NULL,
  `conciliado_automaticamente` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`id_pagamento`),
  INDEX `idx_pagamento_cobranca` (`cobranca_id` ASC) VISIBLE,
  CONSTRAINT `fk_Pagamento_Cobranca`
    FOREIGN KEY (`cobranca_id`)
    REFERENCES `CobrancaMensalidade` (`id_cobranca`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- =============================================================================
-- DOMÍNIO 6: EMISSÃO DIGITAL E ACERVO REGULATÓRIO MEC
-- =============================================================================

-- 32. Tabela DocumentoAcademico (Históricos, Declarações, Atas e Diplomas com QR Code)
CREATE TABLE IF NOT EXISTS `DocumentoAcademico` (
  `id_documento` INT NOT NULL AUTO_INCREMENT,
  `aluno_matricula` INT NOT NULL,
  `tipo_documento` VARCHAR(40) NOT NULL,
  `codigo_verificacao` VARCHAR(64) NOT NULL UNIQUE,
  `hash_sha256` VARCHAR(64) NOT NULL,
  `url_validacao_qrcode` VARCHAR(255) NOT NULL,
  `emitido_em` DATETIME NOT NULL,
  `valido` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`id_documento`),
  INDEX `idx_documento_aluno` (`aluno_matricula` ASC) VISIBLE,
  INDEX `idx_documento_codigo` (`codigo_verificacao` ASC) VISIBLE,
  CONSTRAINT `fk_DocumentoAcademico_Aluno`
    FOREIGN KEY (`aluno_matricula`)
    REFERENCES `Aluno` (`matricula`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 33. Tabela AcervoDigitalMEC (Custódia e Conformidade Portarias MEC 315/2018 e 360/2022)
CREATE TABLE IF NOT EXISTS `AcervoDigitalMEC` (
  `id_acervo` INT NOT NULL AUTO_INCREMENT,
  `documento_id` INT NOT NULL UNIQUE,
  `portaria_referencia` VARCHAR(40) NOT NULL DEFAULT 'PORTARIA_MEC_360_2022',
  `formato_arquivo` VARCHAR(30) NOT NULL DEFAULT 'PDF_A_ASSINADO',
  `assinatura_icp_brasil` VARCHAR(128) NOT NULL,
  `carimbo_tempo` DATETIME NOT NULL,
  `prazo_guarda` VARCHAR(30) NOT NULL DEFAULT 'PERMANENTE',
  `status_custodia` VARCHAR(25) NOT NULL DEFAULT 'INTEGRO',
  PRIMARY KEY (`id_acervo`),
  INDEX `idx_acervo_documento` (`documento_id` ASC) VISIBLE,
  CONSTRAINT `fk_AcervoDigitalMEC_Documento`
    FOREIGN KEY (`documento_id`)
    REFERENCES `DocumentoAcademico` (`id_documento`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
