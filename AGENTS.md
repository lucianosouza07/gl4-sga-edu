# 🤖 Diretrizes do Projeto — GL4 SGA-EDU (Sistema de Gestão Acadêmica)

Este arquivo é a **fonte única de regras e governança do repositório para agentes de IA** (Google Antigravity, Gemini CLI e OpenAI Codex). Qualquer agente que opere neste projeto deve seguir rigorosamente os princípios, invariantes e fluxos descritos abaixo.

---

## 📚 Referências Oficiais do Projeto

- **[CONTEXT.md](CONTEXT.md)**: Vocabulário ubíquo e limites canônicos do domínio (Usuário, Aluno, Professor, Matrícula).
- **[docs/arquitetura_cadastro_alunos.md](docs/arquitetura_cadastro_alunos.md)**: Documento mestre de arquitetura, contratos de API, schemas, regras de negócio e roteiro passo a passo do módulo de Alunos.
- **[docs/arquitetura_autenticacao_rbac.md](docs/arquitetura_autenticacao_rbac.md)**: Especificação completa de segurança, JWT Bearer Token, roles (ADMIN, SECRETARIA, PROFESSOR, ALUNO) e proteção via FastAPI Dependencies.
- **[docs/planejamento_fase1_frontend.md](docs/planejamento_fase1_frontend.md)**: Guia de frontend com Vite, React, Tailwind CSS v4 e shadcn/ui com tema Meridian.
- **[docs/setup_ambiente_backend.md](docs/setup_ambiente_backend.md)**: Guia de instalação e ativação do ambiente virtual Python.

---

## 🏛️ Invariantes de Arquitetura e Qualidade

1. **Isolamento entre Backend e Frontend:**
   - O contrato entre `backend/` e `frontend/` é estritamente via rede (REST API com payload JSON).
   - Nunca compartilhe código de models ou imports diretos entre as duas pastas.

2. **Padrão de Domínio (IAM vs. Domain Roles):**
   - A entidade `Usuario` representa unicamente a **identidade digital e acesso** (login, senha, perfil de autorização e nome de exibição).
   - Regras pedagógicas e dados acadêmicos pertencem a entidades especializadas (ex: `Aluno`, `Professor`). O relacionamento é `1:1` opcional.
   - Administradores e Secretarias não necessitam de tabelas satélites desnecessárias.

3. **Uso Mandatório de Componentes Shadcn UI no Frontend:**
   - É **proibido** utilizar tags HTML cruas substituíveis (`<button>`, `<input>`, `<textarea>`, `<select>`, `<dialog>`, `<table>`, `<hr>`) nas telas e páginas.
   - Use sempre os componentes equivalentes de `@/components/ui/` (`Button`, `Input`, `Textarea`, `Dialog`, `Table`, `Separator`, etc.).
   - Rode `python3 scripts/check_shadcn_usage.py` para auditar a conformidade antes de finalizar qualquer tela.

4. **Segurança e Criptografia:**
   - **Nunca** armazene ou trafegue senhas em texto puro. Sempre utilize hash Bcrypt (`app.core.security.gerar_hash_senha`).
   - Autenticação via **JWT Bearer Token (Stateless)** com algoritmo `HS256` e expiração configurada.
   - **Nunca** registre segredos, tokens ou arquivos `.env` no Git. Arquivos `.db`, `.sqlite3`, `.venv/` e `node_modules/` devem permanecer no `.gitignore`.

5. **Controle de Acesso Baseado em Perfis (RBAC):**
   - Endpoints sensíveis devem declarar explicitamente a dependência de autorização (ex: `Depends(require_roles([PerfilUsuario.SECRETARIA, PerfilUsuario.ADMIN]))`).
   - Acessos não autorizados devem retornar `HTTP 403 Forbidden`.

6. **TDD e Cobertura de Testes no Backend:**
   - Escreva testes unitários e de integração com `pytest` para todo novo Service ou Endpoint.
   - Testes devem rodar de forma isolada em banco de dados em memória (`sqlite:///:memory:`) utilizando as fixtures em `tests/conftest.py`.

7. **TypeScript Strict no Frontend:**
   - Mantenha o TypeScript em modo estrito. **Não utilize o tipo `any`**. Use interfaces em `src/types/`.

---

## 🔄 Fluxo de Trabalho para Qualquer Agente

1. **Leitura Prévia:** Antes de propor alterações em regras ou telas, leia os documentos correspondentes em `docs/` e o `CONTEXT.md`.
2. **Mudanças Mínimas e Cirúrgicas:** Faça a menor alteração suficiente que satisfaça a tarefa solicitada. Não refatore código alheio sem pedido explícito.
3. **Validação Automatizada Mandatória:** Antes de considerar uma tarefa concluída, execute o validador do repositório:
   ```bash
   ./scripts/verify.sh
   ```
4. **Atualização da Documentação:** Ao concluir uma etapa ou tarefa, atualize os checkboxes correspondentes em `docs/arquitetura_cadastro_alunos.md` e, se novos termos surgirem, registre-os imediatamente em `CONTEXT.md`.

---

## ⚡ Comandos Oficiais do Repositório

### Validação e Qualidade Geral
```bash
./scripts/verify.sh            # Valida tudo (Backend Pytest + Frontend Linter/Build)
./scripts/verify.sh --backend  # Apenas testes do backend Python
./scripts/verify.sh --frontend # Apenas auditoria shadcn e build do frontend
./scripts/verify.sh --quick    # Checagem rápida (sem rebuild completo de produção)
```

### Backend (Python / FastAPI)
```bash
cd backend
source .venv/bin/activate

# Executar suíte de testes
pytest -v

# Inicializar banco e seed do administrador
python -m app.seeds.admin_seed

# Iniciar servidor de desenvolvimento FastAPI
uvicorn app.main:app --reload --port 8000
```

### Frontend (React / Vite / Tailwind v4 / shadcn)
```bash
cd frontend

# Auditoria de componentes shadcn
python3 ../scripts/check_shadcn_usage.py

# Iniciar servidor local
npm run dev

# Checagem de tipos e build
npm run build
```
