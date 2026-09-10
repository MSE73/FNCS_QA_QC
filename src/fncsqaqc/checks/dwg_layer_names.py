"""Checks that every layer used in a DWG/DXF is part of the firm's approved
layer standard. Xref-bound layer names (e.g. "ARCH-BG|A-WALL") are always
skipped since they belong to the architect's background, not this file."""
from __future__ import annotations

import difflib

from fncsqaqc.checks.base import CheckContext
from fncsqaqc.models import CheckResult, Severity

CHECK_ID = "layer_names"
CHECK_NAME = "Layer Name Compliance"


def run(ctx: CheckContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    approved = ctx.layer_standard.active_layer_names()
    approved_display = {name: rule.name for name, rule in {
        r.name.strip().upper(): r for r in ctx.layer_standard.layers if r.active
    }.items()}

    for layer in ctx.doc.layers:
        name = layer.dxf.name
        if "|" in name:
            continue  # xref-bound layer, not this file's responsibility
        if name.strip().upper() in approved | {"0", "DEFPOINTS"}:
            continue

        close = difflib.get_close_matches(name.upper(), approved, n=1, cutoff=0.75)
        if close:
            suggestion = approved_display.get(close[0], close[0])
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=ctx.relative_path,
                    message=f"Layer '{name}' is not in the approved standard",
                    details=f"Did you mean '{suggestion}'?",
                )
            )
        else:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.FAIL,
                    file=ctx.relative_path,
                    message=f"Layer '{name}' is not in the approved standard",
                    details="No close match found in the layer standard",
                )
            )

    return results
