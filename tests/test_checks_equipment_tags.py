import ezdxf

from fncsqaqc.checks.base import CheckContext
from fncsqaqc.checks.dwg_equipment_tags import FileTags, _scan_entities, collect, reconcile
from fncsqaqc.dxf.reference_scanner import scan
from fncsqaqc.models import LayerStandard, Severity


class _FakeText:
    def __init__(self, text: str):
        self._text = text

    def dxftype(self) -> str:
        return "TEXT"

    @property
    def dxf(self):
        return {"text": self._text}


class _FakeTable:
    """Duck-typed ACAD_TABLE stand-in -- ezdxf can't construct real
    ACAD_TABLE entities from scratch (read-only compat support), so this
    exercises the same virtual_entities()-decomposition path collect() uses
    without needing a real table in a real DXF file."""

    def __init__(self, cell_texts: list[str]):
        self._cell_texts = cell_texts

    def dxftype(self) -> str:
        return "ACAD_TABLE"

    def virtual_entities(self):
        return [_FakeText(t) for t in self._cell_texts]


def _ctx(relative_path: str, doc) -> CheckContext:
    return CheckContext(
        relative_path=relative_path,
        doc=doc,
        graph=scan(doc),
        layer_standard=LayerStandard(layers=[], text_styles=[]),
    )


def _doc_with_text(layer: str, text: str):
    doc = ezdxf.new()
    doc.layers.add(layer)
    doc.modelspace().add_text(text, dxfattribs={"layer": layer})
    return doc


def test_tag_matched_against_schedule_in_a_different_file():
    # This firm keeps the schedule in its own drawing, separate from the
    # layout drawing that places the tag -- that's the real-world case the
    # per-file version of this check couldn't see.
    layout_doc = _doc_with_text("M-HVAC-EQPM-IDEN", "AHU-01")
    schedule_doc = _doc_with_text("M-HVAC-SCHED", "AHU-01")

    tags_by_file = {
        "layout.dwg": collect(_ctx("layout.dwg", layout_doc)),
        "schedule.dwg": collect(_ctx("schedule.dwg", schedule_doc)),
    }
    results = reconcile(tags_by_file)
    assert results == []


def test_tag_in_drawing_with_no_matching_schedule_entry_anywhere_fails():
    layout_doc = _doc_with_text("M-HVAC-EQPM-IDEN", "AHU-02")
    schedule_doc = _doc_with_text("M-HVAC-SCHED", "AHU-01")

    tags_by_file = {
        "layout.dwg": collect(_ctx("layout.dwg", layout_doc)),
        "schedule.dwg": collect(_ctx("schedule.dwg", schedule_doc)),
    }
    results = reconcile(tags_by_file)
    assert any(
        r.severity == Severity.FAIL and "AHU-02" in r.message and r.file == "layout.dwg" for r in results
    )


def test_acad_table_cells_are_scanned_as_schedule_tags():
    # This firm's real schedules are native AutoCAD table objects, not text
    # on a layer named *SCHED* -- a table is schedule content regardless of
    # what layer it lives on.
    table = _FakeTable(["PUMPS SCHEDULE", "PUMP DESIGNATION", "TWP-01", "TRANSFER WATER PUMP"])
    tags = FileTags()
    _scan_entities([table], tags)
    assert tags.schedule_tags == {"TWP-01"}
    assert tags.drawing_tags == set()


def test_malformed_acad_table_does_not_crash_scan():
    class _BrokenTable:
        def dxftype(self) -> str:
            return "ACAD_TABLE"

        def virtual_entities(self):
            raise RuntimeError("corrupt table data")

    tags = FileTags()
    _scan_entities([_BrokenTable()], tags)
    assert tags.schedule_tags == set()


def test_schedule_tag_never_placed_in_any_drawing_warns():
    layout_doc = _doc_with_text("M-HVAC-EQPM-IDEN", "AHU-01")
    schedule_doc = _doc_with_text("M-HVAC-SCHED", "AHU-01, AHU-02")

    tags_by_file = {
        "layout.dwg": collect(_ctx("layout.dwg", layout_doc)),
        "schedule.dwg": collect(_ctx("schedule.dwg", schedule_doc)),
    }
    results = reconcile(tags_by_file)
    assert any(
        r.severity == Severity.WARN and "AHU-02" in r.message and r.file == "schedule.dwg" for r in results
    )
