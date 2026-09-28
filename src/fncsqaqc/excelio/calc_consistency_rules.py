"""Loads the firm's calc internal-consistency ruleset
(CalcConsistencyRules.xlsx). See docs/PROCEDURE.md #23 for how this was
sourced from a real found bug."""
from __future__ import annotations

from pathlib import Path

from fncsqaqc.excelio.common import as_bool, as_float, as_str, read_rows
from fncsqaqc.models import CalcConsistencyRule


def load_calc_consistency_rules(workbook_path: Path) -> list[CalcConsistencyRule]:
    rows = read_rows(
        workbook_path,
        "CalcConsistencyRules",
        required_columns=["Value Label"],
        optional_columns=["Tolerance (%)", "Notes", "Active (Y/N)"],
    )
    return [
        CalcConsistencyRule(
            value_label=as_str(row["Value Label"]),
            tolerance_pct=as_float(row.get("Tolerance (%)")) or 5.0,
            notes=as_str(row.get("Notes")),
            active=as_bool(row.get("Active (Y/N)")),
        )
        for row in rows
        if as_str(row["Value Label"])
    ]
