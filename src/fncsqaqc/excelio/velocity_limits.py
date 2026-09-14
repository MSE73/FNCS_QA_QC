"""Loads the firm's velocity-limit reference table (VelocityLimits.xlsx).
See docs/PROCEDURE.md #15 for how the values were sourced."""
from __future__ import annotations

from pathlib import Path

from fncsqaqc.excelio.common import as_bool, as_float, as_str, read_rows
from fncsqaqc.models import VelocityLimit


def load_velocity_limits(workbook_path: Path) -> list[VelocityLimit]:
    rows = read_rows(
        workbook_path,
        "VelocityLimits",
        required_columns=["Type (Duct/Pipe)", "System"],
        optional_columns=[
            "Min Velocity (m/s)",
            "Max Velocity (m/s)",
            "Code Basis",
            "Notes",
            "Active (Y/N)",
        ],
    )
    return [
        VelocityLimit(
            type=as_str(row["Type (Duct/Pipe)"]),
            system=as_str(row["System"]),
            min_velocity=as_float(row.get("Min Velocity (m/s)")),
            max_velocity=as_float(row.get("Max Velocity (m/s)")),
            code_basis=as_str(row.get("Code Basis")),
            notes=as_str(row.get("Notes")),
            active=as_bool(row.get("Active (Y/N)")),
        )
        for row in rows
        if as_str(row["Type (Duct/Pipe)"]) and as_str(row["System"])
    ]
