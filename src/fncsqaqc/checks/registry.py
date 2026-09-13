"""Registry of per-file checks. Phase 2 extension point: new checks
(e.g. calc-based code-compliance) register here the same way.

`equipment_tags` is NOT in this registry even though it's a per-file scan --
it needs project-wide reconciliation (see checks/dwg_equipment_tags.py), so
pipeline.py drives its collect/reconcile steps directly instead of dispatching
it through `active_checks` like the others."""
from __future__ import annotations

from fncsqaqc.checks import (
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
]


def active_checks(disabled_ids: set[str]) -> list[CheckSpec]:
    return [spec for spec in CHECKS if spec.id not in disabled_ids]
