"""Checks that each named text style uses the font mapped to its
system/discipline in the firm's standard, and flags inline font overrides
(e.g. "\\fArial|b0|i0;" inside MTEXT) that silently bypass the style."""
from __future__ import annotations

from fncsqaqc.checks.base import CheckContext
from fncsqaqc.models import CheckResult, Severity

CHECK_ID = "text_style_fonts"
CHECK_NAME = "Text Style / Font Compliance"


def run(ctx: CheckContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    style_rules = ctx.layer_standard.style_by_name()

    for style in ctx.doc.styles:
        name = style.dxf.name
        if not name or name.strip().upper() == "STANDARD":
            continue

        rule = style_rules.get(name.strip().upper())
        actual_font = (style.dxf.font or "").strip()

        if rule is None:
            if ctx.graph.is_style_used(name):
                results.append(
                    CheckResult(
                        check_id=CHECK_ID,
                        severity=Severity.WARN,
                        file=ctx.relative_path,
                        message=f"Text style '{name}' is not in the approved standard",
                        details=f"Currently uses font '{actual_font}'",
                    )
                )
            continue

        expected_font = rule.expected_font.strip()
        if expected_font and actual_font.lower() != expected_font.lower():
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.FAIL,
                    file=ctx.relative_path,
                    message=f"Text style '{name}' uses the wrong font",
                    details=f"Expected '{expected_font}', found '{actual_font or '(none)'}'",
                )
            )

    overrides = ctx.graph.inline_font_overrides
    for block_name, tokens in overrides.items():
        for token in tokens:
            results.append(
                CheckResult(
                    check_id=CHECK_ID,
                    severity=Severity.WARN,
                    file=ctx.relative_path,
                    message="MTEXT uses an inline font override, bypassing the text style standard",
                    details=f"In block/space '{block_name}': \\f{token};",
                )
            )

    return results
