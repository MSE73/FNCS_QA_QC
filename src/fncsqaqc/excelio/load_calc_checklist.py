"""Loads the firm's load-calc completeness checklist
(LoadCalcChecklist.xlsx). See docs/PROCEDURE.md #21 for how this was
sourced from a real manual calc review."""
from __future__ import annotations

from pathlib import Path

from fncsqaqc.excelio.common import as_bool, as_str, read_rows
from fncsqaqc.models import LoadCalcChecklistItem


def load_load_calc_checklist(workbook_path: Path) -> list[LoadCalcChecklistItem]:
    rows = read_rows(
        workbook_path,
        "LoadCalcChecklist",
        required_columns=["Category", "Item", "Keywords"],
        optional_columns=["Required (Y/N)", "Notes", "Active (Y/N)"],
    )
    return [
        LoadCalcChecklistItem(
            category=as_str(row["Category"]),
            item=as_str(row["Item"]),
            keywords=as_str(row["Keywords"]),
            required=as_bool(row.get("Required (Y/N)")),
            notes=as_str(row.get("Notes")),
            active=as_bool(row.get("Active (Y/N)")),
        )
        for row in rows
        if as_str(row["Item"])
    ]
