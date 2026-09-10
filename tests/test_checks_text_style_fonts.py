from fncsqaqc.checks.base import CheckContext
from fncsqaqc.checks.dwg_text_style_fonts import run
from fncsqaqc.dxf.reference_scanner import scan
from fncsqaqc.models import LayerStandard, Severity, TextStyleRule

from tests import factories


def _ctx(doc, layer_standard):
    return CheckContext(relative_path="test.dxf", doc=doc, graph=scan(doc), layer_standard=layer_standard)


def test_correct_font_passes():
    doc = factories.make_basic_doc()
    standard = LayerStandard(
        layers=[], text_styles=[TextStyleRule(style_name="MEP-DUCT-TAG", expected_font="simplex.shx")]
    )
    results = run(_ctx(doc, standard))
    assert results == []


def test_wrong_font_fails():
    doc = factories.make_doc_with_wrong_font_style()
    standard = LayerStandard(
        layers=[], text_styles=[TextStyleRule(style_name="MEP-DUCT-TAG", expected_font="simplex.shx")]
    )
    results = run(_ctx(doc, standard))
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL
    assert "arial.ttf" in results[0].details


def test_inline_font_override_is_warned():
    doc = factories.make_doc_with_inline_font_override()
    standard = LayerStandard(
        layers=[], text_styles=[TextStyleRule(style_name="MEP-DUCT-TAG", expected_font="simplex.shx")]
    )
    results = run(_ctx(doc, standard))
    override_result = next(r for r in results if "inline font override" in r.message)
    assert override_result.severity == Severity.WARN
