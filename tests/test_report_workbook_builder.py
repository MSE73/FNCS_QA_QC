"""Guards against a check whose findings are built but silently routed to
the catch-all "Other" sheet because nobody registered it in
_SHEET_FOR_CHECK -- exactly what happened to manhole_check until this test
was added (its acceptance test happened to produce zero findings, so the
missing mapping went unnoticed)."""
from fncsqaqc.checks import (
    code_compliance_calc_consistency,
    code_compliance_equipment_sizing,
    code_compliance_load_calc,
    code_compliance_manholes,
    code_compliance_slope,
    code_compliance_velocity,
)
from fncsqaqc.report.workbook_builder import _SHEET_FOR_CHECK

_PHASE2_CHECK_MODULES = [
    code_compliance_velocity,
    code_compliance_slope,
    code_compliance_equipment_sizing,
    code_compliance_manholes,
    code_compliance_load_calc,
    code_compliance_calc_consistency,
]


def test_every_phase2_check_id_routes_to_a_sheet():
    for module in _PHASE2_CHECK_MODULES:
        assert module.CHECK_ID in _SHEET_FOR_CHECK, (
            f"{module.CHECK_ID} has no sheet mapping in _SHEET_FOR_CHECK -- "
            "its findings would silently land on the 'Other' sheet"
        )
