#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [[ ! -s app.py ]]; then
    echo "Error: app.py no existe o está vacío en $PROJECT_DIR" >&2
    exit 1
fi

if [[ ! -s requirements.txt ]]; then
    echo "Error: no se encontró requirements.txt o está vacío." >&2
    exit 1
fi

VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
if [[ ! -x "$VENV_PYTHON" ]]; then
    if ! command -v python3 >/dev/null 2>&1; then
        echo "Error: se necesita python3 para crear el entorno virtual." >&2
        exit 1
    fi
    echo "Creando entorno virtual .venv..."
    python3 -m venv "$PROJECT_DIR/.venv"
    "$VENV_PYTHON" -m pip install --upgrade pip
fi

echo "Verificando dependencias de requirements.txt..."
"$VENV_PYTHON" -m pip install -r "$PROJECT_DIR/requirements.txt"

exec "$VENV_PYTHON" -m streamlit run "$PROJECT_DIR/app.py" "$@"
