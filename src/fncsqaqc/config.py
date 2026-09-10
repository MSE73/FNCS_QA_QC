"""Configuration resolution: ODA File Converter path and cache directory.

Priority for the ODA path: CLI flag > env var > user config (%APPDATA%) >
project-local fncsqaqc.toml > default install-path glob.
"""
from __future__ import annotations

import glob
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import platformdirs

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore

APP_NAME = "fncsqaqc"
ENV_ODA_PATH = "FNCSQAQC_ODA_PATH"
DEFAULT_ODA_GLOB = r"C:\Program Files\ODA\ODAFileConverter_*\ODAFileConverter.exe"


class OdaNotFoundError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            "ODA File Converter not found. Install it from https://www.opendesign.com/ "
            "(free download) and either pass --oda-path, set the "
            f"{ENV_ODA_PATH} environment variable, or add oda_converter_path to "
            f"{user_config_path()}."
        )


def user_config_path() -> Path:
    return Path(platformdirs.user_config_dir(APP_NAME)) / "config.toml"


def default_cache_dir() -> Path:
    return Path(platformdirs.user_cache_dir(APP_NAME))


def _read_toml(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def _glob_default_oda() -> str | None:
    matches = sorted(glob.glob(DEFAULT_ODA_GLOB))
    return matches[-1] if matches else None


@dataclass
class AppConfig:
    oda_path: Path | None
    cache_dir: Path

    def require_oda_path(self) -> Path:
        if self.oda_path is None:
            raise OdaNotFoundError()
        return self.oda_path


def resolve_config(
    oda_path_flag: str | None,
    cache_dir_flag: str | None,
    project_config_flag: str | None,
) -> AppConfig:
    """Resolve the ODA path and cache dir. Does NOT fail if ODA can't be found -
    that's only fatal if a DWG actually needs converting (see converters/oda_converter.py)."""
    oda_path = oda_path_flag or os.environ.get(ENV_ODA_PATH)

    if not oda_path:
        user_cfg = _read_toml(user_config_path())
        oda_path = user_cfg.get("oda_converter_path")

    if not oda_path:
        project_cfg_path = Path(project_config_flag) if project_config_flag else Path("fncsqaqc.toml")
        project_cfg = _read_toml(project_cfg_path)
        oda_path = project_cfg.get("oda_converter_path")

    if not oda_path:
        oda_path = _glob_default_oda()

    resolved_oda = Path(oda_path) if oda_path and Path(oda_path).is_file() else None
    cache_dir = Path(cache_dir_flag) if cache_dir_flag else default_cache_dir()
    return AppConfig(oda_path=resolved_oda, cache_dir=cache_dir)
