"""Command-line entry point."""
from __future__ import annotations

import datetime as dt
import logging
import sys
from pathlib import Path

import click

from fncsqaqc.checks.registry import CHECKS
from fncsqaqc.config import OdaNotFoundError, resolve_config
from fncsqaqc.excelio.deliverables_list import load_deliverables
from fncsqaqc.excelio.drawings_list import load_drawings_list
from fncsqaqc.excelio.layer_list import load_layer_standard
from fncsqaqc.excelio.sizing_summary import load_velocity_sizing
from fncsqaqc.excelio.velocity_limits import load_velocity_limits
from fncsqaqc.models import Severity
from fncsqaqc.pipeline import RunOptions, run as run_pipeline
from fncsqaqc.report import console_summary, workbook_builder

_VALID_CHECK_IDS = {spec.id for spec in CHECKS}


@click.group()
def cli() -> None:
    """FNCS MEP drawing QA/QC checker."""


@cli.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--layers-excel", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--deliverables-excel", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--drawings-excel", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--output", type=click.Path(path_type=Path), default=None)
@click.option("--cache-dir", type=click.Path(path_type=Path), default=None)
@click.option("--oda-path", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
@click.option("--config", "config_path", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
@click.option("--no-cache", is_flag=True, default=False, help="Force reconversion of every DWG.")
@click.option("--enable-equipment-tag-check", is_flag=True, default=False)
@click.option(
    "--velocity-excel",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Per-project sizing-summary workbook (Velocity sheet). Requires --velocity-limits-excel.",
)
@click.option(
    "--velocity-limits-excel",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Firm-wide velocity-limit reference table (docs/excel_templates/VelocityLimits.xlsx).",
)
@click.option("--disable-check", "disabled_checks", multiple=True, help="Disable a check by id (repeatable).")
@click.option(
    "--fail-on",
    type=click.Choice(["none", "warn", "fail"]),
    default="fail",
    help="Controls the process exit code.",
)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-q", "--quiet", is_flag=True, default=False)
def check(
    folder: Path,
    layers_excel: Path,
    deliverables_excel: Path,
    drawings_excel: Path,
    output: Path | None,
    cache_dir: Path | None,
    oda_path: Path | None,
    config_path: Path | None,
    no_cache: bool,
    enable_equipment_tag_check: bool,
    velocity_excel: Path | None,
    velocity_limits_excel: Path | None,
    disabled_checks: tuple[str, ...],
    fail_on: str,
    verbose: bool,
    quiet: bool,
) -> None:
    """Run drawing-cleanliness and folder-completeness checks against FOLDER."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else (logging.WARNING if quiet else logging.INFO),
        format="%(levelname)s: %(message)s",
    )

    unknown = set(disabled_checks) - _VALID_CHECK_IDS
    if unknown:
        raise click.BadParameter(
            f"Unknown check id(s): {', '.join(sorted(unknown))}. Valid ids: {', '.join(sorted(_VALID_CHECK_IDS))}",
            param_hint="--disable-check",
        )
    if velocity_excel and not velocity_limits_excel:
        raise click.BadParameter(
            "--velocity-excel requires --velocity-limits-excel", param_hint="--velocity-limits-excel"
        )

    app_config = resolve_config(
        oda_path_flag=str(oda_path) if oda_path else None,
        cache_dir_flag=str(cache_dir) if cache_dir else None,
        project_config_flag=str(config_path) if config_path else None,
    )

    layer_standard = load_layer_standard(layers_excel)
    deliverables = load_deliverables(deliverables_excel)
    drawings_list = load_drawings_list(drawings_excel)
    velocity_sizing = load_velocity_sizing(velocity_excel) if velocity_excel else []
    velocity_limits = load_velocity_limits(velocity_limits_excel) if velocity_limits_excel else []

    if output is None:
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path.cwd() / f"QAQC_Report_{folder.name}_{timestamp}.xlsx"

    options = RunOptions(
        folder=folder,
        layer_standard=layer_standard,
        deliverables=deliverables,
        drawings_list=drawings_list,
        config=app_config,
        force_reconvert=no_cache,
        disabled_check_ids=frozenset(disabled_checks),
        enable_equipment_tags=enable_equipment_tag_check,
        velocity_sizing=velocity_sizing,
        velocity_limits=velocity_limits,
    )

    try:
        result = run_pipeline(options)
    except OdaNotFoundError as exc:
        click.echo(str(exc), err=True)
        sys.exit(2)

    workbook_builder.build(result, output)
    if not quiet:
        console_summary.print_summary(result, output)

    exit_code = _determine_exit_code(result, fail_on)
    sys.exit(exit_code)


def _determine_exit_code(result, fail_on: str) -> int:
    if result.errors:
        return 1
    counts = result.counts()
    if fail_on == "none":
        return 0
    if fail_on == "warn" and (counts[Severity.WARN] or counts[Severity.FAIL]):
        return 1
    if fail_on == "fail" and counts[Severity.FAIL]:
        return 1
    return 0


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
