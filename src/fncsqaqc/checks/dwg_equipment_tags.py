"""Opt-in heuristic check: every equipment tag placed in the drawing should
also appear in an equipment schedule, and vice versa.

Tags today are plain TEXT/MTEXT near equipment (no attributed-block standard
exists yet), so this is necessarily a heuristic, not an exact check:
  - "Tag" candidates = TEXT/MTEXT anywhere matching TAG_PATTERN (e.g. AHU-01).
  - "Schedule" candidates = the same pattern, but found on a layer whose name
    contains "SCHED" (the firm's usual convention for schedule tables/text).
Disabled by default (--enable-equipment-tag-check to turn on) since there is
no strict current standard to validate against with full confidence.
"""
from __future__ import annotations

import re

from fncsqaqc.checks.base import CheckContext
from fncsqaqc.models import CheckResult, Severity

CHECK_ID = "equipment_tags"
CHECK_NAME = "Equipment Tagging / Schedule Cross-check"

TAG_PATTERN = re.compile(r"^[A-Z]{1,6}-\d{1,4}[A-Z]?$")
SCHEDULE_LAYER_HINT = "SCHED"


def _candidate_tags(text: str) -> set[str]:
    return {
        token.strip().upper()
        for token in re.split(r"[\s,;]+", text)
        if TAG_PATTERN.match(token.strip().upper())
    }


def run(ctx: CheckContext) -> list[CheckResult]:
    drawing_tags: set[str] = set()
    schedule_tags: set[str] = set()

    for space in [ctx.doc.modelspace()] + [
        ctx.doc.layouts.get(n) for n in ctx.doc.layout_names() if n != "Model"
    ]:
        for entity in space:
            dxftype = entity.dxftype()
            if dxftype not in ("TEXT", "MTEXT"):
                continue
            text = entity.plain_text() if dxftype == "MTEXT" else entity.dxf.get("text", "")
            tags = _candidate_tags(text)
            if not tags:
                continue
            layer = (entity.dxf.get("layer", "") or "").upper()
            if SCHEDULE_LAYER_HINT in layer:
                schedule_tags |= tags
            else:
                drawing_tags |= tags

    results: list[CheckResult] = []
    for tag in sorted(drawing_tags - schedule_tags):
        results.append(
            CheckResult(
                check_id=CHECK_ID,
                severity=Severity.FAIL,
                file=ctx.relative_path,
                message=f"Equipment tag '{tag}' found in drawing but not in the equipment schedule",
            )
        )
    for tag in sorted(schedule_tags - drawing_tags):
        results.append(
            CheckResult(
                check_id=CHECK_ID,
                severity=Severity.WARN,
                file=ctx.relative_path,
                message=f"Equipment tag '{tag}' is in the schedule but not found tagged in the drawing",
            )
        )

    return results
