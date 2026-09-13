"""Opt-in heuristic check: every equipment tag placed in the drawing should
also appear in an equipment schedule, and vice versa.

Tags today are plain TEXT/MTEXT near equipment (no attributed-block standard
exists yet), so this is necessarily a heuristic, not an exact check:
  - "Tag" candidates = TEXT/MTEXT anywhere matching TAG_PATTERN (e.g. AHU-01).
  - "Schedule" candidates = the same pattern, found either on a layer whose
    name contains "SCHED", or inside the cells of an ACAD_TABLE entity --
    this firm's actual schedules are native AutoCAD tables, not text on a
    conventionally-named layer, so a table is always schedule content
    regardless of what layer it sits on. ezdxf can't read ACAD_TABLE cells
    directly; `virtual_entities()` decomposes the table into the TEXT/MTEXT
    it's actually drawn from, which is what's scanned here.

Reconciliation is project-wide, not per-file: this firm keeps the equipment
schedule in its own drawing (e.g. P0801 SCHEDULE.dwg), separate from the
layout drawings that place the tags, so a tag and its schedule entry are
essentially never in the same file. `collect()` runs per-file during the
main scan (cheap -- reuses the already-loaded doc); `reconcile()` then
compares each file's tags against the tag/schedule sets from every file in
the run. Disabled by default (--enable-equipment-tag-check to turn on)
since there is no strict current standard to validate against with full
confidence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from fncsqaqc.checks.base import CheckContext
from fncsqaqc.models import CheckResult, Severity

CHECK_ID = "equipment_tags"
CHECK_NAME = "Equipment Tagging / Schedule Cross-check"

TAG_PATTERN = re.compile(r"^[A-Z]{1,6}-\d{1,4}[A-Z]?$")
SCHEDULE_LAYER_HINT = "SCHED"


@dataclass
class FileTags:
    drawing_tags: set[str] = field(default_factory=set)
    schedule_tags: set[str] = field(default_factory=set)


def _candidate_tags(text: str) -> set[str]:
    return {
        token.strip().upper()
        for token in re.split(r"[\s,;]+", text)
        if TAG_PATTERN.match(token.strip().upper())
    }


def _text_of(entity) -> str:
    dxftype = entity.dxftype()
    if dxftype == "MTEXT":
        return entity.plain_text()
    if dxftype == "TEXT":
        return entity.dxf.get("text", "")
    return ""


def _scan_entities(entities, tags: FileTags) -> None:
    for entity in entities:
        dxftype = entity.dxftype()

        if dxftype == "ACAD_TABLE":
            try:
                cell_entities = entity.virtual_entities()
            except Exception:  # noqa: BLE001 - a malformed table must not abort the scan
                continue
            for cell_entity in cell_entities:
                tags.schedule_tags |= _candidate_tags(_text_of(cell_entity))
            continue

        if dxftype not in ("TEXT", "MTEXT"):
            continue
        found = _candidate_tags(_text_of(entity))
        if not found:
            continue
        layer = (entity.dxf.get("layer", "") or "").upper()
        if SCHEDULE_LAYER_HINT in layer:
            tags.schedule_tags |= found
        else:
            tags.drawing_tags |= found


def collect(ctx: CheckContext) -> FileTags:
    tags = FileTags()

    for space in [ctx.doc.modelspace()] + [
        ctx.doc.layouts.get(n) for n in ctx.doc.layout_names() if n != "Model"
    ]:
        _scan_entities(space, tags)

    return tags


def reconcile(tags_by_file: dict[str, FileTags]) -> list[CheckResult]:
    all_schedule_tags: set[str] = set()
    all_drawing_tags: set[str] = set()
    for tags in tags_by_file.values():
        all_schedule_tags |= tags.schedule_tags
        all_drawing_tags |= tags.drawing_tags

    results: list[CheckResult] = []
    for relative_path, tags in tags_by_file.items():
        for tag in sorted(tags.drawing_tags - all_schedule_tags):
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.FAIL,
                    file=relative_path,
                    message=f"Equipment tag '{tag}' found in drawing but not in the equipment schedule",
                )
            )
        for tag in sorted(tags.schedule_tags - all_drawing_tags):
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=relative_path,
                    message=f"Equipment tag '{tag}' is in the schedule but not found tagged in any drawing",
                )
            )

    return results
