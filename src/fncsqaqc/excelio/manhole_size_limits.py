"""Loads the firm's manhole/inspection-chamber minimum-size reference table
(ManholeSizeLimits.xlsx). See docs/PROCEDURE.md #20 for how the values were
sourced."""
from __future__ import annotations

from pathlib import Path

from fncsqaqc.excelio.common import as_bool, as_float, as_str, read_rows
from fncsqaqc.models import ManholeLimit


def load_manhole_size_limits(workbook_path: Path) -> list[ManholeLimit]:
    rows = read_rows(
        workbook_path,
        "ManholeSizeLimits",
        required_columns=["Min Depth (m)", "Min Size Round (mm)", "Min Size Square (mm)"],
        optional_columns=["Max Depth (m)", "Code Basis", "Notes", "Active (Y/N)"],
    )
    return [
        ManholeLimit(
            min_depth_m=as_float(row["Min Depth (m)"]) or 0.0,
            max_depth_m=as_float(row.get("Max Depth (m)")),
            min_size_round_mm=as_float(row["Min Size Round (mm)"]) or 0.0,
            min_size_square_mm=as_float(row["Min Size Square (mm)"]) or 0.0,
            code_basis=as_str(row.get("Code Basis")),
            notes=as_str(row.get("Notes")),
            active=as_bool(row.get("Active (Y/N)")),
        )
        for row in rows
        if as_float(row["Min Depth (m)"]) is not None
    ]
