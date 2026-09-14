import math

from fncsqaqc.checks.code_compliance_velocity import check
from fncsqaqc.models import SizingRow, Severity, VelocityLimit


def _limit(**kwargs) -> VelocityLimit:
    defaults = dict(type="Duct", system="Supply", min_velocity=None, max_velocity=8.0, code_basis="ASHRAE")
    defaults.update(kwargs)
    return VelocityLimit(**defaults)


def _row(**kwargs) -> SizingRow:
    defaults = dict(tag="SD-01", type="Duct", system="Supply", design_flow_ls=1000.0, installed_size="600x300")
    defaults.update(kwargs)
    return SizingRow(**defaults)


def test_duct_within_limit_passes():
    # 1000 L/s / (0.6*0.3 m^2) = 5.56 m/s, under the 8.0 m/s max
    results = check([_row()], [_limit()])
    assert results == []


def test_duct_over_max_fails():
    results = check([_row(design_flow_ls=6000.0)], [_limit()])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL
    assert "exceeds the maximum" in results[0].message


def test_pipe_below_min_fails():
    # DN100 pipe, area = pi*0.05^2 = 0.00785 m^2; 0.1 L/s -> ~0.013 m/s, under a 0.6 m/s minimum
    row = _row(type="Pipe", system="Drainage (gravity)", installed_size="DN100", design_flow_ls=0.1)
    limit = _limit(type="Pipe", system="Drainage (gravity)", min_velocity=0.6, max_velocity=None)
    results = check([row], [limit])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL
    assert "below the minimum" in results[0].message


def test_no_matching_limit_warns():
    results = check([_row(system="Made Up System")], [_limit()])
    assert len(results) == 1
    assert results[0].severity == Severity.WARN
    assert "no velocity limit defined" in results[0].message


def test_inactive_limit_warns_with_reason():
    limit = _limit(system="Fuel Gas", min_velocity=None, max_velocity=None, active=False, notes="Sized by pressure drop")
    results = check([_row(system="Fuel Gas")], [limit])
    assert len(results) == 1
    assert results[0].severity == Severity.WARN
    assert "inactive" in results[0].message
    assert "pressure drop" in results[0].details


def test_missing_flow_warns():
    results = check([_row(design_flow_ls=None)], [_limit()])
    assert len(results) == 1
    assert "missing or unparseable Design Flow" in results[0].message


def test_unparseable_size_warns():
    results = check([_row(installed_size="see note")], [_limit()])
    assert len(results) == 1
    assert "could not parse Installed Size" in results[0].message


def test_pipe_size_parses_with_dn_and_mm_suffix():
    limit = _limit(type="Pipe", system="Domestic Cold Water", max_velocity=2.4)
    for size in ["DN50", "50mm", "Ø50"]:
        row = _row(type="Pipe", system="Domestic Cold Water", installed_size=size, design_flow_ls=1.0)
        results = check([row], [limit])
        # 1 L/s / (pi*0.025^2) = 0.509 m/s, under the 2.4 m/s max -> passes for every spelling
        assert results == [], f"size spelling '{size}' should have parsed cleanly"
