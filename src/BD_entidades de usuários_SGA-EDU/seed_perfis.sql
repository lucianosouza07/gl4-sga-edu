-- Criando uma tabela para guardar os perfis RBAC
CREATE TABLE Perfil (
    id_perfil INT AUTO_INCREMENT PRIMARY KEY,
    nome_perfil VARCHAR(50) NOT NULL
);

-- Seed (Inserção inicial) dos 5 perfis exigidos
INSERT INTO Perfil (nome_perfil) VALUES 
('Aluno'), 
('Professor'), 
('Secretaria'), 
('Financeiro'), 
('Admin');