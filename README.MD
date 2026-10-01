# 🎓 GL4 SGA-EDU — Sistema de Gestão Acadêmica

Sistema moderno, robusto e escalável de Gestão Acadêmica desenvolvido com foco em alta performance, boas práticas de engenharia de software (DDD, SOLID, Clean Architecture e TDD) e uma experiência visual contemporânea.

---

## 🚀 Stack Tecnológica

### Backend
- **Python 3.10+** (FastAPI)
- **SQLAlchemy 2.0** (ORM agnóstico com suporte nativo a UUIDs)
- **Pydantic v2** (Validação estrita de contratos de dados)
- **Passlib & Bcrypt** (Criptografia e hashing seguro de senhas)
- **PyJWT** (Autenticação Stateless com JWT Bearer Token e RBAC)
- **Pytest** (Suíte completa de testes unitários e de integração em memória)

### Frontend
- **React 19** com **TypeScript**
- **Vite** (Build ultra-rápido com `@tailwindcss/vite`)
- **Tailwind CSS v4** (CSS-first e variáveis modernas)
- **shadcn/ui** (Catálogo completo de componentes acessíveis)
- **Tema Meridian** (Paleta harmoniosa em `oklch` via Tweakcn com suporte a Dark Mode)
- **Axios** (Comunicação HTTP com interceptors automáticos para Bearer token)
- **Lucide React** (Ícones modernos)

---

## 📚 Documentação Oficial

Toda a arquitetura e governança do projeto estão detalhadas na pasta `docs/` e na raiz:

| Documento | Descrição |
| :--- | :--- |
| **[AGENTS.md](AGENTS.md)** | **Governança única para Agentes de IA** (invariantes, comandos e fluxo de trabalho). |
| **[CONTEXT.md](CONTEXT.md)** | **Linguagem Ubíqua e Domínio** (glossário canônico e limites entre entidades). |
| **[docs/arquitetura_cadastro_alunos.md](docs/arquitetura_cadastro_alunos.md)** | **Documento Mestre**: Especificação da API, schemas, regras de negócio e roteiro passo a passo. |
| **[docs/arquitetura_autenticacao_rbac.md](docs/arquitetura_autenticacao_rbac.md)** | **Segurança & RBAC**: Fluxos de login, tokens JWT, permissões e proteção de endpoints. |
| **[docs/planejamento_fase1_frontend.md](docs/planejamento_fase1_frontend.md)** | **Frontend Setup**: Vite, Tailwind v4, shadcn/ui e integração do tema Meridian. |
| **[docs/setup_ambiente_backend.md](docs/setup_ambiente_backend.md)** | **Backend Setup**: Guia de criação do ambiente virtual Python e instalação de pacotes. |

---

## ⚡ Comandos Rápidos

### 1. Validação Automatizada de Qualidade (All-in-One)
O projeto conta com script de verificação integrado que roda testes do backend, linter de shadcn e build do frontend:

```bash
./scripts/verify.sh            # Validação completa (Backend Pytest + Frontend Linter & Build)
./scripts/verify.sh --backend  # Apenas testes do backend Python
./scripts/verify.sh --frontend # Apenas auditoria shadcn e build do frontend
./scripts/verify.sh --quick    # Checagem rápida de tipos sem build de produção
```

### 2. Executando o Backend
```bash
cd backend
source .venv/bin/activate

# Executar testes unitários
pytest -v

# Criar tabelas e administrador padrão
python -m app.seeds.admin_seed

# Subir servidor FastAPI
uvicorn app.main:app --reload --port 8000
```
Swagger interativo da API: `http://localhost:8000/docs`

### 3. Executando o Frontend
```bash
cd frontend

# Auditoria de componentes shadcn
python3 ../scripts/check_shadcn_usage.py

# Iniciar servidor local Vite
npm run dev

# Checagem de tipos e compilação
npm run build
```
Aplicação web: `http://localhost:5173`