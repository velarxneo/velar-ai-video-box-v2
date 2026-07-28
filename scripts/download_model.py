"""Download model packs declared in manifests/<id>.json.

Adding a new selectable pack requires only another manifest file - this
script contains no model-specific URLs.

Usage:
    python scripts/download_model.py <manifest-id> [<manifest-id> ...]
    python scripts/download_model.py --list
    python scripts/download_model.py --verify-only <manifest-id>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import time
from pathlib import Path

import requests
from tqdm import tqdm

from utils import configure_logging, env_int, env_path

LOGGER = logging.getLogger("velar.download")

CHUNK_SIZE = 1024 * 1024  # 1 MiB


def load_manifest(manifest_dir: Path, manifest_id: str) -> dict:
    path = manifest_dir / f"{manifest_id}.json"
    if not path.is_file():
        LOGGER.error("Manifest not found: %s", path)
        raise SystemExit(1)
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def list_manifests(manifest_dir: Path) -> list[dict]:
    manifests = []
    if not manifest_dir.is_dir():
        return manifests
    for path in sorted(manifest_dir.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            LOGGER.warning("Skipping unreadable manifest %s: %s", path, exc)
            continue
        manifests.append({"id": data.get("id", path.stem), "name": data.get("name", path.stem)})
    return manifests


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Path, entry: dict) -> bool:
    if not path.is_file():
        return False
    expected_size = entry.get("size")
    if expected_size and path.stat().st_size != expected_size:
        return False
    expected_sha = entry.get("sha256")
    if expected_sha:
        return sha256_file(path) == expected_sha.lower()
    return path.stat().st_size > 0


def download_file(entry: dict, dest_root: Path, retries: int, timeout: int) -> bool:
    folder = entry["folder"]
    filename = entry["filename"]
    url = entry["url"]
    required = bool(entry.get("required", True))

    dest_dir = dest_root / folder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    part = dest.with_name(dest.name + ".part")

    if verify_file(dest, entry):
        LOGGER.info("[%s] already present and verified", filename)
        return True

    for attempt in range(1, retries + 1):
        try:
            resume_from = part.stat().st_size if part.is_file() else 0
            headers = {"Range": f"bytes={resume_from}-"} if resume_from else {}
            with requests.get(url, headers=headers, stream=True, timeout=timeout) as resp:
                if resp.status_code == 416:
                    part.unlink(missing_ok=True)
                    continue
                resp.raise_for_status()
                got_partial = resp.status_code == 206
                mode = "ab" if resume_from and got_partial else "wb"
                if mode == "wb":
                    resume_from = 0
                total = resume_from + int(resp.headers.get("content-length") or 0)
                with part.open(mode) as fh, tqdm(
                    total=total or None,
                    initial=resume_from,
                    unit="B",
                    unit_scale=True,
                    desc=filename,
                ) as bar:
                    for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            fh.write(chunk)
                            bar.update(len(chunk))
            part.rename(dest)
            if verify_file(dest, entry):
                LOGGER.info("[%s] downloaded and verified", filename)
                return True
            LOGGER.warning(
                "[%s] verification failed after download (attempt %d/%d)", filename, attempt, retries
            )
            dest.unlink(missing_ok=True)
        except (requests.RequestException, OSError) as exc:
            LOGGER.warning("[%s] attempt %d/%d failed: %s", filename, attempt, retries, exc)
            time.sleep(min(2**attempt, 30))

    LOGGER.error("[%s] failed after %d attempts", filename, retries)
    return not required


def install_manifest(
    manifest_id: str,
    manifest_dir: Path,
    models_dir: Path,
    retries: int,
    timeout: int,
    verify_only: bool,
) -> bool:
    manifest = load_manifest(manifest_dir, manifest_id)
    LOGGER.info("Installing pack '%s' (%s)", manifest.get("name", manifest_id), manifest_id)
    ok = True
    for entry in manifest.get("models", []):
        if verify_only:
            dest = models_dir / entry["folder"] / entry["filename"]
            status = "OK" if verify_file(dest, entry) else "MISSING/INVALID"
            LOGGER.info("[%s] %s", entry["filename"], status)
            if status != "OK" and entry.get("required", True):
                ok = False
            continue
        if not download_file(entry, models_dir, retries, timeout):
            ok = False
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest_ids", nargs="*", help="Manifest id(s) to install")
    parser.add_argument("--list", action="store_true", help="List available manifests and exit")
    parser.add_argument(
        "--verify-only", action="store_true", help="Only verify existing files, do not download"
    )
    args = parser.parse_args()

    configure_logging()

    manifest_dir = env_path("VELAR_MANIFEST_DIR", "manifests")
    models_dir = env_path("VELAR_MODELS_DIR", "models")
    retries = env_int("VELAR_DOWNLOAD_RETRIES", 4)
    timeout = env_int("VELAR_DOWNLOAD_TIMEOUT", 300)

    if args.list:
        for m in list_manifests(manifest_dir):
            print(f"{m['id']:<28} {m['name']}")
        return 0

    if not args.manifest_ids:
        LOGGER.error("No manifest id given. Use --list to see available packs.")
        return 1

    success = True
    for manifest_id in args.manifest_ids:
        if not install_manifest(
            manifest_id, manifest_dir, models_dir, retries, timeout, args.verify_only
        ):
            success = False

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
