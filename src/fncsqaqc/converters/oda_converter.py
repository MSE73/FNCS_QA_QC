"""Drives the ODA File Converter to batch-convert DWG -> DXF, with a
cache so unchanged drawings aren't reconverted on repeat runs.

ODA File Converter CLI (non-interactive):
    ODAFileConverter.exe <in_dir> <out_dir> <out_version> <out_type> <recurse 0|1> <audit 0|1> [filter]
It preserves relative subfolder structure between <in_dir> and <out_dir>.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from fncsqaqc.config import AppConfig
from fncsqaqc.converters.conversion_cache import ConversionCache
from fncsqaqc.models import ConversionLogEntry, DiscoveredFile

ODA_OUT_VERSION = "ACAD2018"
ODA_OUT_TYPE = "DXF"
ODA_TIMEOUT_S = 600


class OdaConversionError(RuntimeError):
    pass


def _link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _run_oda(exe: Path, in_dir: Path, out_dir: Path) -> subprocess.CompletedProcess:
    args = [
        str(exe),
        str(in_dir),
        str(out_dir),
        ODA_OUT_VERSION,
        ODA_OUT_TYPE,
        "1",  # recurse
        "1",  # audit
        "*.DWG",
    ]
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=ODA_TIMEOUT_S,
        check=False,
    )


def ensure_converted(
    dwg_files: list[DiscoveredFile],
    config: AppConfig,
    cache: ConversionCache,
    force: bool = False,
) -> tuple[dict[Path, Path], list[ConversionLogEntry]]:
    """Returns (relative_path -> absolute dxf path, conversion log entries) for
    every given DWG DiscoveredFile, converting only what's stale."""
    resolved: dict[Path, Path] = {}
    log: list[ConversionLogEntry] = []

    stale = [
        f
        for f in dwg_files
        if force or cache.is_stale(f.relative_path, f.size, f.mtime_ns)
    ]
    fresh = [f for f in dwg_files if f not in stale]

    for f in fresh:
        dxf_path = cache.get_dxf_path(f.relative_path)
        resolved[f.relative_path] = dxf_path
        log.append(ConversionLogEntry(str(f.relative_path), "cached"))

    if stale:
        oda_exe = config.require_oda_path()
        start = time.time()
        with tempfile.TemporaryDirectory(prefix="fncsqaqc_stage_") as tmp:
            stage_in = Path(tmp) / "in"
            stage_out = Path(tmp) / "out"
            for f in stale:
                _link_or_copy(f.absolute_path, stage_in / f.relative_path)
            stage_out.mkdir(parents=True, exist_ok=True)

            proc = _run_oda(oda_exe, stage_in, stage_out)
            duration = time.time() - start

            for f in stale:
                produced = (stage_out / f.relative_path).with_suffix(".dxf")
                if produced.is_file():
                    dest = cache.dxf_path_for(f.relative_path)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(produced, dest)
                    cache.record(f.relative_path, f.size, f.mtime_ns, dest.relative_to(cache.dxf_dir))
                    resolved[f.relative_path] = dest
                    log.append(ConversionLogEntry(str(f.relative_path), "converted", duration_s=duration))
                else:
                    detail = (proc.stderr or proc.stdout or "ODA produced no output file").strip()[:500]
                    log.append(
                        ConversionLogEntry(str(f.relative_path), "failed", detail=detail, duration_s=duration)
                    )

        cache.save()

    return resolved, log
