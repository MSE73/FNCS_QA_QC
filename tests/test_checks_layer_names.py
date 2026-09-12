from fncsqaqc.checks.base import CheckContext
from fncsqaqc.checks.dwg_layer_names import run
from fncsqaqc.dxf.reference_scanner import scan
from fncsqaqc.models import LayerRule, LayerStandard, Severity

from tests import factories


def _ctx(doc, layer_standard):
    return CheckContext(relative_path="test.dxf", doc=doc, graph=scan(doc), layer_standard=layer_standard)


def test_approved_layer_passes():
    doc = factories.make_basic_doc()
    standard = LayerStandard(layers=[LayerRule(name="M-DUCT")], text_styles=[])
    results = run(_ctx(doc, standard))
    assert results == []


def test_typo_layer_is_warned_with_suggestion():
    doc = factories.make_basic_doc()
    doc.layers.add("M-DUCTS")  # close to M-DUCT
    standard = LayerStandard(layers=[LayerRule(name="M-DUCT")], text_styles=[])
    results = run(_ctx(doc, standard))
    typo_result = next(r for r in results if "M-DUCTS" in r.message)
    assert typo_result.severity == Severity.WARN
    assert "M-DUCT" in typo_result.details


def test_unknown_layer_is_failed():
    doc = factories.make_basic_doc()
    doc.layers.add("RANDOM-LAYER-XYZ")
    standard = LayerStandard(layers=[LayerRule(name="M-DUCT")], text_styles=[])
    results = run(_ctx(doc, standard))
    unknown_result = next(r for r in results if "RANDOM-LAYER-XYZ" in r.message)
    assert unknown_result.severity == Severity.FAIL


def test_xref_bound_layer_is_skipped():
    doc = factories.make_doc_with_xref_layer()
    standard = LayerStandard(layers=[], text_styles=[])
    results = run(_ctx(doc, standard))
    assert results == []


def test_xref_bind_renamed_layer_is_skipped():
    doc = factories.make_doc_with_bound_xref_layer()
    standard = LayerStandard(layers=[], text_styles=[])
    results = run(_ctx(doc, standard))
    assert results == []
