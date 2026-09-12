"""Builds a "used-by" reference graph for layers, text styles, linetypes,
dimstyles, and blocks. ezdxf has no PURGE call, so this reimplements the
question AutoCAD's PURGE answers: "is this resource still referenced?"

Layers/styles/linetypes/dimstyles are considered used if referenced by ANY
entity anywhere, even inside a block that is itself never inserted -- this
mirrors real PURGE's conservative behaviour (it won't purge a layer used only
inside an orphan block until that block itself is purged first).

Blocks are different: "used" means reachable by a chain of INSERTs starting
from a root space (model space or any paperspace layout), computed by graph
reachability so nested-block usage is resolved correctly in one pass.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ezdxf.document import Drawing
from ezdxf.lldxf.const import DXFAttributeError

RESERVED_LAYERS = {"0", "DEFPOINTS"}
RESERVED_STYLES = {"STANDARD"}
RESERVED_LINETYPES = {"CONTINUOUS", "BYLAYER", "BYBLOCK"}

_STYLE_BEARING_TYPES = {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"}
_INLINE_FONT_OVERRIDE_RE = re.compile(r"\\f([^;]*);", re.IGNORECASE)


def _get(entity, key: str, default: Any = None) -> Any:
    """entity.dxf.get() raises DXFAttributeError (not just returning the
    default) when `key` isn't a valid attribute for this entity type at all
    -- true for AutoCAD extension entities like ARCALIGNEDTEXT that ezdxf
    loads without the full common-attribute set."""
    try:
        return entity.dxf.get(key, default)
    except DXFAttributeError:
        return default


@dataclass
class ReferenceGraph:
    used_layers: set[str] = field(default_factory=set)
    used_styles: set[str] = field(default_factory=set)
    used_linetypes: set[str] = field(default_factory=set)
    used_dimstyles: set[str] = field(default_factory=set)
    used_blocks: set[str] = field(default_factory=set)
    inline_font_overrides: dict[str, list[str]] = field(default_factory=dict)  # file-relative: unused here, see checks

    def is_layer_used(self, name: str) -> bool:
        return name.strip().upper() in RESERVED_LAYERS or name in self.used_layers

    def is_style_used(self, name: str) -> bool:
        return name.strip().upper() in RESERVED_STYLES or name in self.used_styles

    def is_linetype_used(self, name: str) -> bool:
        return name.strip().upper() in RESERVED_LINETYPES or name in self.used_linetypes

    def is_block_used(self, name: str) -> bool:
        return name in self.used_blocks


def is_purgeable_block_name(name: str) -> bool:
    """Anonymous (*D.../*U...), layout-backing (*Model_Space/*Paper_Space),
    and legacy shape blocks (_CLOSEDFILLED etc.) are never user-purgeable
    and would just be noise in a purge report."""
    return not name.startswith("*") and not name.startswith("_")


def scan(doc: Drawing) -> ReferenceGraph:
    graph = ReferenceGraph()

    header_dimstyle = doc.header.get("$DIMSTYLE")
    if header_dimstyle:
        graph.used_dimstyles.add(header_dimstyle)

    insert_edges: dict[str, set[str]] = {}
    roots: set[str] = set()
    xref_blocks: set[str] = set()

    for block in doc.blocks:
        block_name = block.name
        if block.block_record.is_any_layout:
            roots.add(block_name)
        if block.block_record.is_xref:
            xref_blocks.add(block_name)

        children: set[str] = set()

        for entity in block:
            dxftype = entity.dxftype()

            layer = _get(entity, "layer")
            if layer:
                graph.used_layers.add(layer)

            linetype = _get(entity, "linetype")
            if linetype and linetype.upper() not in ("BYLAYER", "BYBLOCK"):
                graph.used_linetypes.add(linetype)

            if dxftype in _STYLE_BEARING_TYPES:
                style = _get(entity, "style")
                if style:
                    graph.used_styles.add(style)
                if dxftype == "MTEXT":
                    for match in _INLINE_FONT_OVERRIDE_RE.finditer(entity.text):
                        graph.inline_font_overrides.setdefault(block_name, []).append(match.group(1))

            if dxftype == "DIMENSION":
                dimstyle = _get(entity, "dimstyle")
                if dimstyle:
                    graph.used_dimstyles.add(dimstyle)

            if dxftype == "INSERT":
                target = _get(entity, "name")
                if target:
                    children.add(target)

            if dxftype == "VIEWPORT":
                for frozen in getattr(entity, "frozen_layers", None) or []:
                    graph.used_layers.add(frozen)

        insert_edges[block_name] = children

    # Layers, styles, and linetypes referenced directly by table/style
    # entries themselves (not just entities) also count as "used".
    for layer_entry in doc.layers:
        lt = layer_entry.dxf.get("linetype", None)
        if lt and lt.upper() not in ("BYLAYER", "BYBLOCK"):
            graph.used_linetypes.add(lt)

    for dimstyle_entry in doc.dimstyles:
        dimtxsty = dimstyle_entry.dxf.get("dimtxsty", None)
        if dimtxsty:
            graph.used_styles.add(dimtxsty)

    # Block reachability: BFS from every root (model space + paperspace layouts).
    seen: set[str] = set()
    frontier = list(roots)
    while frontier:
        name = frontier.pop()
        if name in seen:
            continue
        seen.add(name)
        for child in insert_edges.get(name, ()):
            if child not in seen:
                frontier.append(child)
    graph.used_blocks = seen | xref_blocks  # xrefs are always considered "used" (can't be purged anyway)

    return graph
