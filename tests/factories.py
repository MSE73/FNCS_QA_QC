"""Synthetic in-memory DXF document builders for tests."""
from __future__ import annotations

import ezdxf
from ezdxf.document import Drawing


def make_basic_doc() -> Drawing:
    doc = ezdxf.new("R2018")
    doc.styles.add("MEP-DUCT-TAG", font="simplex.shx")
    doc.layers.add("M-DUCT")
    return doc


def make_doc_with_unused_layer() -> Drawing:
    doc = ezdxf.new("R2018")
    doc.layers.add("USED-LAYER")
    doc.layers.add("UNUSED-LAYER")
    doc.modelspace().add_line((0, 0), (1, 1), dxfattribs={"layer": "USED-LAYER"})
    return doc


def make_doc_with_layer_used_only_in_orphan_block() -> Drawing:
    doc = ezdxf.new("R2018")
    doc.layers.add("ORPHAN-LAYER")
    orphan_block = doc.blocks.new("OrphanBlock")
    orphan_block.add_line((0, 0), (1, 1), dxfattribs={"layer": "ORPHAN-LAYER"})
    # OrphanBlock is intentionally never inserted anywhere.
    return doc


def make_doc_with_layer_used_only_via_viewport_freeze() -> Drawing:
    doc = ezdxf.new("R2018")
    doc.layers.add("FROZEN-LAYER")
    psp = doc.layouts.get("Layout1")
    vp = psp.add_viewport(center=(0, 0), size=(10, 10), view_center_point=(0, 0), view_height=10)
    vp.frozen_layers = ["FROZEN-LAYER"]
    return doc


def make_doc_with_anonymous_block() -> Drawing:
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    msp.add_linear_dim(base=(0, 2), p1=(0, 0), p2=(5, 0), dimstyle="Standard").render()
    return doc


def make_doc_with_xref_layer() -> Drawing:
    doc = ezdxf.new("R2018")
    doc.layers.add("XREFNAME|A-WALL")
    return doc


def make_doc_with_wrong_font_style() -> Drawing:
    doc = ezdxf.new("R2018")
    doc.styles.add("MEP-DUCT-TAG", font="arial.ttf")
    doc.modelspace().add_text(
        "DUCT TAG", dxfattribs={"style": "MEP-DUCT-TAG", "height": 2.5, "layer": "0"}
    )
    return doc


def make_doc_with_inline_font_override() -> Drawing:
    doc = ezdxf.new("R2018")
    doc.styles.add("MEP-DUCT-TAG", font="simplex.shx")
    doc.modelspace().add_mtext(
        r"\fArial|b0|i0;OVERRIDE TEXT", dxfattribs={"style": "MEP-DUCT-TAG", "char_height": 2.5, "layer": "0"}
    )
    return doc


def make_doc_with_wrong_text_height() -> Drawing:
    doc = ezdxf.new("R2018")
    doc.styles.add("MEP-DUCT-TAG", font="simplex.shx")
    doc.modelspace().add_text(
        "TOO BIG", dxfattribs={"style": "MEP-DUCT-TAG", "height": 10.0, "layer": "0"}
    )
    return doc


def make_doc_with_scaled_text_in_block() -> Drawing:
    doc = ezdxf.new("R2018")
    doc.styles.add("MEP-DUCT-TAG", font="simplex.shx")
    blk = doc.blocks.new("TagBlock")
    blk.add_text("TAG", dxfattribs={"style": "MEP-DUCT-TAG", "height": 1.0, "layer": "0"})
    doc.modelspace().add_blockref("TagBlock", (0, 0), dxfattribs={"xscale": 2.5, "yscale": 2.5})
    return doc
