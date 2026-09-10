"""Iterates TEXT/MTEXT as they actually render: world-space height and style,
including text nested inside (possibly scaled, possibly nested) block inserts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from ezdxf.document import Drawing

_MAX_INSERT_DEPTH = 25


@dataclass
class RenderedText:
    dxftype: str
    height: float | None
    style: str | None
    layer: str | None


def _flatten(entity, depth: int = 0) -> Iterator:
    if depth > _MAX_INSERT_DEPTH:
        return
    if entity.dxftype() == "INSERT":
        for child in entity.virtual_entities():
            yield from _flatten(child, depth + 1)
    else:
        yield entity


def iter_rendered_text(doc: Drawing) -> Iterator[RenderedText]:
    spaces = [doc.modelspace()]
    for name in doc.layout_names():
        if name != "Model":
            spaces.append(doc.layouts.get(name))

    for space in spaces:
        for entity in space:
            for flat in _flatten(entity):
                dxftype = flat.dxftype()
                if dxftype == "TEXT":
                    yield RenderedText(
                        dxftype="TEXT",
                        height=flat.dxf.get("height", None),
                        style=flat.dxf.get("style", None),
                        layer=flat.dxf.get("layer", None),
                    )
                elif dxftype == "MTEXT":
                    yield RenderedText(
                        dxftype="MTEXT",
                        height=flat.dxf.get("char_height", None),
                        style=flat.dxf.get("style", None),
                        layer=flat.dxf.get("layer", None),
                    )
