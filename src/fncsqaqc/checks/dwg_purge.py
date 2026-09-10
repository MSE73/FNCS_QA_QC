"""Reports unused (purgeable) layers, text styles, linetypes, and blocks,
based on the reference graph built by dxf/reference_scanner.py."""
from __future__ import annotations

from fncsqaqc.checks.base import CheckContext
from fncsqaqc.dxf.reference_scanner import is_purgeable_block_name
from fncsqaqc.models import CheckResult, Severity

CHECK_ID = "purge"
CHECK_NAME = "Unused Resources (Purge)"


def run(ctx: CheckContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    doc, graph = ctx.doc, ctx.graph

    for layer in doc.layers:
        if not graph.is_layer_used(layer.dxf.name):
            results.append(_result(ctx, "Layer", layer.dxf.name))

    for style in doc.styles:
        if style.dxf.name and not graph.is_style_used(style.dxf.name):
            results.append(_result(ctx, "Text style", style.dxf.name))

    for linetype in doc.linetypes:
        if linetype.dxf.name and not graph.is_linetype_used(linetype.dxf.name):
            results.append(_result(ctx, "Linetype", linetype.dxf.name))

    for block in doc.blocks:
        if is_purgeable_block_name(block.name) and not graph.is_block_used(block.name):
            results.append(_result(ctx, "Block", block.name))

    return results


def _result(ctx: CheckContext, kind: str, name: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID,
        severity=Severity.WARN,
        file=ctx.relative_path,
        message=f"{kind} '{name}' is unused and should be purged",
    )
