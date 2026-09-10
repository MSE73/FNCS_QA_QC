"""Checks rendered TEXT/MTEXT heights (world-space, accounting for block
insert scale) against the expected height per text style, with a tolerance.

Phase 1 simplification: only fixed-height-per-style is supported. A
scale-aware multiplier (ScaleMultipliers sheet) is intentionally deferred --
reliably detecting "drawing scale" without a firm title-block convention
isn't reliable enough to build on yet.
"""
from __future__ import annotations

from collections import defaultdict

from fncsqaqc.checks.base import CheckContext
from fncsqaqc.dxf.rendered_entities import iter_rendered_text
from fncsqaqc.models import CheckResult, Severity

CHECK_ID = "text_heights"
CHECK_NAME = "Text Height Compliance"


def run(ctx: CheckContext) -> list[CheckResult]:
    style_rules = ctx.layer_standard.style_by_name()
    mismatches: dict[tuple[str, float], int] = defaultdict(int)

    for rendered in iter_rendered_text(ctx.doc):
        if rendered.height is None or not rendered.style:
            continue
        rule = style_rules.get(rendered.style.strip().upper())
        if rule is None or rule.expected_height is None:
            continue
        if rule.scales_with_drawing:
            continue  # not yet supported, see module docstring

        tolerance = rule.height_tolerance_pct / 100.0
        low = rule.expected_height * (1 - tolerance)
        high = rule.expected_height * (1 + tolerance)
        if not (low <= rendered.height <= high):
            mismatches[(rendered.style, round(rendered.height, 4))] += 1

    results: list[CheckResult] = []
    for (style_name, actual_height), count in sorted(mismatches.items()):
        expected = style_rules[style_name.strip().upper()].expected_height
        occurrence_note = f" ({count} occurrences)" if count > 1 else ""
        results.append(
            CheckResult(
                check_id=CHECK_ID,
                severity=Severity.FAIL,
                file=ctx.relative_path,
                message=f"Text using style '{style_name}' has the wrong height{occurrence_note}",
                details=f"Expected {expected}, found {actual_height}",
                occurrences=count,
            )
        )

    return results
