from fncsqaqc.checks.code_compliance_load_calc import check
from fncsqaqc.models import LoadCalcChecklistItem, Severity


def _item(**kwargs) -> LoadCalcChecklistItem:
    defaults = dict(
        category="HAP Air Conditioning Report",
        item="Design Weather Data",
        keywords="Design Weather Data|Weather Data",
    )
    defaults.update(kwargs)
    return LoadCalcChecklistItem(**defaults)


def test_keyword_present_passes():
    text = "Section 3: Design Weather Data\nAmman, Jordan..."
    results = check(text, [_item()])
    assert results == []


def test_keyword_present_case_insensitive():
    text = "SECTION 3: DESIGN WEATHER DATA"
    results = check(text, [_item()])
    assert results == []


def test_alternative_keyword_matches():
    text = "Weather Data Summary for the design day"
    results = check(text, [_item()])
    assert results == []


def test_required_missing_fails():
    text = "Zone Sizing Summary\nDOAS Sizing Summary"
    results = check(text, [_item()])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL
    assert "Missing required calc content" in results[0].message
    assert "Design Weather Data" in results[0].message


def test_optional_missing_warns():
    item = _item(required=False)
    results = check("nothing relevant here", [item])
    assert len(results) == 1
    assert results[0].severity == Severity.WARN
    assert "Optional calc content not found" in results[0].message


def test_inactive_item_skipped():
    item = _item(active=False)
    results = check("nothing relevant here", [item])
    assert results == []


def test_multiple_items_multiple_findings():
    items = [
        _item(item="Design Weather Data", keywords="Design Weather Data"),
        _item(item="System Input Data", keywords="System Input Data"),
    ]
    text = "Zone Sizing Summary only"
    results = check(text, items)
    assert len(results) == 2
    assert {r.message.split(": ")[1].split(" / ")[1] for r in results} == {
        "Design Weather Data",
        "System Input Data",
    }
