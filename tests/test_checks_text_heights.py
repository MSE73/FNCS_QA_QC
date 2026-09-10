from fncsqaqc.checks.base import CheckContext
from fncsqaqc.checks.dwg_text_heights import run
from fncsqaqc.dxf.reference_scanner import scan
from fncsqaqc.models import LayerStandard, Severity, TextStyleRule

from tests import factories


def _ctx(doc, layer_standard):
    return CheckContext(relative_path="test.dxf", doc=doc, graph=scan(doc), layer_standard=layer_standard)


def test_correct_height_passes():
    doc = factories.make_doc_with_wrong_font_style()  # height 2.5, style MEP-DUCT-TAG
    standard = LayerStandard(
        layers=[],
        text_styles=[TextStyleRule(style_name="MEP-DUCT-TAG", expected_height=2.5, height_tolerance_pct=5.0)],
    )
    results = run(_ctx(doc, standard))
    assert results == []


def test_wrong_height_fails():
    doc = factories.make_doc_with_wrong_text_height()  # height 10.0
    standard = LayerStandard(
        layers=[],
        text_styles=[TextStyleRule(style_name="MEP-DUCT-TAG", expected_height=2.5, height_tolerance_pct=5.0)],
    )
    results = run(_ctx(doc, standard))
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL


def test_scaled_text_in_block_uses_world_space_height():
    doc = factories.make_doc_with_scaled_text_in_block()  # base height 1.0, block inserted at 2.5x scale -> 2.5
    standard = LayerStandard(
        layers=[],
        text_styles=[TextStyleRule(style_name="MEP-DUCT-TAG", expected_height=2.5, height_tolerance_pct=5.0)],
    )
    results = run(_ctx(doc, standard))
    assert results == []


def test_tolerance_respected():
    doc = factories.make_doc_with_wrong_font_style()  # height 2.5
    standard = LayerStandard(
        layers=[],
        text_styles=[TextStyleRule(style_name="MEP-DUCT-TAG", expected_height=2.4, height_tolerance_pct=10.0)],
    )
    results = run(_ctx(doc, standard))
    assert results == []
