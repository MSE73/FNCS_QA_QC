"""Shared data models for the QA/QC pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    FAIL = "FAIL"


class FileKind(str, Enum):
    DWG = "DWG"
    DXF = "DXF"
    RVT = "RVT"
    PDF = "PDF"
    XLSX = "XLSX"
    OTHER = "OTHER"


@dataclass(frozen=True)
class DiscoveredFile:
    """A file found while walking the target folder."""

    relative_path: Path
    absolute_path: Path
    kind: FileKind
    size: int
    mtime_ns: int


@dataclass
class CheckResult:
    """One row of findings from a single check."""

    check_id: str
    severity: Severity
    file: str
    message: str
    details: str = ""
    occurrences: int = 1


@dataclass
class ConversionLogEntry:
    relative_path: str
    status: str  # "cached" | "converted" | "failed"
    detail: str = ""
    duration_s: float = 0.0


@dataclass
class RunResult:
    """Aggregated results for a full run of the pipeline."""

    folder: Path
    results: list[CheckResult] = field(default_factory=list)
    conversion_log: list[ConversionLogEntry] = field(default_factory=list)
    errors: list[CheckResult] = field(default_factory=list)

    def add(self, result: CheckResult) -> None:
        self.results.append(result)

    def extend(self, results: list[CheckResult]) -> None:
        self.results.extend(results)

    def counts(self) -> dict[Severity, int]:
        counts = {Severity.INFO: 0, Severity.WARN: 0, Severity.FAIL: 0}
        for r in self.results:
            counts[r.severity] += 1
        return counts

    def worst_severity(self) -> Severity:
        counts = self.counts()
        if counts[Severity.FAIL]:
            return Severity.FAIL
        if counts[Severity.WARN]:
            return Severity.WARN
        return Severity.INFO


# ---- Rule set models (loaded from the firm's Excel inputs) ----


@dataclass(frozen=True)
class LayerRule:
    name: str
    discipline: str = ""
    description: str = ""
    active: bool = True


@dataclass(frozen=True)
class TextStyleRule:
    style_name: str
    discipline: str = ""
    expected_font: str = ""
    expected_height: float | None = None
    scales_with_drawing: bool = False
    height_tolerance_pct: float = 5.0
    active: bool = True


@dataclass(frozen=True)
class ScaleMultiplier:
    drawing_scale: str
    multiplier: float


@dataclass
class LayerStandard:
    layers: list[LayerRule]
    text_styles: list[TextStyleRule]
    scale_multipliers: list[ScaleMultiplier] = field(default_factory=list)

    def active_layer_names(self) -> set[str]:
        return {l.name.strip().upper() for l in self.layers if l.active}

    def style_by_name(self) -> dict[str, TextStyleRule]:
        return {s.style_name.strip().upper(): s for s in self.text_styles if s.active}


@dataclass(frozen=True)
class DeliverableItem:
    category: str
    item: str
    expected_pattern: str
    required: bool = True
    discipline: str = ""
    notes: str = ""


@dataclass(frozen=True)
class DrawingListItem:
    drawing_no: str
    title: str
    discipline: str = ""
    expected_pattern: str = ""
    required: bool = True
    notes: str = ""
