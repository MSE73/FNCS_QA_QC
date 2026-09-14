"""First Phase 2 technical-audit check: duct/pipe velocity, computed from a
manually-filled sizing-summary workbook rather than parsed from drawings or
calc sources (see docs/PHASE1_PLAN.md's Phase 2 velocity spec for why).

Not a per-file DXF check -- like folder_completeness, this runs once per
run against two Excel inputs: the per-project sizing summary (SizingRow,
one row per tagged duct/pipe run) and the firm-wide velocity-limit
reference table (VelocityLimit, docs/PROCEDURE.md #15).

Matching a sizing row to a limit is by (Type, System), case-insensitive and
trimmed but otherwise exact -- same strict-matching philosophy as
equipment_tags, so a typo'd System name surfaces as "no limit defined"
rather than silently matching the wrong row.
"""
from __future__ import annotations

import math
import re

from fncsqaqc.models import CheckResult, SizingRow, Severity, VelocityLimit

CHECK_ID = "velocity_check"
CHECK_NAME = "Duct/Pipe Velocity Compliance"

_FOLDER_FILE = "(sizing summary)"
_DUCT_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
_PIPE_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)")


def _parse_area_m2(type_: str, size_text: str) -> float | None:
    """Duct sizes are read as WxH in mm (e.g. "600x300"); pipe sizes are
    read as a bare diameter in mm, tolerating prefixes like "DN"/"Ø"/"mm"
    (e.g. "DN150", "Ø150", "150mm")."""
    type_u = type_.strip().upper()
    text = size_text.strip()

    if type_u == "DUCT":
        match = _DUCT_SIZE_RE.search(text)
        if not match:
            return None
        w_mm, h_mm = float(match.group(1)), float(match.group(2))
        if w_mm <= 0 or h_mm <= 0:
            return None
        return (w_mm * h_mm) / 1_000_000.0

    if type_u == "PIPE":
        match = _PIPE_SIZE_RE.search(text)
        if not match:
            return None
        d_mm = float(match.group(1))
        if d_mm <= 0:
            return None
        radius_m = d_mm / 1000.0 / 2.0
        return math.pi * radius_m * radius_m

    return None


def check(rows: list[SizingRow], limits: list[VelocityLimit]) -> list[CheckResult]:
    limit_by_key = {(limit.type.strip().upper(), limit.system.strip().upper()): limit for limit in limits}

    results: list[CheckResult] = []
    for row in rows:
        key = (row.type.strip().upper(), row.system.strip().upper())
        limit = limit_by_key.get(key)

        if limit is None:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': no velocity limit defined for Type='{row.type}' System='{row.system}'",
                    details="Check spelling against VelocityLimits.xlsx, or the System needs a new row added there.",
                )
            )
            continue

        if not limit.active:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=(
                        f"'{row.tag}': velocity limit for Type='{row.type}' System='{row.system}' "
                        "is defined but marked inactive -- not enforced"
                    ),
                    details=f"Code basis: {limit.code_basis or 'n/a'}. {limit.notes}".strip(),
                )
            )
            continue

        if row.design_flow_ls is None:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': missing or unparseable Design Flow (L/s)",
                )
            )
            continue

        area_m2 = _parse_area_m2(row.type, row.installed_size)
        if area_m2 is None:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': could not parse Installed Size '{row.installed_size}'",
                    details="Ducts: WxH in mm (e.g. 600x300). Pipes: diameter in mm (e.g. DN150, 150mm).",
                )
            )
            continue

        velocity_ms = (row.design_flow_ls / 1000.0) / area_m2

        if limit.min_velocity is not None and velocity_ms < limit.min_velocity:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.FAIL,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': velocity {velocity_ms:.2f} m/s is below the minimum {limit.min_velocity} m/s",
                    details=f"Type={row.type}, System={row.system}, Code basis: {limit.code_basis}",
                )
            )
        elif limit.max_velocity is not None and velocity_ms > limit.max_velocity:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.FAIL,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': velocity {velocity_ms:.2f} m/s exceeds the maximum {limit.max_velocity} m/s",
                    details=f"Type={row.type}, System={row.system}, Code basis: {limit.code_basis}",
                )
            )

    return results
