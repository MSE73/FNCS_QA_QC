"""Orchestrates a full QA/QC run: discover -> convert -> inspect -> aggregate -> report."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fncsqaqc.checks.base import CheckContext
from fncsqaqc.checks.folder_completeness import check_deliverables, check_drawings
from fncsqaqc.checks.registry import active_checks
from fncsqaqc.config import AppConfig
from fncsqaqc.converters.conversion_cache import ConversionCache
from fncsqaqc.converters.oda_converter import ensure_converted
from fncsqaqc.discovery.file_classifier import discover
from fncsqaqc.dxf import loader as dxf_loader
from fncsqaqc.dxf.reference_scanner import scan as scan_references
from fncsqaqc.models import (
    CheckResult,
    DeliverableItem,
    DrawingListItem,
    FileKind,
    LayerStandard,
    RunResult,
    Severity,
)
from fncsqaqc.revit.handler import deferred_result


@dataclass
class RunOptions:
    folder: Path
    layer_standard: LayerStandard
    deliverables: list[DeliverableItem]
    drawings_list: list[DrawingListItem]
    config: AppConfig
    force_reconvert: bool = False
    disabled_check_ids: frozenset[str] = frozenset()
    enable_equipment_tags: bool = False


def run(options: RunOptions) -> RunResult:
    result = RunResult(folder=options.folder)

    files = discover(options.folder)
    dwg_files = [f for f in files if f.kind == FileKind.DWG]
    dxf_files = [f for f in files if f.kind == FileKind.DXF]
    rvt_files = [f for f in files if f.kind == FileKind.RVT]

    for f in rvt_files:
        result.add(deferred_result(f))

    cache = ConversionCache(options.config.cache_dir, options.folder)
    converted, conversion_log = ensure_converted(
        dwg_files, options.config, cache, force=options.force_reconvert
    )
    result.conversion_log.extend(conversion_log)

    checks = active_checks(options.disabled_check_ids, options.enable_equipment_tags)

    dxf_targets: list[tuple[str, Path]] = [
        (str(f.relative_path), converted[f.relative_path])
        for f in dwg_files
        if f.relative_path in converted
    ] + [(str(f.relative_path), f.absolute_path) for f in dxf_files]

    for relative_path, dxf_path in dxf_targets:
        load_result = dxf_loader.load(dxf_path)

        if load_result.doc is None:
            result.errors.append(
                CheckResult(
                    check_id="load_error",
                    severity=Severity.FAIL,
                    file=relative_path,
                    message="File could not be opened",
                    details=load_result.error or "",
                )
            )
            continue

        if load_result.needed_repair:
            result.add(
                CheckResult(
                    check_id="load_error",
                    severity=Severity.WARN,
                    file=relative_path,
                    message="File had structural errors and needed repair to open",
                    details=load_result.error or "",
                )
            )

        graph = scan_references(load_result.doc)
        ctx = CheckContext(
            relative_path=relative_path,
            doc=load_result.doc,
            graph=graph,
            layer_standard=options.layer_standard,
        )

        for spec in checks:
            try:
                result.extend(spec.fn(ctx))
            except Exception as exc:  # noqa: BLE001 - one check failing must not abort the run
                result.errors.append(
                    CheckResult(
                        check_id=spec.id,
                        severity=Severity.FAIL,
                        file=relative_path,
                        message=f"Check '{spec.name}' raised an error",
                        details=str(exc),
                    )
                )

    result.extend(check_deliverables(options.deliverables, files))
    result.extend(check_drawings(options.drawings_list, files))

    return result
