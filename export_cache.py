"""Temporary storage for chart payloads between free export and upgrade exports."""

import json
import os
import shutil
import time
import uuid
from pathlib import Path

def _default_cache_root():
    override = os.environ.get("EXPORT_CACHE_DIR", "").strip()
    if override:
        return Path(override)
    if os.environ.get("VERCEL"):
        return Path("/tmp/5-things-export-cache")
    return Path(__file__).resolve().parent / ".export_cache"


_CACHE_ROOT = _default_cache_root()
_TTL_SECONDS = 60 * 60 * 2


def _ensure_root():
    _CACHE_ROOT.mkdir(parents=True, exist_ok=True)


def _purge_expired():
    if not _CACHE_ROOT.exists():
        return
    now = time.time()
    for entry in _CACHE_ROOT.iterdir():
        if not entry.is_dir():
            continue
        try:
            if now - entry.stat().st_mtime > _TTL_SECONDS:
                shutil.rmtree(entry, ignore_errors=True)
        except OSError:
            pass


def save_export_payload(inputs, charts):
    _purge_expired()
    _ensure_root()
    cache_id = uuid.uuid4().hex
    folder = _CACHE_ROOT / cache_id
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "inputs.json", "w", encoding="utf-8") as f:
        json.dump(inputs, f)
    for key, data_url in (charts or {}).items():
        if not data_url or "," not in str(data_url):
            continue
        _, encoded = str(data_url).split(",", 1)
        path = folder / f"{key}.b64"
        path.write_text(encoded, encoding="utf-8")
    return cache_id


def load_export_payload(cache_id):
    if not cache_id:
        return None, None
    folder = _CACHE_ROOT / str(cache_id)
    if not folder.is_dir():
        return None, None
    inputs_path = folder / "inputs.json"
    if not inputs_path.exists():
        return None, None
    with open(inputs_path, encoding="utf-8") as f:
        inputs = json.load(f)
    charts = {}
    for path in folder.glob("*.b64"):
        key = path.stem
        encoded = path.read_text(encoding="utf-8")
        charts[key] = f"data:image/png;base64,{encoded}"
    return inputs, charts
