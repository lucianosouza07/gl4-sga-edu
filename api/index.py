import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
MAIN_MODULE_DIR = BACKEND_DIR / "modulo_34_cadastrar_professor"

for path in (str(BACKEND_DIR), str(MAIN_MODULE_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

from modulo_34_cadastrar_professor.main import app  # noqa: E402, F401
