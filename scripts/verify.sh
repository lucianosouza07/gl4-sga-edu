#!/usr/bin/env bash
# ==============================================================================
# verify.sh — Validador Completo de Qualidade e Build do GL4 SGA-EDU
#
# Estrutura:
#  1. Backend: Executa Pytest no ambiente virtual (.venv)
#  2. Frontend: Validação de Shadcn UI + Typecheck (tsc) + Build (Vite)
#
# Uso:
#   ./scripts/verify.sh            # Validação completa (Backend + Frontend)
#   ./scripts/verify.sh --backend  # Apenas backend Python
#   ./scripts/verify.sh --frontend # Apenas frontend React
#   ./scripts/verify.sh --quick    # Verificação rápida (sem rebuild completo do front)
# ==============================================================================

set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

run_backend=true
run_frontend=true
quick_mode=false

for arg in "$@"; do
  case $arg in
    --backend|--api)
      run_backend=true
      run_frontend=false
      ;;
    --frontend|--web)
      run_backend=false
      run_frontend=true
      ;;
    --quick)
      quick_mode=true
      ;;
    -h|--help)
      echo -e "${BOLD}Uso:${RESET} ./scripts/verify.sh [--backend | --frontend] [--quick]"
      exit 0
      ;;
  esac
done

echo -e "\n${BOLD}${BLUE}======================================================${RESET}"
echo -e "${BOLD}${BLUE}   GL4 SGA-EDU — Verificação de Qualidade e Testes    ${RESET}"
echo -e "${BOLD}${BLUE}======================================================${RESET}\n"

# ------------------------------------------------------------------------------
# 1. BACKEND
# ------------------------------------------------------------------------------
if [ "$run_backend" = true ]; then
  echo -e "${BOLD}[1/2] 🐍 Verificando Backend (Python / FastAPI)...${RESET}"
  
  if [ ! -d "backend/.venv" ]; then
    echo -e "${RED}Erro: Ambiente virtual 'backend/.venv' não encontrado.${RESET}"
    echo "Crie o ambiente com: cd backend && python3 -m venv .venv && pip install -r requirements.txt"
    exit 1
  fi

  cd backend
  echo -e "  ↳ Executando testes unitários e de integração com pytest..."
  ./.venv/bin/pytest -v
  cd "$REPO_ROOT"
  echo -e "${GREEN}  ✓ Backend validado com sucesso!${RESET}\n"
fi

# ------------------------------------------------------------------------------
# 2. FRONTEND
# ------------------------------------------------------------------------------
if [ "$run_frontend" = true ]; then
  echo -e "${BOLD}[2/2] ⚛️  Verificando Frontend (React / Vite / shadcn)...${RESET}"

  if [ ! -d "frontend/node_modules" ]; then
    echo -e "${RED}Erro: 'frontend/node_modules' não encontrado. Execute 'npm install' em frontend.${RESET}"
    exit 1
  fi

  echo -e "  ↳ Auditando uso de componentes shadcn/ui..."
  python3 scripts/check_shadcn_usage.py

  cd frontend
  if [ "$quick_mode" = true ]; then
    echo -e "  ↳ Executando Typecheck rápido (tsc -b)..."
    npx tsc -b
  else
    echo -e "  ↳ Executando Typecheck e Build de Produção (npm run build)..."
    npm run build
  fi
  cd "$REPO_ROOT"
  echo -e "${GREEN}  ✓ Frontend validado com sucesso!${RESET}\n"
fi

echo -e "${BOLD}${GREEN}======================================================${RESET}"
echo -e "${BOLD}${GREEN}   ✅ TODAS AS VERIFICAÇÕES PASSARAM COM SUCESSO!     ${RESET}"
echo -e "${BOLD}${GREEN}======================================================${RESET}\n"
