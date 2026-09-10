"""Loads the firm's Layers & Text Styles standard workbook."""
from __future__ import annotations

from pathlib import Path

from fncsqaqc.excelio.common import ExcelSchemaError, as_bool, as_float, as_str, read_rows
from fncsqaqc.models import LayerRule, LayerStandard, ScaleMultiplier, TextStyleRule


def load_layer_standard(workbook_path: Path) -> LayerStandard:
    layer_rows = read_rows(
        workbook_path,
        "Layers",
        required_columns=["Layer Name"],
        optional_columns=["Discipline", "Description", "Active (Y/N)"],
    )
    layers = [
        LayerRule(
            name=as_str(row["Layer Name"]),
            discipline=as_str(row.get("Discipline")),
            description=as_str(row.get("Description")),
            active=as_bool(row.get("Active (Y/N)")),
        )
        for row in layer_rows
        if as_str(row["Layer Name"])
    ]

    style_rows = read_rows(
        workbook_path,
        "TextStyles",
        required_columns=["Style Name"],
        optional_columns=[
            "System/Discipline",
            "Expected Font",
            "Expected Height",
            "Height Scales With Drawing (Y/N)",
            "Height Tolerance %",
            "Active (Y/N)",
        ],
    )
    text_styles = [
        TextStyleRule(
            style_name=as_str(row["Style Name"]),
            discipline=as_str(row.get("System/Discipline")),
            expected_font=as_str(row.get("Expected Font")),
            expected_height=as_float(row.get("Expected Height")),
            scales_with_drawing=as_bool(row.get("Height Scales With Drawing (Y/N)"), default=False),
            height_tolerance_pct=as_float(row.get("Height Tolerance %")) or 5.0,
            active=as_bool(row.get("Active (Y/N)")),
        )
        for row in style_rows
        if as_str(row["Style Name"])
    ]

    scale_multipliers: list[ScaleMultiplier] = []
    try:
        scale_rows = read_rows(
            workbook_path,
            "ScaleMultipliers",
            required_columns=["Drawing Scale", "Multiplier"],
        )
        scale_multipliers = [
            ScaleMultiplier(drawing_scale=as_str(row["Drawing Scale"]), multiplier=as_float(row["Multiplier"]) or 1.0)
            for row in scale_rows
        ]
    except ExcelSchemaError:
        pass  # ScaleMultipliers sheet is optional

    return LayerStandard(layers=layers, text_styles=text_styles, scale_multipliers=scale_multipliers)
