#!/usr/bin/env bash
# Velar AI Video Box v2 - Step 2: pick and download a model/workflow pack.
#
# Usage:
#   ./install_models.sh                     # interactive menu
#   ./install_models.sh wan22_i2v_14b_fp8   # non-interactive, direct id(s)
#   ./install_models.sh --list              # list available packs
#   ./install_models.sh --verify-only <id>  # check existing files, no download

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

export VELAR_MANIFEST_DIR="$SCRIPT_DIR/manifests"
export VELAR_MODELS_DIR="${VELAR_MODELS_DIR:-$COMFYUI_ROOT/models}"

# Pass-through mode: --list, --verify-only, or explicit ids
if [ "$#" -gt 0 ]; then
    exec python "$SCRIPT_DIR/scripts/download_model.py" "$@"
fi

mapfile -t PACKS < <(python "$SCRIPT_DIR/scripts/download_model.py" --list)

if [ "${#PACKS[@]}" -eq 0 ]; then
    echo "[velar] no manifests found in $VELAR_MANIFEST_DIR" >&2
    exit 1
fi

echo "Available workflow model packs:"
echo
PS3=$'\nSelect a pack to install (or All / Quit): '
select pack in "${PACKS[@]}" "All" "Quit"; do
    case "$pack" in
        "Quit")
            exit 0
            ;;
        "All")
            ids=()
            for p in "${PACKS[@]}"; do ids+=("${p%% *}"); done
            python "$SCRIPT_DIR/scripts/download_model.py" "${ids[@]}"
            break
            ;;
        "")
            echo "Invalid selection, try again."
            ;;
        *)
            id="${pack%% *}"
            python "$SCRIPT_DIR/scripts/download_model.py" "$id"
            break
            ;;
    esac
done
