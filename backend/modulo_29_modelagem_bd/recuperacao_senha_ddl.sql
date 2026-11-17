-- =============================================================================
-- SGA-EDU: DDL para Módulo de Recuperação de Senha de Acesso via E-mail
-- Tabelas: TokenRecuperacao e LogAuditoriaRecuperacao
-- =============================================================================

CREATE TABLE IF NOT EXISTS TokenRecuperacao (
    id_token INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    criado_em DATETIME NOT NULL,
    expira_em DATETIME NOT NULL,
    utilizado BOOLEAN NOT NULL DEFAULT FALSE,
    utilizado_em DATETIME NULL,
    revogado BOOLEAN NOT NULL DEFAULT FALSE,
    ip_solicitacao VARCHAR(45) NOT NULL,
    ip_utilizacao VARCHAR(45) NULL,
    INDEX idx_token_hash (token_hash),
    INDEX idx_usuario_token (usuario_id, utilizado, revogado),
    CONSTRAINT fk_TokenRecuperacao_Usuario FOREIGN KEY (usuario_id)
        REFERENCES Usuario (id_usuario) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS LogAuditoriaRecuperacao (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL,
    data_hora DATETIME NOT NULL,
    ip_origem VARCHAR(45) NOT NULL,
    user_agent VARCHAR(255) NULL,
    acao VARCHAR(50) NOT NULL,
    status_resultado VARCHAR(20) NOT NULL,
    detalhes VARCHAR(255) NULL,
    INDEX idx_auditoria_usuario (usuario_id),
    INDEX idx_auditoria_data (data_hora),
    CONSTRAINT fk_LogAuditoria_Usuario FOREIGN KEY (usuario_id)
        REFERENCES Usuario (id_usuario) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
