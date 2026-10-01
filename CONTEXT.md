# Gestão Acadêmica (SGA-EDU)

Contexto responsável pela identidade dos usuários, autenticação, controle de permissões e ciclo de vida cadastral e acadêmico dos estudantes.

## Language

**Usuário**:
Conta de acesso e identidade digital no sistema, contendo credenciais de login, nome para identificação e perfil de autorização.
_Avoid_: Conta, login, auth_user

**Aluno**:
Pessoa física matriculada na instituição de ensino com registro acadêmico formal, vinculada obrigatoriamente a um Usuário.
_Avoid_: Estudante, discente, matriculado

**Perfil de Usuário**:
Papel funcional atribuído a um Usuário que define suas permissões de acesso (ADMIN, SECRETARIA, PROFESSOR, ALUNO).
_Avoid_: Cargo, role, nível de acesso

**Matrícula**:
Código numérico único e imutável gerado automaticamente no cadastro do Aluno. Usa o ano e o semestre do cadastro, seguidos de uma sequência que reinicia a cada semestre e cresce sem limite fixo (ex: `202620001`).
_Avoid_: Código acadêmico, RA, registro escolar

**Administrador**:
Usuário com acesso irrestrito para governança e configuração do sistema, sem necessidade de dados acadêmicos ou funcionais adicionais.
_Avoid_: Superuser, root, admin_geral

**Secretaria**:
Usuário com perfil operacional responsável por criar e gerenciar o cadastro de Alunos e suas matrículas.
_Avoid_: Atendimento, recepção, operador

**Professor**:
Pessoa física do corpo docente responsável por ministrar disciplinas e turmas e lançar avaliações, vinculada a um Usuário.
_Avoid_: Docente, educador, instrutor
