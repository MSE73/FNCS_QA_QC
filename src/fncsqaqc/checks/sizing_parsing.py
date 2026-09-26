"""Shared free-text size parsing for the sizing-summary-workbook checks
(velocity, slope, ...). Pipe sizes are read as a bare diameter in mm,
tolerating prefixes/suffixes like "DN"/"O/o slash"/"mm" (e.g. "DN150",
"O150", "150mm")."""
from __future__ import annotations

import re

_PIPE_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)")


def parse_pipe_diameter_mm(size_text: str) -> float | None:
    match = _PIPE_SIZE_RE.search(size_text.strip())
    if not match:
        return None
    d_mm = float(match.group(1))
    if d_mm <= 0:
        return None
    return d_mm
