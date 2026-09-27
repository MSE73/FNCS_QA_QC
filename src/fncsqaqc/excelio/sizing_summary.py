"""Loads the per-project sizing-summary workbook. Velocity, Slope,
EquipmentSizing, and Manholes sheets (docs/PHASE1_PLAN.md's "Phase 2
overall scope" section)."""
from __future__ import annotations

from pathlib import Path

from fncsqaqc.excelio.common import as_float, as_str, read_rows
from fncsqaqc.models import EquipmentSizingRow, ManholeRow, SizingRow, SlopeRow


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


def load_equipment_sizing(workbook_path: Path) -> list[EquipmentSizingRow]:
    rows = read_rows(
        workbook_path,
        "EquipmentSizing",
        required_columns=["Tag", "Parameter", "Required (Calc)", "Installed (Drawing)"],
        optional_columns=["Unit", "Tolerance (%)", "Notes"],
    )
    return [
        EquipmentSizingRow(
            tag=as_str(row["Tag"]),
            parameter=as_str(row["Parameter"]),
            required_value=as_float(row.get("Required (Calc)")),
            installed_value=as_float(row.get("Installed (Drawing)")),
            unit=as_str(row.get("Unit")),
            tolerance_pct=as_float(row.get("Tolerance (%)")) or 0.0,
            notes=as_str(row.get("Notes")),
        )
        for row in rows
        if as_str(row["Tag"])
    ]


def load_manhole_sizing(workbook_path: Path) -> list[ManholeRow]:
    rows = read_rows(
        workbook_path,
        "Manholes",
        required_columns=["Tag", "MH Size (mm)", "Approx Depth (m)"],
        optional_columns=["Notes"],
    )
    return [
        ManholeRow(
            tag=as_str(row["Tag"]),
            mh_size=as_str(row.get("MH Size (mm)")),
            depth_m=as_float(row.get("Approx Depth (m)")),
            notes=as_str(row.get("Notes")),
        )
        for row in rows
        if as_str(row["Tag"])
    ]


def load_slope_sizing(workbook_path: Path) -> list[SlopeRow]:
    rows = read_rows(
        workbook_path,
        "Slope",
        required_columns=[
            "Tag",
            "Installed Size",
            "Upstream Invert (m)",
            "Downstream Invert (m)",
            "Run Length (m)",
        ],
        optional_columns=["Notes"],
    )
    return [
        SlopeRow(
            tag=as_str(row["Tag"]),
            installed_size=as_str(row.get("Installed Size")),
            upstream_invert_m=as_float(row.get("Upstream Invert (m)")),
            downstream_invert_m=as_float(row.get("Downstream Invert (m)")),
            length_m=as_float(row.get("Run Length (m)")),
            notes=as_str(row.get("Notes")),
        )
        for row in rows
        if as_str(row["Tag"])
    ]
