"""Walk a folder and classify every file by extension."""
from __future__ import annotations

from pathlib import Path

from fncsqaqc.models import DiscoveredFile, FileKind

_EXTENSION_MAP = {
    ".dwg": FileKind.DWG,
    ".dxf": FileKind.DXF,
    ".rvt": FileKind.RVT,
    ".pdf": FileKind.PDF,
    ".xlsx": FileKind.XLSX,
    ".xls": FileKind.XLSX,
}

# Folders never worth walking into.
_SKIP_DIR_NAMES = {".git", "__pycache__", "$RECYCLE.BIN"}


def classify(path: Path) -> FileKind:
    return _EXTENSION_MAP.get(path.suffix.lower(), FileKind.OTHER)


def discover(folder: Path) -> list[DiscoveredFile]:
    """Recursively walk `folder`, returning every file with its classification."""
    folder = folder.resolve()
    discovered: list[DiscoveredFile] = []

    for path in _walk(folder):
        stat = path.stat()
        discovered.append(
            DiscoveredFile(
                relative_path=path.relative_to(folder),
                absolute_path=path,
                kind=classify(path),
                size=stat.st_size,
                mtime_ns=stat.st_mtime_ns,
            )
        )

    return discovered


def _walk(folder: Path):
    for entry in folder.iterdir():
        if entry.is_dir():
            if entry.name in _SKIP_DIR_NAMES:
                continue
            yield from _walk(entry)
        elif entry.is_file():
            yield entry
