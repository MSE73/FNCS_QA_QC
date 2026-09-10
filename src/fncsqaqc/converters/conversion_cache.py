"""Persistent manifest tracking which DWGs have already been converted to DXF.

One cache root per scanned folder (keyed by a hash of its resolved path), so
repeat runs against the same project don't reconvert unchanged drawings.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ManifestEntry:
    size: int
    mtime_ns: int
    dxf_relative_path: str
    converted_at: float


class ConversionCache:
    MANIFEST_NAME = "manifest.json"
    DXF_SUBDIR = "dxf"

    def __init__(self, cache_root: Path, source_folder: Path):
        self.source_folder = source_folder.resolve()
        digest = hashlib.sha1(str(self.source_folder).lower().encode("utf-8")).hexdigest()[:16]
        self.root = cache_root / digest
        self.dxf_dir = self.root / self.DXF_SUBDIR
        self.manifest_path = self.root / self.MANIFEST_NAME
        self._manifest: dict[str, ManifestEntry] = {}
        self._load()

    def _load(self) -> None:
        if not self.manifest_path.is_file():
            return
        raw = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self._manifest = {k: ManifestEntry(**v) for k, v in raw.items()}

    def save(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        raw = {k: asdict(v) for k, v in self._manifest.items()}
        self.manifest_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    def _key(self, relative_path: Path) -> str:
        return str(relative_path).replace("\\", "/")

    def is_stale(self, relative_path: Path, size: int, mtime_ns: int) -> bool:
        entry = self._manifest.get(self._key(relative_path))
        if entry is None:
            return True
        if entry.size != size or entry.mtime_ns != mtime_ns:
            return True
        return not (self.dxf_dir / entry.dxf_relative_path).is_file()

    def get_dxf_path(self, relative_path: Path) -> Path | None:
        entry = self._manifest.get(self._key(relative_path))
        if entry is None:
            return None
        candidate = self.dxf_dir / entry.dxf_relative_path
        return candidate if candidate.is_file() else None

    def record(self, relative_path: Path, size: int, mtime_ns: int, dxf_relative_path: Path) -> None:
        self._manifest[self._key(relative_path)] = ManifestEntry(
            size=size,
            mtime_ns=mtime_ns,
            dxf_relative_path=str(dxf_relative_path).replace("\\", "/"),
            converted_at=time.time(),
        )

    def dxf_path_for(self, relative_path: Path) -> Path:
        """Where a DWG's converted DXF should live in the cache, mirroring its
        relative folder structure but with a .dxf extension."""
        return (self.dxf_dir / relative_path).with_suffix(".dxf")
