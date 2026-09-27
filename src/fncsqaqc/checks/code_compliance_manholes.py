"""Fourth Phase 2 technical-audit sub-check: manhole/inspection-chamber
minimum sizing, computed from a manually-filled sizing-summary workbook --
same mechanism and philosophy as code_compliance_slope.py, just matching a
chamber's plan size against a code-mandated minimum for its depth instead
of matching a pipe's slope against a minimum grade.

Not a per-file DXF check -- runs once per run against two Excel inputs: the
per-project sizing summary (ManholeRow, one row per manhole/inspection
chamber, mirroring this firm's own manhole-schedule columns) and the
firm-wide minimum-size reference table (ManholeLimit, docs/PROCEDURE.md
#20).

Matching a sizing row to a limit is a range lookup by chamber depth (m) --
UK Approved Document H Table 11 (the code basis used here) keys minimum
inspection-chamber size off depth alone, not connecting pipe diameter.
"""
from __future__ import annotations

from fncsqaqc.checks.sizing_parsing import parse_manhole_size
from fncsqaqc.models import CheckResult, ManholeLimit, ManholeRow, Severity

CHECK_ID = "manhole_check"
CHECK_NAME = "Manhole / Inspection Chamber Minimum Size Compliance"

_FOLDER_FILE = "(sizing summary)"


def _find_limit(depth_m: float, limits: list[ManholeLimit]) -> ManholeLimit | None:
    # Both bounds are inclusive, matching UK Approved Document H's own
    # "not exceeding X" / "exceeding X but not exceeding Y" phrasing --
    # a depth landing exactly on a tier boundary belongs to the SHALLOWER
    # tier. Reference-table rows must be listed shallowest-first so the
    # first (and only intended) match at a shared boundary wins.
    for limit in limits:
        if depth_m < limit.min_depth_m:
            continue
        if limit.max_depth_m is not None and depth_m > limit.max_depth_m:
            continue
        return limit
    return None


def check(rows: list[ManholeRow], limits: list[ManholeLimit]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for row in rows:
        parsed = parse_manhole_size(row.mh_size)
        if parsed is None:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': could not parse MH Size '{row.mh_size}'",
                    details="Square/rect in mm (e.g. 600X600) or round diameter in mm (e.g. O900, 900mm).",
                )
            )
            continue
        shape, min_dimension_mm = parsed

        if row.depth_m is None:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': missing Approx Depth (m)",
                )
            )
            continue

        if row.depth_m <= 0:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': depth must be greater than zero (got {row.depth_m})",
                )
            )
            continue

        limit = _find_limit(row.depth_m, limits)
        if limit is None:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': no minimum-size limit defined for depth {row.depth_m:g}m",
                    details="Check ManholeSizeLimits.xlsx -- the depth may fall outside every defined range.",
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
                        f"'{row.tag}': minimum-size limit for depth {row.depth_m:g}m is defined but "
                        "marked inactive -- not enforced"
                    ),
                    details=f"Code basis: {limit.code_basis or 'n/a'}. {limit.notes}".strip(),
                )
            )
            continue

        min_required_mm = limit.min_size_round_mm if shape == "round" else limit.min_size_square_mm
        if min_dimension_mm < min_required_mm:
            shape_label = "diameter" if shape == "round" else "minimum side"
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.FAIL,
                    file=_FOLDER_FILE,
                    message=(
                        f"'{row.tag}': {shape} chamber {shape_label} {min_dimension_mm:g}mm is below the "
                        f"minimum {min_required_mm:g}mm for {row.depth_m:g}m depth"
                    ),
                    details=f"Code basis: {limit.code_basis}",
                )
            )

    return results
