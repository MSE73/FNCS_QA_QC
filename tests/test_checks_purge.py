from fncsqaqc.checks.base import CheckContext
from fncsqaqc.checks.dwg_purge import run
from fncsqaqc.dxf.reference_scanner import scan
from fncsqaqc.models import LayerStandard

from tests import factories


def _ctx(doc):
    return CheckContext(
        relative_path="test.dxf", doc=doc, graph=scan(doc), layer_standard=LayerStandard(layers=[], text_styles=[])
    )


def test_unused_layer_reported():
    doc = factories.make_doc_with_unused_layer()
    results = run(_ctx(doc))
    messages = [r.message for r in results]
    assert any("'UNUSED-LAYER'" in m for m in messages)
    assert not any("'USED-LAYER'" in m for m in messages)


def test_orphan_block_reported_but_anonymous_block_is_not():
    doc = factories.make_doc_with_anonymous_block()
    results = run(_ctx(doc))
    assert not any(r.message.startswith("Block '*D") for r in results)
