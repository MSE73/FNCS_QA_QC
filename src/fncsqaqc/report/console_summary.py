"""Prints a colored pass/fail summary to the terminal after a run."""
from __future__ import annotations

from collections import Counter

from rich.console import Console
from rich.table import Table

from fncsqaqc.models import RunResult, Severity

_SEVERITY_STYLE = {
    Severity.FAIL: "bold red",
    Severity.WARN: "yellow",
    Severity.INFO: "cyan",
}


def print_summary(run: RunResult, output_path) -> None:
    console = Console()
    counts = run.counts()

    table = Table(title="FNCS QA/QC Summary")
    table.add_column("Severity")
    table.add_column("Count", justify="right")
    for sev in (Severity.FAIL, Severity.WARN, Severity.INFO):
        table.add_row(f"[{_SEVERITY_STYLE[sev]}]{sev.value}[/]", str(counts[sev]))
    console.print(table)

    by_file: Counter = Counter()
    for r in run.results:
        if r.severity == Severity.FAIL:
            by_file[r.file] += 1
    if by_file:
        top = Table(title="Top failing files")
        top.add_column("File")
        top.add_column("FAIL count", justify="right")
        for file, count in by_file.most_common(10):
            top.add_row(file, str(count))
        console.print(top)

    if run.errors:
        console.print(f"[bold red]{len(run.errors)} file(s) could not be processed[/] — see the 'Errors' sheet.")

    console.print(f"Report written to: [bold]{output_path}[/]")
