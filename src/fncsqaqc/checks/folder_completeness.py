"""Folder-level checks: does the submission folder contain everything the
deliverables checklist and drawings list require? Runs once per run, not
per-file."""
from __future__ import annotations

import fnmatch
import re

from fncsqaqc.models import (
    CheckResult,
    DeliverableItem,
    DiscoveredFile,
    DrawingListItem,
    Severity,
)

DELIVERABLES_CHECK_ID = "folder_deliverables"
DRAWINGS_CHECK_ID = "drawings_list"


def _matches(pattern: str, relative_path: str) -> bool:
    pattern = pattern.strip()
    if not pattern:
        return False
    normalized = relative_path.replace("\\", "/")
    if pattern.startswith("re:"):
        return re.search(pattern[3:], normalized, re.IGNORECASE) is not None
    return fnmatch.fnmatch(normalized.lower(), pattern.lower())


def check_deliverables(
    items: list[DeliverableItem], files: list[DiscoveredFile]
) -> list[CheckResult]:
    results: list[CheckResult] = []
    paths = [str(f.relative_path) for f in files]

    for item in items:
        matched = any(_matches(item.expected_pattern, p) for p in paths)
        if not matched and item.required:
            results.append(
                CheckResult(
                    check_id=DELIVERABLES_CHECK_ID,
                    severity=Severity.FAIL,
                    file="(folder)",
                    message=f"Missing required deliverable: {item.category} / {item.item}",
                    details=f"Expected pattern: {item.expected_pattern}",
                )
            )
        elif not matched:
            results.append(
                CheckResult(
                    check_id=DELIVERABLES_CHECK_ID,
                    severity=Severity.WARN,
                    file="(folder)",
                    message=f"Optional deliverable not found: {item.category} / {item.item}",
                    details=f"Expected pattern: {item.expected_pattern}",
                )
            )

    return results


def check_drawings(
    items: list[DrawingListItem],
    files: list[DiscoveredFile],
    layout_names_by_file: dict[str, list[str]] | None = None,
) -> list[CheckResult]:
    """A required drawing counts as found if either its own filename or a
    paperspace layout tab inside any drawing file matches the expected
    pattern -- this firm routinely bundles several sheet numbers as separate
    layout tabs in one DWG (e.g. one file per system, one tab per floor)."""
    results: list[CheckResult] = []
    drawing_files = [
        f for f in files if f.kind.value in ("DWG", "DXF")
    ]
    paths = [str(f.relative_path) for f in drawing_files]
    layout_names_by_file = layout_names_by_file or {}
    matched_paths: set[str] = set()

    for item in items:
        pattern = item.expected_pattern.strip() or f"*{item.drawing_no}*"
        matches = [p for p in paths if _matches(pattern, p)]
        layout_matches = [
            p
            for p, layouts in layout_names_by_file.items()
            if any(_matches(pattern, layout) for layout in layouts)
        ]
        if matches or layout_matches:
            matched_paths.update(matches)
            matched_paths.update(layout_matches)
        elif item.required:
            results.append(
                CheckResult(
                    check_id=DRAWINGS_CHECK_ID,
                    severity=Severity.FAIL,
                    file="(folder)",
                    message=f"Missing required drawing: {item.drawing_no} - {item.title}",
                    details=f"Expected pattern: {pattern}",
                )
            )
        else:
            results.append(
                CheckResult(
                    check_id=DRAWINGS_CHECK_ID,
                    severity=Severity.WARN,
                    file="(folder)",
                    message=f"Optional drawing not found: {item.drawing_no} - {item.title}",
                    details=f"Expected pattern: {pattern}",
                )
            )

    for path in paths:
        if path not in matched_paths:
            results.append(
                CheckResult(
                    check_id=DRAWINGS_CHECK_ID,
                    severity=Severity.WARN,
                    file=path,
                    message="Drawing file does not match any entry in the drawings list",
                    details="Unexpected/unlisted drawing",
                )
            )

    return results
