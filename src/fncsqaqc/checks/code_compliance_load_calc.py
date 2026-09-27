"""Fifth Phase 2 technical-audit sub-check: load-calc presence/
completeness. Mechanically unlike sub-checks #1-#4 -- no drawing side, no
sizing-summary Excel, no numeric comparison. Formalizes the manual calc
review done by hand in an earlier session (docs/PROCEDURE.md's project-
memory follow-up #5): search the calc document's extracted text for
expected section headers/content and flag what's missing, the same way
that manual review found a real HAP report missing its Design Weather
Data / System Input Data / System Output Data sections, and a water tank
capacity used as a bare input with no sizing derivation shown.

Does NOT re-derive or verify the load numbers themselves (out of scope --
would mean independently re-running the load calc). Presence/absence of
expected content only, same required->FAIL / optional->WARN severity
shape as the folder-completeness checks (checks/folder_completeness.py).
"""
from __future__ import annotations

from fncsqaqc.models import CheckResult, LoadCalcChecklistItem, Severity

CHECK_ID = "load_calc_check"
CHECK_NAME = "Load Calc Presence/Completeness"

_FOLDER_FILE = "(calc document)"


def _found(calc_text: str, keywords: str) -> bool:
    text_lower = calc_text.lower()
    alternatives = [k.strip().lower() for k in keywords.split("|") if k.strip()]
    return any(alt in text_lower for alt in alternatives)


def check(calc_text: str, items: list[LoadCalcChecklistItem]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for item in items:
        if not item.active:
            continue
        if _found(calc_text, item.keywords):
            continue
        severity = Severity.FAIL if item.required else Severity.WARN
        label = "Missing required calc content" if item.required else "Optional calc content not found"
        results.append(
            CheckResult(
                check_id=CHECK_ID,
                severity=severity,
                file=_FOLDER_FILE,
                message=f"{label}: {item.category} / {item.item}",
                details=f"Expected keywords: {item.keywords}. {item.notes}".strip(),
            )
        )
    return results
