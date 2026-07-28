"""Install ComfyUI custom nodes declared in custom_nodes.json.

Safe to re-run: existing node directories are left in place (pull manually
inside the node's folder to update). Missing repositories are cloned and
their requirements.txt installed. Failures stop the script for required
nodes and are logged, non-fatally, for optional ones.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

from utils import configure_logging, env_path

LOGGER = logging.getLogger("velar.nodes")


def load_config(path: Path) -> list[dict]:
    if not path.is_file():
        LOGGER.error("Custom node config not found: %s", path)
        raise SystemExit(1)
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("nodes", [])


def install_node(node: dict, nodes_dir: Path) -> bool:
    name = node["name"]
    repo = node["repo"]
    required = bool(node.get("required", False))
    target = nodes_dir / name

    if target.exists():
        LOGGER.info("[%s] already installed, skipping clone", name)
    else:
        LOGGER.info("[%s] cloning %s", name, repo)
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo, str(target)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            LOGGER.error("[%s] clone failed: %s", name, result.stderr.strip())
            if required:
                raise SystemExit(1)
            return False

    requirements = target / "requirements.txt"
    if requirements.is_file():
        LOGGER.info("[%s] installing requirements", name)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            LOGGER.error("[%s] requirements install failed: %s", name, result.stderr.strip())
            if required:
                raise SystemExit(1)
            return False

    LOGGER.info("[%s] ready", name)
    return True


def main() -> int:
    configure_logging()
    config_path = env_path("VELAR_NODES_CONFIG", "custom_nodes.json")
    nodes_dir = env_path("VELAR_CUSTOM_NODES_DIR", "custom_nodes")
    nodes_dir.mkdir(parents=True, exist_ok=True)

    nodes = load_config(config_path)
    if not nodes:
        LOGGER.warning("No custom nodes declared in %s", config_path)
        return 0

    ok = True
    for node in nodes:
        if not install_node(node, nodes_dir):
            ok = False

    if ok:
        LOGGER.info("Custom node installation complete")
    else:
        LOGGER.warning("Custom node installation finished with optional failures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
