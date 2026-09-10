"""Loads a DXF file defensively: a single corrupt file must never abort a batch run."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import ezdxf
import ezdxf.recover
from ezdxf.document import Drawing


@dataclass
class LoadResult:
    doc: Drawing | None
    needed_repair: bool = False
    error: str | None = None


def load(path: Path) -> LoadResult:
    try:
        doc = ezdxf.readfile(str(path))
        return LoadResult(doc=doc)
    except ezdxf.DXFStructureError:
        pass
    except OSError as exc:
        return LoadResult(doc=None, error=str(exc))

    try:
        doc, auditor = ezdxf.recover.readfile(str(path))
        if auditor.has_errors:
            detail = "; ".join(str(e) for e in auditor.errors[:5])
            return LoadResult(doc=doc, needed_repair=True, error=detail)
        return LoadResult(doc=doc, needed_repair=True)
    except Exception as exc:  # noqa: BLE001 - last-resort guard, never let one file kill the run
        return LoadResult(doc=None, error=str(exc))
