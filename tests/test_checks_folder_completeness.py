from pathlib import Path

from fncsqaqc.checks.folder_completeness import check_deliverables, check_drawings
from fncsqaqc.models import DeliverableItem, DiscoveredFile, DrawingListItem, FileKind, Severity


def _file(rel: str, kind: FileKind = FileKind.PDF) -> DiscoveredFile:
    return DiscoveredFile(relative_path=Path(rel), absolute_path=Path("/x") / rel, kind=kind, size=1, mtime_ns=1)


def test_missing_required_deliverable_fails():
    items = [DeliverableItem(category="Calcs", item="HVAC Load", expected_pattern="Calculations/*.pdf")]
    files = [_file("Drawings/D-101.dwg", FileKind.DWG)]
    results = check_deliverables(items, files)
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL


def test_present_deliverable_passes():
    items = [DeliverableItem(category="Calcs", item="HVAC Load", expected_pattern="Calculations/*.pdf")]
    files = [_file("Calculations/hvac_load.pdf")]
    results = check_deliverables(items, files)
    assert results == []


def test_optional_missing_deliverable_warns():
    items = [
        DeliverableItem(category="Preambles", item="Preamble", expected_pattern="Preambles/*.docx", required=False)
    ]
    results = check_deliverables(items, [])
    assert len(results) == 1
    assert results[0].severity == Severity.WARN


def test_missing_required_drawing_fails():
    items = [DrawingListItem(drawing_no="M-101", title="HVAC Layout")]
    files = [_file("Drawings/E-101.dwg", FileKind.DWG)]
    results = check_drawings(items, files)
    assert any(r.severity == Severity.FAIL and "M-101" in r.message for r in results)


def test_unexpected_drawing_is_warned():
    items = [DrawingListItem(drawing_no="M-101", title="HVAC Layout")]
    files = [_file("Drawings/M-101.dwg", FileKind.DWG), _file("Drawings/WIP-SCRATCH.dwg", FileKind.DWG)]
    results = check_drawings(items, files)
    assert any("does not match any entry" in r.message for r in results)
    assert not any(r.severity.value == "FAIL" for r in results)
