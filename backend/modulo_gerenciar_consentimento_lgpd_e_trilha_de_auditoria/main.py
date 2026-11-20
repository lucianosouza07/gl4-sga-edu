"""Entrypoint ASGI do microsserviço/módulo de Consentimento LGPD e Trilha de Auditoria."""

import uvicorn
from .router import criar_app

app = criar_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
