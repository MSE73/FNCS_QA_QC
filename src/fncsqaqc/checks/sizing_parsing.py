"""Shared free-text size parsing for the sizing-summary-workbook checks
(velocity, slope, manholes, ...). Pipe sizes are read as a bare diameter in
mm, tolerating prefixes/suffixes like "DN"/"O/o slash"/"mm" (e.g. "DN150",
"O150", "150mm")."""
from __future__ import annotations

import re

_PIPE_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)")
_RECT_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)")


def parse_pipe_diameter_mm(size_text: str) -> float | None:
    match = _PIPE_SIZE_RE.search(size_text.strip())
    if not match:
        return None
    d_mm = float(match.group(1))
    if d_mm <= 0:
        return None
    return d_mm


def parse_manhole_size(size_text: str) -> tuple[str, float] | None:
    """Manhole/inspection-chamber size, e.g. "600X600" (square, chamber's
    minimum plan dimension is the smaller side) or "900"/"O900"/"D900mm"
    (round, minimum plan dimension is the diameter). Returns
    (shape, min_dimension_mm) where shape is "square" or "round", or None
    if unparseable. A bare number with no "AxB" pattern is treated as
    round, since this firm records round chambers as a single diameter
    figure (the ezdxf-decoded AutoCAD diameter symbol %%C, or DIA/D/O)."""
    text = size_text.strip()
    rect_match = _RECT_SIZE_RE.search(text)
    if rect_match:
        a, b = float(rect_match.group(1)), float(rect_match.group(2))
        min_side = min(a, b)
        if min_side <= 0:
            return None
        return "square", min_side

    diameter_mm = parse_pipe_diameter_mm(text)
    if diameter_mm is None:
        return None
    return "round", diameter_mm
