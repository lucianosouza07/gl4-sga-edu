#!/usr/bin/env bash
# ==============================================================================
# start.sh — Script Unificado de Inicialização do GL4 SGA-EDU
#
# Inicializa o Backend (FastAPI / Uvicorn) e o Frontend (React / Vite)
# de forma simultânea e gerenciada, com encerramento gracioso via Ctrl+C.
#
# Uso:
#   ./scripts/start.sh            # Inicia Backend e Frontend juntos
#   ./scripts/start.sh --backend  # Inicia apenas o Backend (API)
#   ./scripts/start.sh --frontend # Inicia apenas o Frontend (Web)
#   ./scripts/start.sh --seed     # Roda os seeds de banco antes de iniciar
# ==============================================================================

set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Cores e estilização para feedback visual no terminal
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
MAGENTA="\033[0;35m"
RED="\033[0;31m"
RESET="\033[0m"

run_backend=true
run_frontend=true
run_seed=false
backend_port=8000
frontend_port=5173

# Processamento de argumentos
while [[ $# -gt 0 ]]; do
  case $1 in
    --backend|--api)
      run_backend=true
      run_frontend=false
      shift
      ;;
    --frontend|--web)
      run_backend=false
      run_frontend=true
      shift
      ;;
    --seed)
      run_seed=true
      shift
      ;;
    --backend-port)
      backend_port="$2"
      shift 2
      ;;
    --frontend-port)
      frontend_port="$2"
      shift 2
      ;;
    -h|--help)
      echo -e "${BOLD}GL4 SGA-EDU — Inicializador do Ambiente de Desenvolvimento${RESET}\n"
      echo -e "${BOLD}Uso:${RESET} ./scripts/start.sh [OPÇÕES]\n"
      echo -e "${BOLD}Opções:${RESET}"
      echo -e "  ${CYAN}--backend, --api${RESET}      Inicia apenas o servidor FastAPI (Backend)"
      echo -e "  ${CYAN}--frontend, --web${RESET}     Inicia apenas o servidor Vite (Frontend)"
      echo -e "  ${CYAN}--seed${RESET}                Executa os seeds de administrador e alunos de teste"
      echo -e "  ${CYAN}--backend-port <PORT>${RESET} Define a porta do Backend (padrão: 8000)"
      echo -e "  ${CYAN}--frontend-port <PORT>${RESET}Define a porta do Frontend (padrão: 5173)"
      echo -e "  ${CYAN}-h, --help${RESET}            Exibe esta mensagem de ajuda\n"
      exit 0
      ;;
    *)
      echo -e "${RED}Opção desconhecida: $1${RESET}"
      echo "Use ./scripts/start.sh --help para ver as opções disponíveis."
      exit 1
      ;;
  esac
done

echo -e "\n${BOLD}${BLUE}======================================================${RESET}"
echo -e "${BOLD}${BLUE}   🎓 GL4 SGA-EDU — Inicialização do Projeto          ${RESET}"
echo -e "${BOLD}${BLUE}======================================================${RESET}\n"

# ------------------------------------------------------------------------------
# 1. VERIFICAÇÃO E PREPARAÇÃO DO AMBIENTE
# ------------------------------------------------------------------------------

# Backend: Verifica se .venv existe, caso contrário tenta criar ou instrui o usuário
if [ "$run_backend" = true ] || [ "$run_seed" = true ]; then
  if [ ! -d "backend/.venv" ]; then
    echo -e "${YELLOW}⚠️  Ambiente virtual 'backend/.venv' não encontrado.${RESET}"
    echo -e "Criando ambiente virtual Python..."
    python3 -m venv backend/.venv
    echo -e "Instalando dependências de 'backend/requirements.txt'..."
    backend/.venv/bin/pip install --upgrade pip
    backend/.venv/bin/pip install -r backend/requirements.txt
    echo -e "${GREEN}✓ Ambiente backend configurado com sucesso!${RESET}\n"
  fi
fi

# Frontend: Verifica se node_modules existe
if [ "$run_frontend" = true ]; then
  if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  'frontend/node_modules' não encontrado.${RESET}"
    echo -e "Instalando dependências do frontend com npm..."
    (cd frontend && npm install)
    echo -e "${GREEN}✓ Dependências do frontend instaladas com sucesso!${RESET}\n"
  fi
fi

# ------------------------------------------------------------------------------
# 2. EXECUÇÃO DE SEEDS / INICIALIZAÇÃO DE BANCO
# ------------------------------------------------------------------------------
if [ "$run_seed" = true ]; then
  echo -e "${BOLD}${YELLOW}==> 📦 Executando Seeds do Banco de Dados...${RESET}"
  cd backend
  ./.venv/bin/python -m app.seeds.admin_seed
  ./.venv/bin/python -m app.seeds.alunos_teste
  cd "$REPO_ROOT"
  echo -e "${GREEN}✓ Seeds executados com sucesso!${RESET}\n"
fi

# ------------------------------------------------------------------------------
# 3. GERENCIAMENTO DE PROCESSOS E ENCERRAMENTO GRACIOSO
# ------------------------------------------------------------------------------
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo -e "\n\n${BOLD}${YELLOW}Encerrando os servidores do GL4 SGA-EDU...${RESET}"
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  wait "$BACKEND_PID" 2>/dev/null || true
  wait "$FRONTEND_PID" 2>/dev/null || true
  echo -e "${GREEN}✓ Todos os serviços foram finalizados com segurança.${RESET}\n"
  exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# ------------------------------------------------------------------------------
# 4. INICIALIZAÇÃO DOS SERVIÇOS
# ------------------------------------------------------------------------------

# Resumo de Acesso
echo -e "${BOLD}Serviços configurados para inicialização:${RESET}"
if [ "$run_backend" = true ]; then
  echo -e "  🐍 ${CYAN}Backend FastAPI:${RESET}      http://localhost:${backend_port}"
  echo -e "     ↳ ${BOLD}Swagger Docs:${RESET}     http://localhost:${backend_port}/docs"
  echo -e "     ↳ ${BOLD}Admin Padrão:${RESET}     admin@gl4.edu / admin123"
fi
if [ "$run_frontend" = true ]; then
  echo -e "  ⚛️  ${CYAN}Frontend React/Vite:${RESET}  http://localhost:${frontend_port}"
fi
echo -e "\n${BOLD}${MAGENTA}Pressione [Ctrl+C] a qualquer momento para interromper todos os serviços.${RESET}\n"
echo -e "${BLUE}------------------------------------------------------${RESET}\n"

# Inicializa o Backend
if [ "$run_backend" = true ]; then
  cd backend
  ./.venv/bin/uvicorn app.main:app --reload --port "$backend_port" &
  BACKEND_PID=$!
  cd "$REPO_ROOT"
fi

# Inicializa o Frontend
if [ "$run_frontend" = true ]; then
  cd frontend
  npm run dev -- --port "$frontend_port" &
  FRONTEND_PID=$!
  cd "$REPO_ROOT"
fi

# Aguarda a execução dos processos em primeiro plano
if [ -n "$BACKEND_PID" ] && [ -n "$FRONTEND_PID" ]; then
  wait "$BACKEND_PID" "$FRONTEND_PID"
elif [ -n "$BACKEND_PID" ]; then
  wait "$BACKEND_PID"
elif [ -n "$FRONTEND_PID" ]; then
  wait "$FRONTEND_PID"
fi
