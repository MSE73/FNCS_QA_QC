import pytest
from openpyxl import Workbook

from fncsqaqc.excelio.common import ExcelSchemaError
from fncsqaqc.excelio.deliverables_list import load_deliverables
from fncsqaqc.excelio.layer_list import load_layer_standard


def test_load_layer_standard_valid(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Layers"
    ws.append(["Layer Name", "Discipline", "Description", "Active (Y/N)"])
    ws.append(["M-DUCT", "Mechanical", "Ductwork", "Y"])
    styles_ws = wb.create_sheet("TextStyles")
    styles_ws.append(["Style Name", "System/Discipline", "Expected Font", "Expected Height"])
    styles_ws.append(["MEP-DUCT-TAG", "Mechanical", "simplex.shx", 2.5])
    path = tmp_path / "layers.xlsx"
    wb.save(path)

    standard = load_layer_standard(path)
    assert standard.active_layer_names() == {"M-DUCT"}
    assert standard.style_by_name()["MEP-DUCT-TAG"].expected_font == "simplex.shx"


def test_load_layer_standard_missing_column_raises_specific_error(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Layers"
    ws.append(["Layer Name Typo", "Discipline"])  # missing "Layer Name"
    ws.append(["M-DUCT", "Mechanical"])
    wb.create_sheet("TextStyles").append(["Style Name"])
    path = tmp_path / "bad_layers.xlsx"
    wb.save(path)

    with pytest.raises(ExcelSchemaError) as exc_info:
        load_layer_standard(path)
    assert "Layer Name" in str(exc_info.value)
    assert "Layers" in str(exc_info.value)


def test_load_deliverables_missing_sheet_raises(tmp_path):
    wb = Workbook()
    wb.active.title = "WrongSheetName"
    path = tmp_path / "deliverables.xlsx"
    wb.save(path)

    with pytest.raises(ExcelSchemaError) as exc_info:
        load_deliverables(path)
    assert "sheet not found" in str(exc_info.value)


def test_load_deliverables_valid(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Deliverables"
    ws.append(["Category", "Item", "Expected Pattern", "Required (Y/N)"])
    ws.append(["Calcs", "HVAC Load", "Calculations/*.pdf", "Y"])
    path = tmp_path / "deliverables.xlsx"
    wb.save(path)

    items = load_deliverables(path)
    assert len(items) == 1
    assert items[0].category == "Calcs"
    assert items[0].required is True
