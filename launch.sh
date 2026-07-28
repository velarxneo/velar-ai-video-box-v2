#!/usr/bin/env bash
# Velar AI Video Box v2 - start ComfyUI.

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VELAR_HOME="${VELAR_HOME:-$HOME/velar}"

if [ -f "$VELAR_HOME/env.sh" ]; then
    # shellcheck disable=SC1090
    source "$VELAR_HOME/env.sh"
fi

VELAR_VENV="${VELAR_VENV:-$VELAR_HOME/venv}"
COMFYUI_ROOT="${COMFYUI_ROOT:-$VELAR_HOME/ComfyUI}"

if [ ! -d "$VELAR_VENV" ]; then
    echo "[velar] venv not found at $VELAR_VENV - run ./install.sh first" >&2
    exit 1
fi

# shellcheck disable=SC1091
source "$VELAR_VENV/bin/activate"
export COMFYUI_ROOT

exec python "$SCRIPT_DIR/scripts/start_comfyui.py"
