"""Remembers the firm-wide reference-file paths (layer standard, limit
tables, checklists) so the GUI doesn't make the engineer re-browse for them
on every run -- only the per-project inputs change run to run."""
from __future__ import annotations

import json
from pathlib import Path

import platformdirs

from fncsqaqc.config import APP_NAME

FIRM_WIDE_KEYS = (
    "layers_excel",
    "velocity_limits_excel",
    "slope_limits_excel",
    "manhole_limits_excel",
    "calc_checklist_excel",
    "calc_consistency_excel",
)


def settings_path() -> Path:
    return Path(platformdirs.user_config_dir(APP_NAME)) / "gui_settings.json"


def load_firm_wide_paths() -> dict[str, str]:
    path = settings_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {k: v for k, v in data.items() if k in FIRM_WIDE_KEYS and isinstance(v, str)}


def save_firm_wide_paths(values: dict[str, str]) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    to_write = {k: v for k, v in values.items() if k in FIRM_WIDE_KEYS and v}
    path.write_text(json.dumps(to_write, indent=2), encoding="utf-8")
