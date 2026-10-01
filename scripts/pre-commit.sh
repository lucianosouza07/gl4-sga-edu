#!/usr/bin/env bash
# ==============================================================================
# pre-commit.sh — PreToolUse Hook de Segurança e Qualidade para o Antigravity
#
# 1. Bloqueia sumariamente vazamento de segredos (.env, .db, .sqlite3, .key, .pem).
# 2. Ao tentar 'git commit', executa o validador mestre ./scripts/verify.sh.
#    Se qualquer teste ou build falhar, nega o commit e exige correção pela IA.
# ==============================================================================

set -euo pipefail

PAYLOAD=$(cat)
COMMAND_LINE=$(echo "$PAYLOAD" | jq -r '.toolCall.args.CommandLine // empty')
SENSITIVE_PATTERN='(\.env(\..+)?|\.db|\.sqlite3|\.key|\.pem|\.crt|\.pfx|id_rsa|secrets\.json|creds\.md)$'

if echo "$COMMAND_LINE" | grep -qE '\bgit\s+(commit|add)\b'; then
  # 1. Verifica se a linha de comando cita explicitamente arquivo sensível
  if echo "$COMMAND_LINE" | grep -qE "$SENSITIVE_PATTERN"; then
    cat <<EOF
{
  "decision": "deny",
  "reason": "BLOQUEIO DE SEGURANÇA: Comando contém referências explícitas a arquivos sensíveis (.env, credenciais, banco local ou chaves)."
}
EOF
    exit 0
  fi

  # 2. Verifica arquivos já colocados em staging (git index)
  if echo "$COMMAND_LINE" | grep -qE '\bgit\s+commit\b'; then
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      STAGED_SENSITIVE=$(git diff --cached --name-only | grep -E "$SENSITIVE_PATTERN" || true)
      if [ -n "$STAGED_SENSITIVE" ]; then
        ESCAPED_FILES=$(echo "$STAGED_SENSITIVE" | tr '\n' ' ')
        cat <<EOF
{
  "decision": "deny",
  "reason": "BLOQUEIO DE SEGURANÇA: Tentativa de commitar arquivos sensíveis em staging: ${ESCAPED_FILES}. Remova-os do git stage antes de continuar."
}
EOF
        exit 0
      fi

      # 3. Executa o validador mestre verify.sh antes de permitir o commit
      REPO_ROOT="$(git rev-parse --show-toplevel)"
      VERIFY_OUTPUT=""
      if ! VERIFY_OUTPUT=$("$REPO_ROOT/scripts/verify.sh" 2>&1); then
        ESCAPED_OUTPUT=$(echo "$VERIFY_OUTPUT" | tail -n 25 | jq -s -R .)
        cat <<EOF
{
  "decision": "deny",
  "reason": "BLOQUEIO DE QUALIDADE: A validação em ./scripts/verify.sh falhou! O agente deve analisar o erro e corrigir o código antes de commitar:\n" + ${ESCAPED_OUTPUT}
}
EOF
        exit 0
      fi
    fi
  fi
fi

cat <<EOF
{
  "decision": "allow"
}
EOF
exit 0
