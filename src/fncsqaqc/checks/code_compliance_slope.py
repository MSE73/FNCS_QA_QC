"""Second Phase 2 technical-audit sub-check: gravity-drainage minimum slope,
computed from a manually-filled sizing-summary workbook -- same mechanism
and philosophy as code_compliance_velocity.py (see docs/PHASE1_PLAN.md's
Phase 2 overall scope, sub-check #2), just measuring installed *slope*
(invert drop over run length) against a code-mandated minimum grade instead
of computing velocity via Manning's equation.

Not a per-file DXF check -- runs once per run against two Excel inputs: the
per-project sizing summary (SlopeRow, one row per pipe run between two
points with known invert levels) and the firm-wide minimum-slope reference
table (SlopeLimit, docs/PROCEDURE.md #18).

Matching a sizing row to a limit is a range lookup by installed pipe
diameter (mm) -- unlike velocity's exact (Type, System) match, minimum
grade under IPC Table 704.1 depends only on diameter, not on which system
the pipe serves.
"""
from __future__ import annotations

from fncsqaqc.checks.sizing_parsing import parse_pipe_diameter_mm
from fncsqaqc.models import CheckResult, SlopeLimit, SlopeRow, Severity

CHECK_ID = "slope_check"
CHECK_NAME = "Drainage Minimum Slope Compliance"

_FOLDER_FILE = "(sizing summary)"


def _find_limit(diameter_mm: float, limits: list[SlopeLimit]) -> SlopeLimit | None:
    for limit in limits:
        if diameter_mm < limit.min_diameter_mm:
            continue
        if limit.max_diameter_mm is not None and diameter_mm > limit.max_diameter_mm:
            continue
        return limit
    return None


def check(rows: list[SlopeRow], limits: list[SlopeLimit]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for row in rows:
        diameter_mm = parse_pipe_diameter_mm(row.installed_size)
        if diameter_mm is None:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': could not parse Installed Size '{row.installed_size}'",
                    details="Pipe diameter in mm (e.g. DN150, Ø150, 150mm).",
                )
            )
            continue

        if row.upstream_invert_m is None or row.downstream_invert_m is None or row.length_m is None:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': missing or unparseable invert level(s) or run length",
                )
            )
            continue

        if row.length_m <= 0:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': run length must be greater than zero (got {row.length_m})",
                )
            )
            continue

        drop_m = row.upstream_invert_m - row.downstream_invert_m
        if drop_m < 0:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.FAIL,
                    file=_FOLDER_FILE,
                    message=(
                        f"'{row.tag}': downstream invert ({row.downstream_invert_m} m) is higher than "
                        f"upstream ({row.upstream_invert_m} m) -- pipe runs uphill"
                    ),
                )
            )
            continue

        limit = _find_limit(diameter_mm, limits)
        if limit is None:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=_FOLDER_FILE,
                    message=f"'{row.tag}': no minimum-slope limit defined for diameter {diameter_mm:g}mm",
                    details="Check DrainageSlopeLimits.xlsx -- the diameter may fall outside every defined range.",
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
                        f"'{row.tag}': minimum-slope limit for diameter {diameter_mm:g}mm is defined but "
                        "marked inactive -- not enforced"
                    ),
                    details=f"Code basis: {limit.code_basis or 'n/a'}. {limit.notes}".strip(),
                )
            )
            continue

        slope_pct = (drop_m / row.length_m) * 100.0
        if slope_pct < limit.min_slope_pct:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.FAIL,
                    file=_FOLDER_FILE,
                    message=(
                        f"'{row.tag}': slope {slope_pct:.2f}% is below the minimum "
                        f"{limit.min_slope_pct:.2f}% for {diameter_mm:g}mm pipe"
                    ),
                    details=f"Code basis: {limit.code_basis}",
                )
            )

    return results
