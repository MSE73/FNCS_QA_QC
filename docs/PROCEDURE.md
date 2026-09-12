# FNCS-QAQC-SOP-01 — Drawing Submission QA/QC Procedure

**Rev 0 — 2026-09-10 — Initial issue (Phase 1 scope)**

## 1. Purpose

Define a standard, repeatable procedure for running the `fncsqaqc` command-line tool
against a project's drawing submission folder before it goes to senior review / the
client, so drawing-cleanliness and completeness issues are caught automatically
instead of relying on manual review alone.

## 2. Scope

Applies to AutoCAD DWG/DXF submissions. `.rvt` (Revit) files are discovered and
logged but not checked — this is a Phase 1 limitation, see §8. Code-compliance
calculations (ventilation, HVAC loads, water/rain tank sizing, drainage slopes,
manholes, pipe velocity, duct sizing per Jordanian code / SBC) are **out of scope**
until Phase 2 — continue reviewing these manually as today.

## 3. Roles

- **Drafter / Junior Engineer** — runs the tool against their own submission before
  marking work complete; fixes flagged issues in AutoCAD; re-runs until clean or
  until remaining items are understood and flagged to the senior.
- **Senior Engineer (QA/QC reviewer)** — reviews the report's `Summary` sheet before
  sign-off; decides whether any outstanding WARN/FAIL items are acceptable
  exceptions; owns and maintains the firm-wide Layer & Text Style standard workbook.

## 4. One-time setup (per machine)

1. Install Python 3.11+.
2. Install [ODA File Converter](https://www.opendesign.com/guestfiles/oda_file_converter)
   (free) — converts DWG → DXF without needing AutoCAD installed.
3. From the repo: `pip install pipx` then `pipx install .`
4. Point the tool at the ODA install, in order of precedence: `--oda-path` flag >
   `FNCSQAQC_ODA_PATH` env var > `oda_converter_path` in
   `%APPDATA%\fncsqaqc\config.toml` > default install-path glob (auto-detected if
   installed to the default location — usually no action needed).
5. Confirm the install: `fncsqaqc check --help`

## 5. Required inputs

| Input | Scope | Notes |
|---|---|---|
| `FNCS_Layer_Standard.xlsx` | Firm-wide, shared across all projects | Sheets `Layers` (`Layer Name \| Discipline \| Description \| Active`) and `TextStyles` (`Style Name \| System/Discipline \| Expected Font \| Expected Height \| Height Scales With Drawing \| Height Tolerance % \| Active`), optional `ScaleMultipliers` sheet. Senior-owned; do not edit ad hoc per project. |
| `Deliverables.xlsx` | Per project | `Category \| Item \| Expected Pattern \| Required (Y/N) \| Discipline \| Notes` |
| `DrawingsList.xlsx` | Per project | `Drawing No. \| Title \| Discipline \| Expected Filename Pattern \| Required (Y/N) \| Notes` |

Templates for all three are in `docs/excel_templates/`. Header matching is
case-insensitive and trimmed, but a missing/misnamed column fails fast with the
exact sheet and column name.

## 6. Procedure

1. Open a terminal in a **working folder that is not the submission folder itself**
   — the submission folder is often exactly what gets zipped and sent to the
   client, so the report and conversion cache must never land inside it. The report
   defaults to the current working directory; the cache defaults to the platform
   user cache dir.
2. Run:
   ```
   fncsqaqc check "D:\Projects\ProjectX\Submission" ^
       --layers-excel "D:\Standards\FNCS_Layer_Standard.xlsx" ^
       --deliverables-excel "D:\Projects\ProjectX\Deliverables.xlsx" ^
       --drawings-excel "D:\Projects\ProjectX\DrawingsList.xlsx"
   ```
3. First run against a folder converts every DWG via ODA (slower); later runs cache
   conversions and only reconvert files that changed since the last run. Use
   `--no-cache` to force a full reconversion if a cached DXF is suspected stale.
4. Read the console pass/warn/fail summary printed at the end of the run.
5. Open the generated `QAQC_Report_<folder>_<timestamp>.xlsx` (or the path passed
   via `--output`).
6. Work through the report sheet by sheet: `LayerCompliance`, `TextStyleFonts`,
   `TextHeights`, `PurgeUnusedResources`, `FolderDeliverables`, `DrawingsList`
   (includes an Unexpected/Unlisted block for discovered files matching no expected
   row), `ConversionLog`, `Errors`.
7. Fix flagged drawings in AutoCAD, save, and re-run the same command — the cache
   means only changed files get reconverted, so repeat runs are fast.
8. Repeat until the FAIL count is zero, or every remaining FAIL has a documented,
   senior-approved reason (see §7).
9. Senior reviews the `Summary` sheet and signs off; submission proceeds.

## 7. Severities and exceptions

- **FAIL** — must be fixed, or explicitly waived by the senior with a reason
  recorded in the project's QA log before submission proceeds.
- **WARN** — should be reviewed; does not block submission by default
  (`--fail-on` defaults to `fail`, meaning only FAIL rows affect the exit code —
  pass `--fail-on warn` to gate on warnings too, e.g. in a script).
- **INFO** — informational only (e.g. `.rvt` files logged as "deferred — not yet
  checked").

To disable a specific check for a run, use `--disable-check <id>` (repeatable).
This must be senior-approved and the reason recorded manually in the project's QA
log — the tool does not log a reason for you. Run with an invalid id to see the
list of valid check ids in the error message.

An opt-in, heuristic equipment-tagging check (item 12: every equipment tagged +
present in an equipment schedule) is available via `--enable-equipment-tag-check`;
it is off by default because tags today are plain TEXT/MTEXT, not attributed
blocks, and there is no strict current standard to check against.

## 8. Known limitations (defer to Phase 2)

- **Code compliance** (ventilation, HVAC load, tank sizing, drainage, duct sizing,
  SBC) is not automated. Continue the current manual review process. This is
  blocked on standardizing calc inputs (today an unstandardized mix of
  Excel/PDF/HAP/Elite exports).
- **Revit (.rvt)** files are discovered and listed in the report as "deferred," but
  no content checks run against them.

## 9. Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| Exits immediately, "ODA File Converter not found" | ODA not installed, or not at a discoverable path | Install ODA, or pass `--oda-path` / set `FNCSQAQC_ODA_PATH` / set it in `%APPDATA%\fncsqaqc\config.toml` |
| Excel load error naming a sheet/column | Input workbook header renamed, reordered, or sheet missing | Fix the header in the named sheet/column to match §5; re-run |
| Row in `ConversionLog` marked "needed repair" | DWG has structural corruption; `ezdxf.recover` fallback kicked in | Open and re-save the DWG in AutoCAD, then re-run |
| Row in `Errors` sheet | A specific file failed to open even after repair-fallback | Open the file directly in AutoCAD to diagnose; the run still completed for all other files |
| A layer/drawing you know is compliant shows FAIL | Firm standard workbook may be out of date, or filename pattern in `DrawingsList.xlsx` doesn't match actual naming | Check with the senior owner of `FNCS_Layer_Standard.xlsx` before assuming the drawing is wrong |

## 10. Revision history

| Rev | Date | Description |
|---|---|---|
| 0 | 2026-09-10 | Initial issue — Phase 1 (drawing cleanliness + folder/deliverables completeness) |
| 1 | 2026-09-12 | Real-folder acceptance test run against a live submission (F12-04-233 Bashar Villa, Mechanical Package). Found and fixed a crash on AutoCAD extension entities (e.g. `ARCALIGNEDTEXT`) in the purge/reference scanner. Also surfaced a firm-wide layer-naming drift — see §11. |

## 11. Known issue: layer-naming standard vs. current practice

The acceptance-test run against F12-04-233 flagged ~800 layer-name FAILs. Sampling
real drawings (via this tool's own ODA/ezdxf pipeline) from three independent recent
projects — F12-04-233 (2026-08), Juniors Zarka (2025-10), Al Muttran School
(2024-11) — showed this is not project-specific drafting error: mechanical layer
naming firm-wide has drifted from the written standard's underscore style
(`M_HVAC_2_DUT-HD`) to a hyphen, one-layer-per-object style (`M-HVAC-DUCT-12`)
sometime between early 2023 and late 2024, and has stayed that way since. The
master AutoCAD template (`MEP - Sharing\CAD Standard\MECHANICAL STANDARD.dwg`)
still uses the old underscore convention as of a March 2026 edit.

`FNCS_CAD_Layers.ods` has been updated (2026-09-12) to accept the well-evidenced
hyphen-style mechanical layer names as alternates alongside the existing
underscore rows — neither convention fails compliance for now. Deliberately NOT
accepted: color/linetype for the numbered-instance layers (observed to vary
per-instance, not a real standard), plumbing hyphen names (too inconsistent
across projects to bless yet), and a third `M1-`/`M2-`/.../`M5-` scale-fused-prefix
variant also seen in current drawings. **Open decision for the senior owner:**
whether to formally adopt the hyphen/per-object convention firm-wide (and update
the master template + retrain), revert practice to the written standard, or
something else — this file update only stops the tool from flagging what's
already normal practice; it doesn't resolve which convention is "correct."
