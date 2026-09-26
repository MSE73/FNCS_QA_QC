"""Loads the firm's drainage minimum-slope reference table
(DrainageSlopeLimits.xlsx). See docs/PROCEDURE.md #18 for how the values
were sourced."""
from __future__ import annotations

from pathlib import Path

from fncsqaqc.excelio.common import as_bool, as_float, as_str, read_rows
from fncsqaqc.models import SlopeLimit


def load_drainage_slope_limits(workbook_path: Path) -> list[SlopeLimit]:
    rows = read_rows(
        workbook_path,
        "DrainageSlopeLimits",
        required_columns=["Min Diameter (mm)", "Min Slope (%)"],
        optional_columns=["Max Diameter (mm)", "Code Basis", "Notes", "Active (Y/N)"],
    )
    return [
        SlopeLimit(
            min_diameter_mm=as_float(row["Min Diameter (mm)"]) or 0.0,
            max_diameter_mm=as_float(row.get("Max Diameter (mm)")),
            min_slope_pct=as_float(row["Min Slope (%)"]) or 0.0,
            code_basis=as_str(row.get("Code Basis")),
            notes=as_str(row.get("Notes")),
            active=as_bool(row.get("Active (Y/N)")),
        )
        for row in rows
        if as_float(row["Min Diameter (mm)"]) is not None and as_float(row["Min Slope (%)"]) is not None
    ]
