from fncsqaqc.dxf.reference_scanner import is_purgeable_block_name, scan

from tests import factories


def test_unused_layer_is_detected():
    doc = factories.make_doc_with_unused_layer()
    graph = scan(doc)
    assert graph.is_layer_used("USED-LAYER")
    assert not graph.is_layer_used("UNUSED-LAYER")


def test_layer_used_only_in_orphan_block_is_still_considered_used():
    doc = factories.make_doc_with_layer_used_only_in_orphan_block()
    graph = scan(doc)
    assert graph.is_layer_used("ORPHAN-LAYER")


def test_layer_used_only_via_viewport_freeze_is_considered_used():
    doc = factories.make_doc_with_layer_used_only_via_viewport_freeze()
    graph = scan(doc)
    assert graph.is_layer_used("FROZEN-LAYER")


def test_reserved_layers_always_used():
    doc = factories.make_basic_doc()
    graph = scan(doc)
    assert graph.is_layer_used("0")
    assert graph.is_layer_used("Defpoints")


def test_anonymous_block_is_not_purgeable():
    doc = factories.make_doc_with_anonymous_block()
    graph = scan(doc)
    anonymous_blocks = [b.name for b in doc.blocks if b.name.startswith("*D")]
    assert anonymous_blocks, "test setup should have produced an anonymous dimension block"
    for name in anonymous_blocks:
        assert not is_purgeable_block_name(name)


def test_orphan_block_itself_is_reported_unused():
    doc = factories.make_doc_with_layer_used_only_in_orphan_block()
    graph = scan(doc)
    assert not graph.is_block_used("OrphanBlock")


def test_inserted_block_is_used():
    doc = factories.make_doc_with_scaled_text_in_block()
    graph = scan(doc)
    assert graph.is_block_used("TagBlock")
