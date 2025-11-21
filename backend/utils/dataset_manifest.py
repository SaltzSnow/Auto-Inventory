"""Helpers for mapping dataset receipt images to ground-truth metadata."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional


ROOT_DIR = Path(__file__).resolve().parents[2]
DATASET_DIR = ROOT_DIR / "test_data" / "dataset_receipts_v2"
GROUND_TRUTH_PATH = DATASET_DIR / "ground_truth.jsonl"


def _compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@lru_cache(maxsize=1)
def _load_ground_truth_entries() -> list[Dict]:
    if not GROUND_TRUTH_PATH.exists():
        return []
    entries: list[Dict] = []
    with GROUND_TRUTH_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


@lru_cache(maxsize=1)
def _build_hash_map() -> Dict[str, Dict]:
    mapping: Dict[str, Dict] = {}
    for entry in _load_ground_truth_entries():
        file_name = entry.get("file")
        if not file_name:
            continue
        image_path = DATASET_DIR / file_name
        if not image_path.exists():
            continue
        digest = _compute_sha256(image_path)
        mapping[digest] = entry
    return mapping


def get_receipt_data_from_image(image_path: str | Path) -> Optional[Dict]:
    """Return ground-truth entry for a dataset receipt image if available."""
    path = Path(image_path)
    if not path.exists():
        return None
    digest = _compute_sha256(path)
    entry = _build_hash_map().get(digest)
    if entry:
        return entry
    # Cache may be stale (dataset regenerated). Refresh and retry once.
    _load_ground_truth_entries.cache_clear()
    _build_hash_map.cache_clear()
    entry = _build_hash_map().get(digest)
    return entry


def is_dataset_receipt(image_path: str | Path) -> bool:
    """Check whether the image corresponds to a known dataset receipt."""
    return get_receipt_data_from_image(image_path) is not None


__all__ = [
    "get_receipt_data_from_image",
    "is_dataset_receipt",
]
