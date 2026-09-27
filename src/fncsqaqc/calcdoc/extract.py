"""Extracts plain text from a project's calc source document, for the
load-calc-presence check (checks/code_compliance_load_calc.py). This
firm's calc sources are an unstandardized mix of PDF (typically a Carrier
HAP export) and Excel (manual pump/tank duty calcs) -- dispatches on file
extension rather than requiring one fixed format.

Presence-only: this extracts text so a checklist item's keywords can be
searched for, it does not parse or verify any numeric value."""
from __future__ import annotations

from pathlib import Path

import openpyxl
from pypdf import PdfReader


class UnsupportedCalcFileError(ValueError):
    pass


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(path)
    if suffix in (".xlsx", ".xlsm"):
        return _extract_excel_text(path)
    raise UnsupportedCalcFileError(
        f"Unsupported calc file type '{suffix}' -- expected .pdf or .xlsx/.xlsm ({path})"
    )


def _extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_excel_text(path: Path) -> str:
    wb = openpyxl.load_workbook(path, data_only=True)
    chunks: list[str] = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            for value in row:
                if value is not None:
                    chunks.append(str(value))
    return "\n".join(chunks)
