"""Launch ComfyUI and propagate its exit status."""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
import sys

from utils import configure_logging, env_path

LOGGER = logging.getLogger("velar.launch")


def main() -> int:
    configure_logging()
    root = env_path("COMFYUI_ROOT", os.path.expanduser("~/velar/ComfyUI"))
    main_script = root / "main.py"
    if not main_script.is_file():
        LOGGER.error("ComfyUI entry point not found: %s", main_script)
        LOGGER.error("Run ./install.sh first.")
        return 1

    # "::" (all interfaces, IPv4 + IPv6) is required for SaladCloud's ingress;
    # it also works fine on RunPod / Vast.ai / local Ubuntu.
    host = os.getenv("COMFYUI_LISTEN", "::")
    port = os.getenv("COMFYUI_PORT", "8188")
    extra_args = shlex.split(os.getenv("COMFYUI_ARGS", ""))

    command = [sys.executable, str(main_script), "--listen", host, "--port", port, *extra_args]
    LOGGER.info("Launching ComfyUI on %s:%s", host, port)
    return subprocess.call(command, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
