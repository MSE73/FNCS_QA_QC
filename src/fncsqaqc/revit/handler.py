"""Stub for Revit (.rvt) handling.

Revit has no ODA-equivalent headless library for reading .rvt without Revit
itself installed. Real support (Phase 2+) would call out to the pyRevit CLI
(`pyrevit run <script> <model> --revit=<version>`) or a compiled Revit
add-in, invoked via subprocess similar to converters/oda_converter.py, and
parse its output the same way. For now every .rvt file is just recorded as
deferred so it's never silently dropped from the report.
"""
from __future__ import annotations

from fncsqaqc.models import CheckResult, DiscoveredFile, Severity

CHECK_ID = "revit_deferred"


def deferred_result(file: DiscoveredFile) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID,
        severity=Severity.INFO,
        file=str(file.relative_path),
        message="Revit file found but not checked (Revit support deferred to a later phase)",
    )
