import pytest
from openpyxl import Workbook

from fncsqaqc.calcdoc.extract import UnsupportedCalcFileError, extract_text


def test_extract_excel_text(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.append(["Pump Duty Calculation", "SP-01"])
    ws.append(["Total Dynamic Head", 12.5])
    path = tmp_path / "calc.xlsx"
    wb.save(path)

    text = extract_text(path)
    assert "Pump Duty Calculation" in text
    assert "SP-01" in text
    assert "Total Dynamic Head" in text
    assert "12.5" in text


def test_extract_unsupported_extension_raises(tmp_path):
    path = tmp_path / "calc.txt"
    path.write_text("Design Weather Data")

    with pytest.raises(UnsupportedCalcFileError):
        extract_text(path)
