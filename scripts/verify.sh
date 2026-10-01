#!/usr/bin/env bash
# ==============================================================================
# verify.sh — Validador Mestre de Qualidade, Testes e Build do GL4 SGA-EDU
#
# Estrutura:
#  1. Backend: Executa Pytest com medição de cobertura de código (pytest-cov)
#  2. Frontend: Auditoria Shadcn UI + Typecheck estrito (tsc) + Build (Vite)
#
# Uso:
#   ./scripts/verify.sh            # Validação completa (Backend + Frontend)
#   ./scripts/verify.sh --backend  # Apenas backend Python + Cobertura
#   ./scripts/verify.sh --frontend # Apenas frontend React
#   ./scripts/verify.sh --quick    # Verificação rápida (sem rebuild completo do front)
# ==============================================================================

set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Cores e estilização para feedback visual
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

START_TIME=$(date +%s)

echo -e "\n${BOLD}${BLUE}======================================================${RESET}"
echo -e "${BOLD}${BLUE}   GL4 SGA-EDU — Validador Mestre de Qualidade        ${RESET}"
echo -e "${BOLD}${BLUE}======================================================${RESET}\n"

# ------------------------------------------------------------------------------
# 1. BACKEND PYTHON (FastAPI, Pytest & Test Coverage)
# ------------------------------------------------------------------------------
if [ "$run_backend" = true ]; then
  echo -e "${BOLD}${YELLOW}==> [1/2] 🐍 Backend (Python / FastAPI / Cobertura de Testes)${RESET}"
  
  if [ ! -d "backend/.venv" ]; then
    echo -e "${RED}Erro: Ambiente virtual 'backend/.venv' não encontrado.${RESET}"
    echo "Crie o ambiente com: cd backend && python3 -m venv .venv && pip install -r requirements.txt"
    exit 1
  fi

  cd backend
  echo -e "  ↳ Executando suíte de testes com medição de cobertura (pytest-cov)..."
  ./.venv/bin/pytest
  cd "$REPO_ROOT"
  echo -e "${GREEN}  ✓ Backend e Cobertura validados com sucesso!${RESET}\n"
fi

# ------------------------------------------------------------------------------
# 2. FRONTEND WEB (React, Vite, TypeScript & shadcn/ui)
# ------------------------------------------------------------------------------
if [ "$run_frontend" = true ]; then
  echo -e "${BOLD}${YELLOW}==> [2/2] ⚛️  Frontend (React / Vite / Tailwind v4 / shadcn)${RESET}"

  if [ ! -d "frontend/node_modules" ]; then
    echo -e "${RED}Erro: 'frontend/node_modules' não encontrado. Execute 'npm install' em frontend.${RESET}"
    exit 1
  fi

  echo -e "  ↳ Auditando conformidade de componentes Shadcn UI..."
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

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo -e "${BOLD}${GREEN}======================================================${RESET}"
echo -e "${BOLD}${GREEN}   ✅ TODAS AS VERIFICAÇÕES PASSARAM! (${ELAPSED}s)      ${RESET}"
echo -e "${BOLD}${GREEN}======================================================${RESET}\n"
