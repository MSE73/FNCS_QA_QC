"""Loads the per-project deliverables checklist workbook."""
from __future__ import annotations

from pathlib import Path

from fncsqaqc.excelio.common import as_bool, as_str, read_rows
from fncsqaqc.models import DeliverableItem

SHEET_NAME = "Deliverables"


def load_deliverables(workbook_path: Path) -> list[DeliverableItem]:
    rows = read_rows(
        workbook_path,
        SHEET_NAME,
        required_columns=["Category", "Item", "Expected Pattern"],
        optional_columns=["Required (Y/N)", "Discipline", "Notes"],
    )
    return [
        DeliverableItem(
            category=as_str(row["Category"]),
            item=as_str(row["Item"]),
            expected_pattern=as_str(row["Expected Pattern"]),
            required=as_bool(row.get("Required (Y/N)")),
            discipline=as_str(row.get("Discipline")),
            notes=as_str(row.get("Notes")),
        )
        for row in rows
        if as_str(row["Item"])
    ]
