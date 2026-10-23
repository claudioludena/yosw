#!/usr/bin/env python3
"""
Wrapper para iniciar el servidor desde el directorio 'asistente'.
"""
import sys
from pathlib import Path

# Raíz del repositorio
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server import iniciar_servidor

if __name__ == "__main__":
    import os
    puerto = int(os.environ.get("PORT", 8000))
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        puerto = int(sys.argv[1])
    iniciar_servidor(port=puerto)
