-- Seed (Inserção inicial) dos 5 perfis RBAC exigidos
INSERT INTO Perfil (id_perfil, nome_perfil) VALUES 
(1, 'Aluno'), 
(2, 'Professor'), 
(3, 'Secretaria'), 
(4, 'Financeiro'), 
(5, 'Admin')
ON DUPLICATE KEY UPDATE nome_perfil = VALUES(nome_perfil);