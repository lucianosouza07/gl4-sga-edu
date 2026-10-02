-- MySQL Workbench Forward Engineering / Schema SGA-Edu

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Table `Perfil` (RBAC)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Perfil` (
  `id_perfil` INT NOT NULL AUTO_INCREMENT,
  `nome_perfil` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id_perfil`)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `Usuario`
-- -----------------------------------------------------
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

-- -----------------------------------------------------
-- Table `Aluno`
-- -----------------------------------------------------
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

-- -----------------------------------------------------
-- Table `Professor`
-- -----------------------------------------------------
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

-- -----------------------------------------------------
-- Table `FuncionarioAdministrativo`
-- -----------------------------------------------------
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
