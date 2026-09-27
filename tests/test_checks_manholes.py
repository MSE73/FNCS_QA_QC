from fncsqaqc.checks.code_compliance_manholes import check
from fncsqaqc.models import ManholeLimit, ManholeRow, Severity


def _limit(**kwargs) -> ManholeLimit:
    defaults = dict(
        min_depth_m=0.6,
        max_depth_m=1.2,
        min_size_round_mm=450,
        min_size_square_mm=450,
        code_basis="UK Approved Document H, Table 11",
    )
    defaults.update(kwargs)
    return ManholeLimit(**defaults)


def _row(**kwargs) -> ManholeRow:
    defaults = dict(tag="MH-01", mh_size="600X600", depth_m=0.95)
    defaults.update(kwargs)
    return ManholeRow(**defaults)


def test_square_chamber_within_limit_passes():
    # min side 600mm >= 450mm minimum
    results = check([_row()], [_limit()])
    assert results == []


def test_square_chamber_below_min_fails():
    row = _row(mh_size="300X400")  # min side 300mm
    results = check([row], [_limit()])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL
    assert "below the minimum" in results[0].message
    assert "minimum side" in results[0].message


def test_round_chamber_uses_round_column():
    row = _row(mh_size="O400", depth_m=0.95)  # round 400mm, below 450mm round minimum
    results = check([row], [_limit()])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL
    assert "round chamber diameter" in results[0].message


def test_round_chamber_within_limit_passes():
    row = _row(mh_size="900mm", depth_m=0.95)
    results = check([row], [_limit()])
    assert results == []


def test_zero_depth_warns():
    row = _row(depth_m=0)
    results = check([row], [_limit()])
    assert len(results) == 1
    assert results[0].severity == Severity.WARN
    assert "greater than zero" in results[0].message


def test_no_matching_limit_warns():
    row = _row(depth_m=5.0)
    results = check([row], [_limit()])  # limit only covers 0.6-1.2m
    assert len(results) == 1
    assert results[0].severity == Severity.WARN
    assert "no minimum-size limit defined" in results[0].message


def test_inactive_limit_warns_with_reason():
    limit = _limit(active=False, notes="Not yet confirmed for this depth")
    results = check([_row()], [limit])
    assert len(results) == 1
    assert results[0].severity == Severity.WARN
    assert "inactive" in results[0].message
    assert "Not yet confirmed" in results[0].details


def test_missing_depth_warns():
    results = check([_row(depth_m=None)], [_limit()])
    assert len(results) == 1
    assert "missing Approx Depth" in results[0].message


def test_unparseable_size_warns():
    results = check([_row(mh_size="see note")], [_limit()])
    assert len(results) == 1
    assert "could not parse MH Size" in results[0].message


def test_open_ended_top_tier_matches():
    limit = _limit(min_depth_m=1.2, max_depth_m=None, min_size_round_mm=1200, min_size_square_mm=675)
    row = _row(mh_size="600X600", depth_m=2.0)  # min side 600mm, below 675mm minimum
    results = check([row], [limit])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL


def test_shallower_tier_wins_at_shared_boundary():
    # Depth exactly on the shared boundary (0.6m) must match the shallower
    # tier first, per UK Approved Document H's "not exceeding X" phrasing.
    shallow = ManholeLimit(min_depth_m=0.0, max_depth_m=0.6, min_size_round_mm=190, min_size_square_mm=100)
    deep = ManholeLimit(min_depth_m=0.6, max_depth_m=1.2, min_size_round_mm=450, min_size_square_mm=450)
    row = _row(mh_size="150X150", depth_m=0.6)  # passes shallow tier (>=100), would fail deep tier (<450)
    results = check([row], [shallow, deep])
    assert results == []
