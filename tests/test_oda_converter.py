from pathlib import Path

from fncsqaqc.config import AppConfig
from fncsqaqc.converters import oda_converter
from fncsqaqc.converters.conversion_cache import ConversionCache
from fncsqaqc.models import DiscoveredFile, FileKind


def _make_dwg(tmp_path: Path, name: str) -> DiscoveredFile:
    src_dir = tmp_path / "source"
    src_dir.mkdir(exist_ok=True)
    path = src_dir / name
    path.write_bytes(b"fake dwg content")
    stat = path.stat()
    return DiscoveredFile(
        relative_path=Path(name),
        absolute_path=path,
        kind=FileKind.DWG,
        size=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
    )


def _fake_config(tmp_path: Path) -> AppConfig:
    fake_exe = tmp_path / "ODAFileConverter.exe"
    fake_exe.write_text("not a real exe")
    return AppConfig(oda_path=fake_exe, cache_dir=tmp_path / "cache")


def test_first_run_converts_and_caches(tmp_path, monkeypatch):
    calls = []

    def fake_run_oda(exe, in_dir, out_dir):
        calls.append((in_dir, out_dir))
        for dwg in in_dir.glob("*.DWG") or in_dir.glob("*.dwg"):
            (out_dir / dwg.name).with_suffix(".dxf").write_text("fake dxf")
        for dwg in in_dir.glob("*.dwg"):
            (out_dir / dwg.name).with_suffix(".dxf").write_text("fake dxf")

        class FakeProc:
            stdout = ""
            stderr = ""

        return FakeProc()

    monkeypatch.setattr(oda_converter, "_run_oda", fake_run_oda)

    config = _fake_config(tmp_path)
    dwg = _make_dwg(tmp_path, "D-101.dwg")
    cache = ConversionCache(config.cache_dir, tmp_path / "source")

    resolved, log = oda_converter.ensure_converted([dwg], config, cache)

    assert len(calls) == 1
    assert dwg.relative_path in resolved
    assert resolved[dwg.relative_path].is_file()
    assert log[0].status == "converted"


def test_unchanged_dwg_is_not_reconverted(tmp_path, monkeypatch):
    call_count = {"n": 0}

    def fake_run_oda(exe, in_dir, out_dir):
        call_count["n"] += 1
        for dwg in list(in_dir.glob("*.dwg")) + list(in_dir.glob("*.DWG")):
            (out_dir / dwg.name).with_suffix(".dxf").write_text("fake dxf")

        class FakeProc:
            stdout = ""
            stderr = ""

        return FakeProc()

    monkeypatch.setattr(oda_converter, "_run_oda", fake_run_oda)

    config = _fake_config(tmp_path)
    dwg = _make_dwg(tmp_path, "D-101.dwg")
    cache = ConversionCache(config.cache_dir, tmp_path / "source")

    oda_converter.ensure_converted([dwg], config, cache)
    assert call_count["n"] == 1

    cache2 = ConversionCache(config.cache_dir, tmp_path / "source")
    resolved2, log2 = oda_converter.ensure_converted([dwg], config, cache2)

    assert call_count["n"] == 1  # no second ODA invocation
    assert log2[0].status == "cached"
    assert resolved2[dwg.relative_path].is_file()


def test_modified_dwg_is_reconverted(tmp_path, monkeypatch):
    call_count = {"n": 0}

    def fake_run_oda(exe, in_dir, out_dir):
        call_count["n"] += 1
        for dwg in list(in_dir.glob("*.dwg")) + list(in_dir.glob("*.DWG")):
            (out_dir / dwg.name).with_suffix(".dxf").write_text("fake dxf")

        class FakeProc:
            stdout = ""
            stderr = ""

        return FakeProc()

    monkeypatch.setattr(oda_converter, "_run_oda", fake_run_oda)

    config = _fake_config(tmp_path)
    dwg = _make_dwg(tmp_path, "D-101.dwg")
    cache = ConversionCache(config.cache_dir, tmp_path / "source")
    oda_converter.ensure_converted([dwg], config, cache)
    assert call_count["n"] == 1

    dwg.absolute_path.write_bytes(b"changed content, different size!!")
    stat = dwg.absolute_path.stat()
    modified_dwg = DiscoveredFile(
        relative_path=dwg.relative_path,
        absolute_path=dwg.absolute_path,
        kind=FileKind.DWG,
        size=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
    )

    cache2 = ConversionCache(config.cache_dir, tmp_path / "source")
    oda_converter.ensure_converted([modified_dwg], config, cache2)
    assert call_count["n"] == 2
