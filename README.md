# Velar AI Video Box v2

Installer-first bootstrap for ComfyUI on ephemeral GPU nodes (SaladCloud,
RunPod, Vast.ai, local Ubuntu). No Docker required. Every time the node
restarts from a blank disk, re-run the two install steps and you're back
where you left off.

```bash
git clone https://github.com/velarxneo/velar-ai-video-box-v2.git
cd velar-ai-video-box-v2
./install.sh            # step 1: ComfyUI + ComfyUI-Manager + custom nodes
./install_models.sh     # step 2: pick which workflow's models to download
./launch.sh             # start ComfyUI
```

Both install steps are idempotent - safe to re-run. `install.sh` skips
anything already present (ComfyUI checkout, venv, PyTorch); `install_models.sh`
skips any model file that's already downloaded and verified.

## Step 2: choosing a model pack

`./install_models.sh` lists every manifest in `manifests/` and lets you pick
one interactively. Non-interactively:

```bash
./install_models.sh --list
./install_models.sh wan22_i2v_14b_fp8
./install_models.sh wan22_i2v_14b_fp8 wan22_ti2v_5b_fp16   # install more than one
./install_models.sh --verify-only wan22_i2v_14b_fp8
```

Available packs out of the box:

| id | pack | size |
| --- | --- | --- |
| `wan22_i2v_14b_fp8` | Wan 2.2 Image-to-Video 14B, FP8 scaled | ~37 GB |
| `wan22_t2v_14b_fp8` | Wan 2.2 Text-to-Video 14B, FP8 scaled | ~37 GB |
| `wan22_ti2v_5b_fp16` | Wan 2.2 TI2V 5B, single-file, low VRAM | ~12 GB |

## Adding a new model pack

Drop a new `manifests/<id>.json` file - no code changes needed. It shows up
in `install_models.sh` automatically. Shape:

```json
{
  "id": "my_pack",
  "name": "Human-readable name",
  "models": [
    {
      "filename": "model.safetensors",
      "folder": "diffusion_models",
      "url": "https://example.com/model.safetensors",
      "required": true,
      "sha256": "optional-64-char-checksum",
      "size": 123456789
    }
  ]
}
```

`sha256` and `size` are optional. Without them, verification can only prove
the file is non-empty - add a checksum for production packs.

## Custom nodes

Declared in `custom_nodes.json`. `ComfyUI-Manager` and
`ComfyUI-VideoHelperSuite` are required; missing repos are cloned and their
`requirements.txt` installed automatically by `install.sh`.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `VELAR_HOME` | `~/velar` | Root for venv, env.sh, and (by default) ComfyUI |
| `COMFYUI_ROOT` | `$VELAR_HOME/ComfyUI` | Where ComfyUI is checked out |
| `COMFYUI_REPO` | `https://github.com/comfyanonymous/ComfyUI.git` | Upstream ComfyUI repo |
| `TORCH_INDEX_URL` | `https://download.pytorch.org/whl/cu124` | PyTorch wheel index (change for a different CUDA version) |
| `VELAR_MODELS_DIR` | `$COMFYUI_ROOT/models` | Model install root |
| `VELAR_MANIFEST_DIR` | `./manifests` | Where `install_models.sh` looks for packs |
| `VELAR_DOWNLOAD_RETRIES` | `4` | Download attempts per file |
| `VELAR_DOWNLOAD_TIMEOUT` | `300` | Per-read timeout in seconds |
| `VELAR_LOG_LEVEL` | `INFO` | Python log level |
| `COMFYUI_LISTEN` | `::` | Bind address (IPv6 dual-stack; required by Salad's ingress) |
| `COMFYUI_PORT` | `8188` | ComfyUI port |
| `COMFYUI_ARGS` | empty | Extra args passed through to ComfyUI |

## Persistent storage (optional)

If your GPU provider offers a persistent volume, point Velar at it so
restarts don't re-download models:

```bash
export VELAR_MODELS_DIR=/data/models
export COMFYUI_ROOT=/data/ComfyUI   # keeps custom nodes too
```

Without a persistent volume, every fresh node just runs the three commands
above again.

## Design principles

- Installer-first: no Docker dependency, works directly on a bare Ubuntu GPU box.
- Idempotent: safe to run `install.sh` / `install_models.sh` repeatedly.
- Manifest-driven: the installer scripts contain no model-specific URLs.
- No systemd required: works inside managed GPU containers as well as full VMs.
