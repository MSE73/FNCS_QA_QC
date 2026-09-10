"""Loads the per-project expected drawings list workbook."""
from __future__ import annotations

from pathlib import Path

from fncsqaqc.excelio.common import as_bool, as_str, read_rows
from fncsqaqc.models import DrawingListItem

SHEET_NAME = "Drawings"


def load_drawings_list(workbook_path: Path) -> list[DrawingListItem]:
    rows = read_rows(
        workbook_path,
        SHEET_NAME,
        required_columns=["Drawing No.", "Title"],
        optional_columns=["Discipline", "Expected Filename Pattern", "Required (Y/N)", "Notes"],
    )
    return [
        DrawingListItem(
            drawing_no=as_str(row["Drawing No."]),
            title=as_str(row["Title"]),
            discipline=as_str(row.get("Discipline")),
            expected_pattern=as_str(row.get("Expected Filename Pattern")),
            required=as_bool(row.get("Required (Y/N)")),
            notes=as_str(row.get("Notes")),
        )
        for row in rows
        if as_str(row["Drawing No."])
    ]
