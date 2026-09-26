from fncsqaqc.checks.code_compliance_equipment_sizing import check
from fncsqaqc.models import EquipmentSizingRow, Severity


def _row(**kwargs) -> EquipmentSizingRow:
    defaults = dict(
        tag="DCWP-01",
        parameter="Flow (L/s)",
        required_value=1.0,
        installed_value=1.45,
        unit="L/s",
        tolerance_pct=0.0,
    )
    defaults.update(kwargs)
    return EquipmentSizingRow(**defaults)


def test_installed_meets_required_passes():
    results = check([_row()])
    assert results == []


def test_installed_exactly_meets_required_passes():
    results = check([_row(required_value=1.45, installed_value=1.45)])
    assert results == []


def test_installed_undersized_fails():
    results = check([_row(required_value=2.0, installed_value=1.45)])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL
    assert "undersized" in results[0].message
    assert "1.45" in results[0].message and "2" in results[0].message


def test_tolerance_absorbs_small_shortfall():
    # required 2.0, installed 1.9 -> 5% short, absorbed by a 5% tolerance
    results = check([_row(required_value=2.0, installed_value=1.9, tolerance_pct=5.0)])
    assert results == []


def test_tolerance_does_not_absorb_large_shortfall():
    results = check([_row(required_value=2.0, installed_value=1.5, tolerance_pct=5.0)])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL
    assert "tolerance 5%" in results[0].message


def test_missing_required_warns():
    results = check([_row(required_value=None)])
    assert len(results) == 1
    assert results[0].severity == Severity.WARN
    assert "Required (Calc)" in results[0].message


def test_missing_installed_warns():
    results = check([_row(installed_value=None)])
    assert len(results) == 1
    assert results[0].severity == Severity.WARN
    assert "Installed (Drawing)" in results[0].message
