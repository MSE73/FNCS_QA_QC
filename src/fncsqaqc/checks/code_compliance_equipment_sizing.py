"""Third Phase 2 technical-audit sub-check: equipment sizing vs. calc --
"does the installed/selected unit meet the calc's required value," not "is
the flow velocity in range" (that's velocity_check) or "is the grade steep
enough" (that's slope_check). See docs/PHASE1_PLAN.md's Phase 2 overall
scope, sub-check #3.

Unlike velocity/slope there is no firm-wide reference table -- this is a
direct calc-vs-drawing comparison (a single manually-filled sizing-summary
sheet), not a check against a published code limit, so it needs only one
Excel input.

Not a per-file DXF check -- runs once per run against the per-project
sizing summary (EquipmentSizingRow, one row per tagged parameter being
compared, e.g. a pump's Flow (L/s) or a boiler's Capacity (kW)).
"""
from __future__ import annotations

from fncsqaqc.models import CheckResult, EquipmentSizingRow, Severity

CHECK_ID = "equipment_sizing_check"
CHECK_NAME = "Equipment Sizing vs. Calc"

_FOLDER_FILE = "(sizing summary)"


def check(rows: list[EquipmentSizingRow]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for row in rows:
        label = f"'{row.tag}' {row.parameter}".strip()

        if row.required_value is None:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"{label}: missing or unparseable Required (Calc) value",
                )
            )
            continue

        if row.installed_value is None:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"{label}: missing or unparseable Installed (Drawing) value",
                )
            )
            continue

        threshold = row.required_value * (1.0 - row.tolerance_pct / 100.0)
        if row.installed_value < threshold:
            unit = f" {row.unit}".rstrip()
            tolerance_note = f" (tolerance {row.tolerance_pct:g}%)" if row.tolerance_pct else ""
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.FAIL,
                    file=_FOLDER_FILE,
                    message=(
                        f"{label}: installed {row.installed_value:g}{unit} is undersized vs. "
                        f"required {row.required_value:g}{unit}{tolerance_note}"
                    ),
                )
            )

    return results
