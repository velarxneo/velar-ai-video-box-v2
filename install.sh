#!/usr/bin/env bash
# Velar AI Video Box v2 - Step 1: install ComfyUI + custom nodes.
#
# Designed for ephemeral GPU nodes (SaladCloud, RunPod, Vast.ai, local Ubuntu)
# that start from a blank disk every time. Safe to re-run (idempotent).
#
# Usage:
#   git clone https://github.com/velarxneo/velar-ai-video-box-v2.git
#   cd velar-ai-video-box-v2
#   ./install.sh
#   ./install_models.sh
#   ./launch.sh

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

VELAR_HOME="${VELAR_HOME:-$HOME/velar}"
COMFYUI_ROOT="${COMFYUI_ROOT:-$VELAR_HOME/ComfyUI}"
VELAR_VENV="${VELAR_VENV:-$VELAR_HOME/venv}"
TORCH_INDEX_URL="${TORCH_INDEX_URL:-https://download.pytorch.org/whl/cu124}"
COMFYUI_REPO="${COMFYUI_REPO:-https://github.com/comfyanonymous/ComfyUI.git}"

log() { echo "[velar] $*"; }

mkdir -p "$VELAR_HOME"

# ----------------------------------------------------------------------
# System packages (skipped if not root - assume already provisioned)
# ----------------------------------------------------------------------
if [ "$(id -u)" -eq 0 ] && command -v apt-get >/dev/null 2>&1; then
    log "Installing system packages"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends \
        git git-lfs ffmpeg curl wget unzip ca-certificates \
        build-essential python3 python3-venv python3-pip \
        libgl1 libglib2.0-0 libsm6 libxext6 libxrender1
    git lfs install --skip-repo >/dev/null 2>&1 || true
else
    log "Not root or apt-get unavailable; skipping system package install"
    log "(assumes git, python3, ffmpeg are already present on this image)"
fi

# ----------------------------------------------------------------------
# ComfyUI checkout
# ----------------------------------------------------------------------
if [ -d "$COMFYUI_ROOT/.git" ]; then
    log "ComfyUI already present at $COMFYUI_ROOT, pulling latest"
    git -C "$COMFYUI_ROOT" pull --ff-only || log "Pull failed, continuing with existing checkout"
else
    log "Cloning ComfyUI into $COMFYUI_ROOT"
    git clone --depth 1 "$COMFYUI_REPO" "$COMFYUI_ROOT"
fi

# ----------------------------------------------------------------------
# Python virtual environment
# ----------------------------------------------------------------------
if [ ! -d "$VELAR_VENV" ]; then
    log "Creating virtualenv at $VELAR_VENV"
    python3 -m venv "$VELAR_VENV"
fi

# shellcheck disable=SC1091
source "$VELAR_VENV/bin/activate"

python -m pip install --upgrade pip setuptools wheel -q

if ! python -c "import torch" >/dev/null 2>&1; then
    log "Installing PyTorch from $TORCH_INDEX_URL"
    pip install --index-url "$TORCH_INDEX_URL" torch torchvision torchaudio -q
else
    log "PyTorch already installed, skipping"
fi

log "Installing ComfyUI requirements"
pip install -r "$COMFYUI_ROOT/requirements.txt" -q

log "Installing Velar bootstrap requirements"
pip install -r "$SCRIPT_DIR/requirements-bootstrap.txt" -q

# ----------------------------------------------------------------------
# Model / workflow directories
# ----------------------------------------------------------------------
mkdir -p \
    "$COMFYUI_ROOT/models/diffusion_models" \
    "$COMFYUI_ROOT/models/text_encoders" \
    "$COMFYUI_ROOT/models/vae" \
    "$COMFYUI_ROOT/models/vae_approx" \
    "$COMFYUI_ROOT/models/loras" \
    "$COMFYUI_ROOT/models/clip_vision" \
    "$COMFYUI_ROOT/models/controlnet" \
    "$COMFYUI_ROOT/models/upscale_models" \
    "$COMFYUI_ROOT/input" \
    "$COMFYUI_ROOT/output" \
    "$COMFYUI_ROOT/user/default/workflows"

# ----------------------------------------------------------------------
# Custom nodes (ComfyUI-Manager, VideoHelperSuite, ...)
# ----------------------------------------------------------------------
log "Installing custom nodes"
VELAR_NODES_CONFIG="$SCRIPT_DIR/custom_nodes.json" \
VELAR_CUSTOM_NODES_DIR="$COMFYUI_ROOT/custom_nodes" \
    python "$SCRIPT_DIR/scripts/install_nodes.py"

# ----------------------------------------------------------------------
# Persist resolved paths for install_models.sh / launch.sh
# ----------------------------------------------------------------------
cat > "$VELAR_HOME/env.sh" <<EOF
export VELAR_HOME="$VELAR_HOME"
export COMFYUI_ROOT="$COMFYUI_ROOT"
export VELAR_VENV="$VELAR_VENV"
EOF

log "Step 1 complete: ComfyUI installed at $COMFYUI_ROOT"
log "Next:  ./install_models.sh   (pick which workflow's models to download)"
log "Then:  ./launch.sh"
