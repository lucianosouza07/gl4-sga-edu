-- ============================================================================
-- SGA-Edu: Módulo de Criptografia de Dados e Backups Automatizados
-- DDL para Tabelas de Metadados de Backup, Política de Retenção e Auditoria
-- Padrão MySQL 8.0+ / InnoDB / utf8mb4_unicode_ci
-- ============================================================================

-- 1. Tabela de Registros e Metadados de Volumes de Backup
CREATE TABLE IF NOT EXISTS BackupRegistro (
    id_backup INT AUTO_INCREMENT PRIMARY KEY,
    nome_arquivo VARCHAR(255) NOT NULL UNIQUE,
    tipo_backup VARCHAR(20) NOT NULL COMMENT 'COMPLETO, INCREMENTAL ou MANUAL',
    caminho_relativo VARCHAR(500) NOT NULL,
    tamanho_original_bytes BIGINT NOT NULL,
    tamanho_cifrado_bytes BIGINT NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    algoritmo_cifragem VARCHAR(30) NOT NULL DEFAULT 'AES-256-GCM',
    criado_em DATETIME NOT NULL,
    expira_em DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'GERANDO' COMMENT 'GERANDO, CONCLUIDO, FALHO ou EXPURGADO',
    validado_em DATETIME NULL,
    status_integridade VARCHAR(20) NOT NULL DEFAULT 'PENDENTE' COMMENT 'PENDENTE, VALIDO ou CORROMPIDO',
    iniciado_por VARCHAR(100) NOT NULL,
    INDEX idx_backup_criado_em (criado_em),
    INDEX idx_backup_status (status),
    INDEX idx_backup_checksum (checksum_sha256)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Tabela de Configuração Institucional de Política de Retenção
CREATE TABLE IF NOT EXISTS PoliticaRetencaoBackup (
    id_politica INT AUTO_INCREMENT PRIMARY KEY,
    frequencia_cron VARCHAR(50) NOT NULL DEFAULT '0 3 * * *',
    dias_retencao_diario INT NOT NULL DEFAULT 30,
    meses_retencao_mensal INT NOT NULL DEFAULT 12,
    copias_minimas_seguranca INT NOT NULL DEFAULT 7,
    compactacao_habilitada BOOLEAN NOT NULL DEFAULT TRUE,
    cifragem_habilitada BOOLEAN NOT NULL DEFAULT TRUE,
    atualizado_em DATETIME NOT NULL,
    atualizado_por VARCHAR(100) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Tabela de Trilha Imutável de Auditoria de Salvaguardas e Segurança
CREATE TABLE IF NOT EXISTS LogAuditoriaBackup (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    data_hora DATETIME NOT NULL,
    operador VARCHAR(100) NOT NULL,
    ip_origem VARCHAR(45) NOT NULL,
    acao VARCHAR(50) NOT NULL,
    status_resultado VARCHAR(20) NOT NULL COMMENT 'SUCESSO, FALHA ou ALERTA',
    backup_id INT NULL,
    detalhes TEXT NULL,
    INDEX idx_auditoria_backup_data (data_hora),
    INDEX idx_auditoria_backup_acao (acao),
    CONSTRAINT fk_LogAuditoria_BackupRegistro FOREIGN KEY (backup_id)
        REFERENCES BackupRegistro (id_backup) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inserção de política de retenção padrão inicial
INSERT INTO PoliticaRetencaoBackup (
    id_politica, frequencia_cron, dias_retencao_diario, meses_retencao_mensal,
    copias_minimas_seguranca, compactacao_habilitada, cifragem_habilitada, atualizado_em, atualizado_por
) VALUES (
    1, '0 3 * * *', 30, 12, 7, TRUE, TRUE, NOW(), 'SISTEMA_SEED'
) ON DUPLICATE KEY UPDATE atualizado_em = NOW();
