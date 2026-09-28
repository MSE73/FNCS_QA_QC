from fncsqaqc.checks.code_compliance_calc_consistency import check
from fncsqaqc.models import CalcConsistencyRule, Severity


def _rule(**kwargs) -> CalcConsistencyRule:
    defaults = dict(value_label="Qin =", tolerance_pct=5.0)
    defaults.update(kwargs)
    return CalcConsistencyRule(**defaults)


def test_consistent_tag_values_pass():
    text = "Pump Reference SMP-01\nQin = 1.25 L/s\nsome other text\nPump Reference SMP-02\nQin = 1.10 L/s"
    results = check(text, [_rule()])
    assert results == []


def test_reused_tag_with_disagreeing_values_fails():
    # This is the real F12-04-233 bug: SMP-01 reused with two very different Qin values.
    text = (
        "Pump Reference SMP-01\nQin = 0.189274448 L/s\n"
        "some other text\n"
        "Pump Reference SMP-01\nQin = 1.083333333 L/s"
    )
    results = check(text, [_rule()])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL
    assert "SMP-01" in results[0].message
    assert "disagrees" in results[0].message


def test_single_occurrence_of_tag_is_silent():
    text = "Pump Reference SMP-01\nQin = 0.19 L/s"
    results = check(text, [_rule()])
    assert results == []


def test_value_within_tolerance_passes():
    # 1.00 vs 1.04 is a 3.8% spread, under the 5% tolerance
    text = "Pump Reference SP-01\nQin = 1.00 L/s\nother\nPump Reference SP-01\nQin = 1.04 L/s"
    results = check(text, [_rule()])
    assert results == []


def test_value_outside_tolerance_fails():
    text = "Pump Reference SP-01\nQin = 1.00 L/s\nother\nPump Reference SP-01\nQin = 1.20 L/s"
    results = check(text, [_rule(tolerance_pct=5.0)])
    assert len(results) == 1
    assert results[0].severity == Severity.FAIL


def test_value_with_no_preceding_tag_is_ignored():
    text = "Qin = 5.0 L/s\nQin = 9.0 L/s"  # no "Reference <TAG>" declaration anywhere
    results = check(text, [_rule()])
    assert results == []


def test_inactive_rule_skipped():
    text = (
        "Pump Reference SMP-01\nQin = 0.19 L/s\n"
        "Pump Reference SMP-01\nQin = 1.08 L/s"
    )
    results = check(text, [_rule(active=False)])
    assert results == []


def test_alternative_keywords_share_one_group():
    rule = _rule(value_label="Total Dynamic Head|TOTAL HEAD LOSS")
    text = (
        "Pump Reference DCWP-01\nTotal Dynamic Head 22 m\n"
        "Pump Reference DCWP-01\nTOTAL HEAD LOSS 9 m"
    )
    results = check(text, [rule])
    assert len(results) == 1
    assert "DCWP-01" in results[0].message


def test_keyword_does_not_match_inside_a_longer_word():
    # "Inflow Rate" must not match a "Flow Rate" keyword -- a real false
    # match found against F12-04-233's calc (docs/PROCEDURE.md #23).
    rule = _rule(value_label="Flow Rate")
    text = (
        "Pump Reference SMP-01\nSump Pit Inflow Rate 0.19 L/s\n"
        "Pump Reference SMP-01\nSump Pit Inflow Rate 9.0 L/s"
    )
    results = check(text, [rule])
    assert results == []


def test_different_tags_not_compared_to_each_other():
    text = "Pump Reference A-01\nQin = 1.0 L/s\nPump Reference B-01\nQin = 9.0 L/s"
    results = check(text, [_rule()])
    assert results == []
