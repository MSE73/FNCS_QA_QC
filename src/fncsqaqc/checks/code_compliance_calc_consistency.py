"""Sixth Phase 2 technical-audit sub-check: calc internal numeric
consistency. Mechanically unlike sub-check #5 (load_calc_check, presence-
only) but sharing its same extracted-text input and same hard boundary --
does NOT re-derive or verify the load numbers themselves (out of scope,
would mean independently re-running the load calc). Instead it checks the
calc document against itself: does the SAME equipment tag state a
DIFFERENT value for the same labeled field in two places?

This firm's own calc sheets share one convention worth relying on: each
calc "block" opens with a line like "Pump Reference SMP-01" or "DHWC
Reference DHWC-1" -- a "<...> Reference <TAG>" declaration. A value found
later in the document is attributed to whichever such declaration most
recently precedes it.

Grounded in a real bug found by manual review (project-memory follow-up
#5, docs/PROCEDURE.md #23): F12-04-233's real calc PDF reuses the tag
"SMP-01" for two unrelated pump-sizing blocks -- the first states
"Qin = 0.189274448 L/s", the second (which should have been tagged
"SMP-02") states "Qin = 1.083333333 L/s", a >5x disagreement for what the
calc claims is the same pump's inflow rate.
"""
from __future__ import annotations

import re
from collections import defaultdict

from fncsqaqc.models import CalcConsistencyRule, CheckResult, Severity

CHECK_ID = "calc_consistency_check"
CHECK_NAME = "Calc Internal Numeric Consistency"

_FOLDER_FILE = "(calc document)"

_TAG_RE = re.compile(r"Reference\s+([A-Za-z0-9][A-Za-z0-9\-]{0,11})", re.IGNORECASE)
_NUMBER_RE = re.compile(r"(-?\d+(?:\.\d+)?)")
_NUMBER_WINDOW = 40  # chars scanned after a keyword match for its value


def _tag_positions(calc_text: str) -> list[tuple[int, str]]:
    return [(m.start(), m.group(1)) for m in _TAG_RE.finditer(calc_text)]


def _nearest_preceding_tag(tag_positions: list[tuple[int, str]], pos: int) -> str | None:
    tag = None
    for tag_pos, candidate in tag_positions:
        if tag_pos > pos:
            break
        tag = candidate
    return tag


def check(calc_text: str, rules: list[CalcConsistencyRule]) -> list[CheckResult]:
    results: list[CheckResult] = []
    tag_positions = _tag_positions(calc_text)

    for rule in rules:
        if not rule.active:
            continue

        values_by_tag: dict[str, list[float]] = defaultdict(list)
        keywords = [k.strip() for k in rule.value_label.split("|") if k.strip()]
        for keyword in keywords:
            # Leading \b only: a keyword like "Qin =" ends in a non-word
            # character, so a trailing \b would never match. The leading
            # boundary alone is enough to stop e.g. "Flow Rate" matching
            # inside "Inflow Rate" -- a real false match found in testing.
            pattern = r"\b" + re.escape(keyword)
            for m in re.finditer(pattern, calc_text, re.IGNORECASE):
                window = calc_text[m.end() : m.end() + _NUMBER_WINDOW]
                num_match = _NUMBER_RE.search(window)
                if not num_match:
                    continue
                tag = _nearest_preceding_tag(tag_positions, m.start())
                if tag is None:
                    continue
                values_by_tag[tag].append(float(num_match.group(1)))

        for tag, values in values_by_tag.items():
            if len(values) < 2:
                continue
            max_abs = max(abs(v) for v in values)
            spread = max(values) - min(values)
            pct = (spread / max_abs * 100.0) if max_abs else 0.0
            if pct > rule.tolerance_pct:
                results.append(
                    CheckResult(
                        check_id=CHECK_ID,
                        severity=Severity.FAIL,
                        file=_FOLDER_FILE,
                        message=(
                            f"'{tag}': '{rule.value_label}' disagrees within the same calc "
                            f"document -- values {sorted(set(values))} differ by {pct:.1f}% "
                            f"(tolerance {rule.tolerance_pct:.1f}%)"
                        ),
                        details=rule.notes,
                    )
                )

    return results
