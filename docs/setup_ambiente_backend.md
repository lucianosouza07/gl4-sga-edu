# 🛠️ Guia de Configuração do Ambiente Backend (Python)

Este documento descreve o passo a passo detalhado para preparar o ambiente virtual Python e instalar as dependências necessárias para o backend do projeto **GL4 SGA EDU**.

---

## 📋 Pré-requisitos

- **Python 3.10+** instalado no sistema operacional.
- Gerenciador de pacotes **pip** instalado.
- Terminal compatível com seu sistema operacional (Bash/Zsh no Linux/macOS ou PowerShell no Windows).

Para verificar a versão instalada do Python:
```bash
python3 --version
# ou no Windows:
python --version
```

---

## 🚀 Passo a Passo

### 1. Criar o `.gitignore` na raiz do projeto (Prevenção)

Para evitar que arquivos temporários, bibliotecas instaladas e dados de cache sejam enviados para o repositório Git, certifique-se de que o `.gitignore` na raiz possua:

```gitignore
# Ambientes virtuais
.venv/
venv/
ENV/

# Python Cache
__pycache__/
*.py[cod]
*$py.class
*.pytest_cache/

# Banco de dados local e variáveis de ambiente
*.db
*.sqlite3
.env
```

---

### 2. Acessar o diretório do backend

Navegue pelo terminal até a pasta `backend`:

```bash
cd backend
```

---

### 3. Criar o Ambiente Virtual (`.venv`)

Crie um ambiente virtual isolado para não misturar os pacotes do projeto com os pacotes globais do seu sistema:

```bash
python3 -m venv .venv
# ou no Windows:
python -m venv .venv
```

> Isso cria o diretório `backend/.venv` contendo o interpretador Python e o gerenciador de pacotes dedicados a este projeto.

---

### 4. Ativar o Ambiente Virtual

A ativação depende do sistema operacional que você está utilizando:

#### No Linux / macOS (Bash ou Zsh):
```bash
source .venv/bin/activate
```

#### No Windows (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```
*(Se ocorrer erro de política de execução no PowerShell, execute antes: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

#### No Windows (Prompt de Comando CMD):
```cmd
.venv\Scripts\activate.bat
```

> **Verificação:** Ao ativar, o prompt do terminal exibirá o prefixo `(.venv)`.

---

### 5. Instalar as Dependências Base

Atualize o instalador de pacotes `pip`:
```bash
pip install --upgrade pip
```

#### Opção A (Recomendada): Usando o `requirements.txt`
Crie ou utilize o arquivo `backend/requirements.txt` com o seguinte conteúdo:

```text
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
sqlalchemy>=2.0.28
pydantic[email]>=2.6.0
passlib[bcrypt]>=1.7.4
bcrypt<4.1.0
pyjwt>=2.8.0
pytest>=8.1.0
httpx>=0.27.0
```

E instale executando:
```bash
pip install -r requirements.txt
```

#### Opção B: Direto via Linha de Comando:
```bash
pip install fastapi uvicorn sqlalchemy "pydantic[email]" "passlib[bcrypt]" "pyjwt>=2.8.0" pytest httpx
```

> ⚠️ **Atenção:** Em terminais Linux e macOS (Zsh/Bash), sempre utilize aspas duplas em `"pydantic[email]"` e `"passlib[bcrypt]"` para evitar que o shell confunda os colchetes com padrões glob de busca de arquivos.

---

### 6. Testar a Instalação

Verifique se todas as bibliotecas foram instaladas e podem ser importadas sem erro:

```bash
python -c "import fastapi, sqlalchemy, pydantic, passlib, jwt, pytest, httpx; print('✅ Ambiente virtual e dependências configurados com sucesso!')"
```

---

### 7. Configuração das Variáveis de Ambiente (`.env`)

Copie o modelo canônico `.env.example` da raiz do projeto para criar o arquivo `.env` local:

```bash
cp ../.env.example ../.env
```

O arquivo `.env` centraliza portas do backend/frontend, conexões de banco de dados (`DATABASE_URL`), segredos JWT, seeds padrão e regras de CORS.

---

## 📌 Comandos Úteis do Dia a Dia

| Ação | Comando |
| :--- | :--- |
| **Ativar o ambiente** | `source .venv/bin/activate` (Linux/Mac) ou `.venv\Scripts\activate` (Win) |
| **Desativar o ambiente** | `deactivate` |
| **Listar pacotes instalados** | `pip list` |
| **Congelar dependências atuais** | `pip freeze > requirements.txt` |
| **Executar os testes** | `pytest` |
