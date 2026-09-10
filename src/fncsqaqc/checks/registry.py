"""Registry of per-file checks. Phase 2 extension point: new checks
(e.g. calc-based code-compliance) register here the same way."""
from __future__ import annotations

from fncsqaqc.checks import (
    dwg_equipment_tags,
    dwg_layer_names,
    dwg_purge,
    dwg_text_heights,
    dwg_text_style_fonts,
)
from fncsqaqc.checks.base import CheckSpec

CHECKS: list[CheckSpec] = [
    CheckSpec(dwg_layer_names.CHECK_ID, dwg_layer_names.CHECK_NAME, dwg_layer_names.run),
    CheckSpec(dwg_text_style_fonts.CHECK_ID, dwg_text_style_fonts.CHECK_NAME, dwg_text_style_fonts.run),
    CheckSpec(dwg_text_heights.CHECK_ID, dwg_text_heights.CHECK_NAME, dwg_text_heights.run),
    CheckSpec(dwg_purge.CHECK_ID, dwg_purge.CHECK_NAME, dwg_purge.run),
    CheckSpec(
        dwg_equipment_tags.CHECK_ID,
        dwg_equipment_tags.CHECK_NAME,
        dwg_equipment_tags.run,
        enabled_by_default=False,
    ),
]


def active_checks(disabled_ids: set[str], enable_equipment_tags: bool) -> list[CheckSpec]:
    active = []
    for spec in CHECKS:
        if spec.id in disabled_ids:
            continue
        if spec.id == dwg_equipment_tags.CHECK_ID and not enable_equipment_tags:
            continue
        if not spec.enabled_by_default and spec.id != dwg_equipment_tags.CHECK_ID:
            continue
        active.append(spec)
    return active
