-- =============================================================================
-- SGA-EDU: Carga Inicial Idempotente (Seeds de Perfis RBAC e Base Acadêmica)
-- =============================================================================

INSERT INTO `Perfil` (`id_perfil`, `nome_perfil`, `descricao`) VALUES
(1, 'Aluno', 'Acesso ao portal discente, matrícula online, consulta de notas, frequência, requerimentos e financeiro'),
(2, 'Professor', 'Acesso ao portal docente, lançamento de notas, frequência, plano de ensino, materiais e comunicados'),
(3, 'Secretaria', 'Gestão acadêmica, matrizes curriculares, turmas, salas, movimentação discente e acervo digital MEC'),
(4, 'Financeiro', 'Gestão de contratos educacionais, emissão de boletos/Pix, bolsas, descontos e conciliação bancária'),
(5, 'Admin', 'Governança de TI, administração de perfis RBAC, MFA, consentimento LGPD e trilhas de auditoria')
ON DUPLICATE KEY UPDATE
  `nome_perfil` = VALUES(`nome_perfil`),
  `descricao` = VALUES(`descricao`);
