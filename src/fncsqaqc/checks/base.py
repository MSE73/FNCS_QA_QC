"""Shared context and protocol for per-file DXF checks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from ezdxf.document import Drawing

from fncsqaqc.dxf.reference_scanner import ReferenceGraph
from fncsqaqc.models import CheckResult, LayerStandard


@dataclass
class CheckContext:
    relative_path: str
    doc: Drawing
    graph: ReferenceGraph
    layer_standard: LayerStandard


class FileCheck(Protocol):
    def __call__(self, ctx: CheckContext) -> list[CheckResult]: ...


@dataclass
class CheckSpec:
    id: str
    name: str
    fn: FileCheck
    enabled_by_default: bool = True
