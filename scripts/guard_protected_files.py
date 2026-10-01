#!/usr/bin/env python3
"""
guard_protected_files.py — PreToolUse Hook para o Antigravity

Protege arquivos críticos de configuração, segurança e infraestrutura
(scripts de verificação, configs de build, banco de dados e regras de governança),
forçando confirmação explícita do usuário (force_ask) antes de permitir qualquer modificação pela LLM.
"""
import json
import os
import sys
import re

PROTECTED_PATTERNS = [
    r"tsconfig(\..*)?\.json$",
    r"vite\.config\.[cm]?[jt]s$",
    r"scripts/verify\.sh$",
    r"scripts/guard_protected_files\.py$",
    r"scripts/pre-commit\.sh$",
    r"backend/pytest\.ini$",
    r"backend/app/database/session\.py$",
    r"AGENTS\.md$",
]

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        tool_call = payload.get("toolCall", {})
        args = tool_call.get("args", {})
        
        # Identifica o caminho do arquivo alvo
        target_file = args.get("TargetFile") or args.get("target_file") or args.get("path") or ""
        
        if target_file:
            for pattern in PROTECTED_PATTERNS:
                if re.search(pattern, target_file):
                    # Arquivo protegido: exige confirmação explícita do usuário
                    output = {
                        "decision": "force_ask",
                        "reason": f"Alteração no arquivo crítico de governança/configuração '{os.path.basename(target_file)}'. Confirmar alteração?"
                    }
                    print(json.dumps(output))
                    return

        # Para todos os demais arquivos, permite a execução normal
        print(json.dumps({"decision": "allow"}))
    except Exception:
        # Fallback seguro
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
