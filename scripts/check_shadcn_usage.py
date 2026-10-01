#!/usr/bin/env python3
"""
check_shadcn_usage.py — Validador de Uso Predominante de Componentes Shadcn UI
Adaptado para o projeto GL4 SGA-EDU (React + Vite + Tailwind v4 + shadcn/ui).

Verifica se o código em frontend/src está utilizando componentes nativos do shadcn
ao invés de tags HTML cruas como <button>, <input>, <table>, etc.

Bypass por linha:
    {/* shadcn-ignore: <motivo> */}
    // shadcn-ignore: <motivo>
"""

import re
import sys
from pathlib import Path

NATIVE_TAG_MAP = {
    # Componentes de Ação / Formulário / Estrutura
    "button": {"component": "Button", "import": "@/components/ui/button"},
    "input": {"component": "Input", "import": "@/components/ui/input"},
    "textarea": {"component": "Textarea", "import": "@/components/ui/textarea"},
    "select": {"component": "Select / NativeSelect", "import": "@/components/ui/select"},
    "dialog": {"component": "Dialog", "import": "@/components/ui/dialog"},
    "table": {"component": "Table", "import": "@/components/ui/table"},
    "progress": {"component": "Progress", "import": "@/components/ui/progress"},
    "hr": {"component": "Separator", "import": "@/components/ui/separator"},

    # Tipografia Padronizada Obrigatória
    "h1": {"component": "Typography variant='h1'", "import": "@/components/ui/typography"},
    "h2": {"component": "Typography variant='h2'", "import": "@/components/ui/typography"},
    "h3": {"component": "Typography variant='h3'", "import": "@/components/ui/typography"},
    "h4": {"component": "Typography variant='h4'", "import": "@/components/ui/typography"},
    "h5": {"component": "Typography variant='h4'", "import": "@/components/ui/typography"},
    "h6": {"component": "Typography variant='h4'", "import": "@/components/ui/typography"},
    "blockquote": {"component": "Typography variant='blockquote'", "import": "@/components/ui/typography"},
}

_TAG_PATTERN = re.compile(r"<\s*(" + "|".join(NATIVE_TAG_MAP.keys()) + r")(\s*|\s+[^>]*)>")

IGNORE_DIRS = {"node_modules", "dist", ".next", ".git"}
UI_DIR_NAME = "components/ui"


def check_file(filepath: Path) -> list[tuple[int, str, str]]:
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return findings

    lines = content.splitlines()
    for idx, line in enumerate(lines, start=1):
        if "shadcn-ignore" in line:
            continue

        for match in _TAG_PATTERN.finditer(line):
            tag = match.group(1).lower()
            # Ignora tags de tipo file no input se necessário ou propriedades específicas
            rule = NATIVE_TAG_MAP.get(tag)
            if rule:
                findings.append((idx, tag, f"Use <{rule['component']}> ({rule['import']}) em vez de <{tag}>"))

    return findings


def main():
    root = Path(__file__).resolve().parent.parent / "frontend" / "src"
    if not root.exists():
        print(f"Diretório não encontrado: {root}")
        sys.exit(0)

    total_findings = 0
    checked_files = 0

    for file in root.rglob("*.tsx"):
        # Ignora os próprios componentes internos em components/ui/
        if UI_DIR_NAME in file.as_posix():
            continue

        checked_files += 1
        findings = check_file(file)
        if findings:
            print(f"\n❌ {file.relative_to(root.parent)}:")
            for line_no, tag, msg in findings:
                print(f"   Linha {line_no}: {msg}")
                total_findings += 1

    if total_findings > 0:
        print(f"\n⚠️  Total de inconformidades com shadcn/ui: {total_findings} (em {checked_files} arquivos analisados)")
        print("💡 Substitua pelas tags do shadcn/ui ou adicione {/* shadcn-ignore: <motivo> */} se for justificado.")
        sys.exit(1)
    else:
        print(f"✅ Todos os componentes analisados ({checked_files} arquivos) utilizam shadcn/ui adequadamente!")
        sys.exit(0)


if __name__ == "__main__":
    main()
