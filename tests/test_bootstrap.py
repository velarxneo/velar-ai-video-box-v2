"""Basic sanity tests for the Velar bootstrap scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import download_model  # noqa: E402
import install_nodes  # noqa: E402


def test_all_manifests_are_valid_json_with_required_fields():
    manifest_dir = REPO_ROOT / "manifests"
    manifests = list(manifest_dir.glob("*.json"))
    assert manifests, "expected at least one manifest"

    for path in manifests:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert "id" in data
        assert "name" in data
        assert "models" in data and data["models"], f"{path} has no models"
        for entry in data["models"]:
            assert {"filename", "folder", "url"} <= entry.keys()


def test_list_manifests_matches_files_on_disk():
    manifest_dir = REPO_ROOT / "manifests"
    found = download_model.list_manifests(manifest_dir)
    ids = {m["id"] for m in found}
    on_disk = {p.stem for p in manifest_dir.glob("*.json")}
    assert ids == on_disk


def test_custom_nodes_config_is_valid():
    config_path = REPO_ROOT / "custom_nodes.json"
    nodes = install_nodes.load_config(config_path)
    assert nodes, "expected at least one custom node declared"
    for node in nodes:
        assert {"name", "repo"} <= node.keys()
    names = [n["name"] for n in nodes]
    assert "ComfyUI-Manager" in names


def test_verify_file_rejects_missing_file(tmp_path):
    missing = tmp_path / "nope.safetensors"
    assert download_model.verify_file(missing, {"filename": "nope.safetensors"}) is False


def test_verify_file_checks_size_when_declared(tmp_path):
    target = tmp_path / "model.bin"
    target.write_bytes(b"x" * 10)
    assert download_model.verify_file(target, {"size": 10}) is True
    assert download_model.verify_file(target, {"size": 11}) is False


def test_verify_file_checks_sha256_when_declared(tmp_path):
    target = tmp_path / "model.bin"
    target.write_bytes(b"hello world")
    good_sha = download_model.sha256_file(target)
    assert download_model.verify_file(target, {"sha256": good_sha}) is True
    assert download_model.verify_file(target, {"sha256": "0" * 64}) is False
