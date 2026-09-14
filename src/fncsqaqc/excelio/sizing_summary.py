"""Loads the per-project sizing-summary workbook. Only the Velocity sheet
exists so far -- Slope, EquipmentSizing, and Manholes sheets get added to
this same file as their checks are built (docs/PHASE1_PLAN.md's "Phase 2
overall scope" section)."""
from __future__ import annotations

from pathlib import Path

from fncsqaqc.excelio.common import as_float, as_str, read_rows
from fncsqaqc.models import SizingRow


def load_velocity_sizing(workbook_path: Path) -> list[SizingRow]:
    rows = read_rows(
        workbook_path,
        "Velocity",
        required_columns=["Tag", "Type (Duct/Pipe)", "System", "Design Flow (L/s)", "Installed Size"],
        optional_columns=["Notes"],
    )
    return [
        SizingRow(
            tag=as_str(row["Tag"]),
            type=as_str(row["Type (Duct/Pipe)"]),
            system=as_str(row["System"]),
            design_flow_ls=as_float(row.get("Design Flow (L/s)")),
            installed_size=as_str(row.get("Installed Size")),
            notes=as_str(row.get("Notes")),
        )
        for row in rows
        if as_str(row["Tag"])
    ]
