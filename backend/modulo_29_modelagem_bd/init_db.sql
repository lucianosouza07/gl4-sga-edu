-- =====================================================
-- SGA-Edu | Script de Inicialização Completa do Banco
-- Módulo 29: Modelagem de Banco de Dados
-- =====================================================

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- 1. Criação da Tabela Perfil (RBAC)
CREATE TABLE IF NOT EXISTS `Perfil` (
  `id_perfil` INT NOT NULL AUTO_INCREMENT,
  `nome_perfil` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id_perfil`)
) ENGINE = InnoDB;

-- 2. Seed dos 5 perfis RBAC da Sprint 1
INSERT INTO `Perfil` (`id_perfil`, `nome_perfil`) VALUES 
(1, 'Aluno'), 
(2, 'Professor'), 
(3, 'Secretaria'), 
(4, 'Financeiro'), 
(5, 'Admin')
ON DUPLICATE KEY UPDATE `nome_perfil` = VALUES(`nome_perfil`);

-- 3. Criação da Tabela Usuario
CREATE TABLE IF NOT EXISTS `Usuario` (
  `id_usuario` INT NOT NULL AUTO_INCREMENT,
  `login` VARCHAR(255) NOT NULL UNIQUE,
  `senha_hash` VARCHAR(255) NOT NULL,
  `perfil_RBAC` INT NOT NULL,
  `tokenMFA` VARCHAR(45) NULL,
  `statusCONTA` INT DEFAULT 1,
  `dadosIdentificacao` VARCHAR(255) NULL,
  PRIMARY KEY (`id_usuario`),
  INDEX `fk_Usuario_Perfil_idx` (`perfil_RBAC` ASC) VISIBLE,
  CONSTRAINT `fk_Usuario_Perfil`
    FOREIGN KEY (`perfil_RBAC`)
    REFERENCES `Perfil` (`id_perfil`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 4. Criação da Tabela Aluno
CREATE TABLE IF NOT EXISTS `Aluno` (
  `matricula` INT NOT NULL,
  `Usuario_id_usuario` INT NOT NULL,
  PRIMARY KEY (`matricula`),
  INDEX `fk_Aluno_Usuario_idx` (`Usuario_id_usuario` ASC) VISIBLE,
  CONSTRAINT `fk_Aluno_Usuario`
    FOREIGN KEY (`Usuario_id_usuario`)
    REFERENCES `Usuario` (`id_usuario`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 5. Criação da Tabela Professor (Alinhada com GL4-34)
CREATE TABLE IF NOT EXISTS `Professor` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(120) NOT NULL,
  `email` VARCHAR(120) NOT NULL UNIQUE,
  `cpf` VARCHAR(14) NOT NULL UNIQUE,
  `telefone` VARCHAR(20) NULL,
  `departamento` VARCHAR(80) NOT NULL,
  `titulacao` VARCHAR(50) NOT NULL,
  `areaAtuacao` VARCHAR(100) NULL,
  `Usuario_id_usuario` INT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_Professor_Usuario1_idx` (`Usuario_id_usuario` ASC) VISIBLE,
  CONSTRAINT `fk_Professor_Usuario1`
    FOREIGN KEY (`Usuario_id_usuario`)
    REFERENCES `Usuario` (`id_usuario`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- 6. Criação da Tabela FuncionarioAdministrativo
CREATE TABLE IF NOT EXISTS `FuncionarioAdministrativo` (
  `id_funcionario` INT NOT NULL AUTO_INCREMENT,
  `setor` VARCHAR(100) NOT NULL,
  `Usuario_id_usuario` INT NOT NULL,
  PRIMARY KEY (`id_funcionario`),
  INDEX `fk_FuncionarioAdministrativo_Usuario1_idx` (`Usuario_id_usuario` ASC) VISIBLE,
  CONSTRAINT `fk_FuncionarioAdministrativo_Usuario1`
    FOREIGN KEY (`Usuario_id_usuario`)
    REFERENCES `Usuario` (`id_usuario`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
