#!/usr/bin/env bash
# ==============================================================================
# start.sh — Atalho na raiz para executar scripts/start.sh
# ==============================================================================

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$REPO_ROOT/scripts/start.sh" "$@"
