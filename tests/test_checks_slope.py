from fncsqaqc.checks.code_compliance_slope import check
from fncsqaqc.models import SlopeLimit, SlopeRow, Severity


def _limit(**kwargs) -> SlopeLimit:
    defaults = dict(min_diameter_mm=66, max_diameter_mm=150, min_slope_pct=1.04, code_basis="IPC Table 704.1")
    defaults.update(kwargs)
    return SlopeLimit(**defaults)


def _row(**kwargs) -> SlopeRow:
    defaults = dict(
        tag="MH-01 to MH-02",
        installed_size="150mm",
        upstream_invert_m=981.50,
        downstream_invert_m=980.95,
        length_m=30.0,
    )
    defaults.update(kwargs)
    return SlopeRow(**defaults)


def test_slope_within_limit_passes():
    # (981.50-980.95)/30 = 1.83%, above the 1.04% minimum
    results = check([_row()], [_limit()])
    assert results == []


def test_slope_below_min_fails():
    # (981.50-981.40)/30 = 0.33%, below the 1.04% minimum
    row = _row(downstream_invert_m=981.40)
    results = check([row], [_limit()])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL
    assert "below the minimum" in results[0].message


def test_uphill_run_fails():
    row = _row(downstream_invert_m=981.60)  # higher than upstream
    results = check([row], [_limit()])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL
    assert "uphill" in results[0].message


def test_zero_length_warns():
    row = _row(length_m=0)
    results = check([row], [_limit()])
    assert len(results) == 1
    assert results[0].severity == Severity.WARN
    assert "greater than zero" in results[0].message


def test_no_matching_limit_warns():
    row = _row(installed_size="900mm")
    results = check([row], [_limit()])  # limit only covers 66-150mm
    assert len(results) == 1
    assert results[0].severity == Severity.WARN
    assert "no minimum-slope limit defined" in results[0].message


def test_inactive_limit_warns_with_reason():
    limit = _limit(active=False, notes="Not yet confirmed for this diameter")
    results = check([_row()], [limit])
    assert len(results) == 1
    assert results[0].severity == Severity.WARN
    assert "inactive" in results[0].message
    assert "Not yet confirmed" in results[0].details


def test_missing_invert_warns():
    results = check([_row(upstream_invert_m=None)], [_limit()])
    assert len(results) == 1
    assert "missing or unparseable invert level" in results[0].message


def test_unparseable_size_warns():
    results = check([_row(installed_size="see note")], [_limit()])
    assert len(results) == 1
    assert "could not parse Installed Size" in results[0].message


def test_open_ended_top_tier_matches():
    limit = _limit(min_diameter_mm=151, max_diameter_mm=None, min_slope_pct=0.52)
    row = _row(installed_size="DN300", upstream_invert_m=100.0, downstream_invert_m=99.9, length_m=30.0)
    # (100.0-99.9)/30 = 0.33%, below 0.52% minimum
    results = check([row], [limit])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL
