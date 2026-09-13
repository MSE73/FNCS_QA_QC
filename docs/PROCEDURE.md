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

**`Deliverables.xlsx` granularity matters:** each row is checked independently —
its `Expected Pattern` only confirms *some* file matching that glob exists, not
that every specific item you have in mind is present. If a project has several
distinct calculations (HVAC load, drainage, water tank sizing, ...), list each
as its own row with its own pattern; bundling them into one row like
`Category=Calculations, Item=Calcs, Expected Pattern=calculation/*.pdf` only
confirms *a* PDF exists in that folder, not that each named calc is actually
there — the same blind spot §12 found and fixed for `DrawingsList`, except here
it's a matter of how the input is filled in, not a tool bug (the schema already
supports one row per item).

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
| 1 | 2026-09-12 | Real-folder acceptance test run against a live submission (F12-04-233 Bashar Villa, Mechanical Package). Found and fixed a crash on AutoCAD extension entities (e.g. `ARCALIGNEDTEXT`) in the purge/reference scanner. Also surfaced a firm-wide layer-naming drift, resolved same day — see §11. |

## 11. Resolved: mechanical layer naming standard (2026-09-12)

The acceptance-test run against F12-04-233 flagged ~800 layer-name FAILs. Sampling
real drawings (via this tool's own ODA/ezdxf pipeline) from three independent recent
projects — F12-04-233 (2026-08), Juniors Zarka (2025-10), Al Muttran School
(2024-11) — showed this was not project-specific drafting error but two firm-wide
drifts from the written standard, since early-to-late 2023:

1. **Separator style:** underscore (`M_HVAC_2_DUT-HD`) drifted to hyphen
   (`M-HVAC-DUCT-12`).
2. **Layer granularity:** the written standard's per-function categories
   (e.g. separate layers for supply/return/exhaust duct, per-grille-type,
   etc.) drifted to one layer per drawn object (`M-HVAC-DUCT-1` through
   `-40`, `M-EQPM-1` through `-10`, and similar), with color/linetype unset
   and varying per instance.

**Senior decision:** hyphen is adopted as the go-forward separator style, but
per-object numbering is rejected — layers stay category-based. `FNCS_CAD_Layers.ods`
was rebuilt accordingly (`scratch/rebuild_layers_ods.py`, not part of the shipped
tool): every mechanical (`M_`) row's name had `_` replaced with `-`, preserving the
real color/linetype/lineweight from the master template export and every
functional category from the written standard (e.g. `M_HVAC_2_DUT-HD` →
`M-HVAC-2-DUT-HD`). The 87 per-instance-numbered/duplicate rows added as the
2026-09-11 stopgap were removed — their geometry belongs on the existing
hyphenated category layers instead (duct annotation → `M-HVAC-2-TXT-1-*`;
centerlines → `M-GEN-1-CETR`; equipment → `M-GEN-2-EQUP` / `M-CONT-2-EQUP`).
Twelve genuinely new general-purpose hyphen layers observed in current practice
that the written standard had no equivalent for (`M-TEXT`, `M-REV`, `M-NODE`,
`M-CEN`, `M-DETL-GENF`, `M-DETL-PIPE`, `M-ANNO-PATT`, `M-ANNO-SYMB`, `M-HATCH`,
`M-HVAC-DUCT-IDEN`, `M-HVAC-CDFF-IDEN`, `M-EQPM-IDEN`) were kept, one row each.
Plumbing and fire layers are untouched — plumbing hyphen usage was too
inconsistent across projects to standardize yet (open item, revisit later).

**Outstanding follow-up (not done by this tool):** the master AutoCAD template
(`MEP - Sharing\CAD Standard\MECHANICAL STANDARD.dwg`, still underscore-style as of
a March 2026 edit) needs to be updated to the new hyphenated category layers, and
drafters need to be retrained off per-instance numbering. Until the template is
updated, new drawings copied from it will still seed the old underscore layers —
expect a transition period of mixed usage.

### Print-hierarchy color pass (2026-09-13)

Checking the mechanical colors against the firm's actual mechanical plot style
(`MEP - Sharing\CAD Standard\PIOT STYLE ELECTRICAL\Mech PLOT.ctb`, read with
`ezdxf.addons.acadctb`) found that 244 of 255 ACI colors plot at a flat 0.13mm —
meaning nearly every mechanical layer's carefully chosen on-screen color (e.g.
supply-duct-HP vs -LP) collapsed to the same line weight in print, while text/
hatch/xref layers plotted bolder (0.20mm) than the system geometry itself.

37 duct/pipe **run-geometry** layers (both `_5_` double-line and `_6_...-SL`
single-line variants) were remapped onto the 6 distinct bold-plotting ACI colors
this CTB has (1 red / 2 yellow / 3 green / 4 cyan / 5 blue / 11 pink), grouped by
system: supply=5, return=3, exhaust=1, fresh air=2, other duct (chimney/transfer/
dust)=11, all piping=4. Symbols, equipment, text, hatch, centerlines, and
background-reference layers were left untouched. **Trade-off accepted:** HP/LP
sub-variants within a family now share one color (e.g. supply-HP and supply-LP
are both blue) — that distinction is no longer color-coded, only tag-text-coded.
The 3 tag layers (`M-HVAC-DUCT-IDEN`, `M-HVAC-CDFF-IDEN`, `M-EQPM-IDEN`) had no
color recorded at all; they're now set to 7 (white/black) like other text layers.
`scratch/apply_print_hierarchy.py` has the full before/after mapping.

This did not change the FAIL/WARN counts from the acceptance run (color has no
bearing on the `layer_names` check) — it only affects what the drawings look like
plotted. Not verified with an actual plot (no AutoCAD/plotter in this pipeline);
worth spot-checking on paper before treating this as final.

The same pass was then done for plumbing (103 layers). Plumbing systems are
typically drawn on their own dedicated sheet (`P0101 DRAINAGE`, `P0201 WATER`,
`P0401 LPG`, ...) rather than mixed on one sheet the way HVAC duct+pipe often
are, so the color is assigned per **system**, not per subtype: Water=5(blue),
Drainage=3(green), Fuel=1(red), Medical gases=2(yellow), Steam=4(cyan), and the
lower-prevalence Ammonia/Compressed-air/Swimming-pool systems share 11(pink)
since they're unlikely to coexist on the same sheet. This also fixed two
layers (`P_AMON_5_PIP-NH3-GAS_`, `P_MGAS_5_PIP-MA7`/`MA7-DL`) that had been
using color 135 — a near-invisible 0.05mm hairline in this CTB, almost
certainly unintentional. `scratch/apply_plumbing_print_hierarchy.py` has the
full mapping. Text and insulation-overlay layers untouched, same as mechanical.

The same pass was then done for fire (24 layers, `F_FIRE_...`, checked against
the same shared `Mech PLOT.ctb`). Every fire layer's color plotted at the flat
0.13mm weight — the same collapse problem as mechanical and plumbing before
their passes. A fire-fighting layout sheet normally shows sprinkler,
hydrant/standpipe, hose reel, and deluge piping together on one plan (like
mechanical duct+pipe), not one system per sheet (like plumbing), so each
**system** got its own distinct bold color rather than sharing one: Hydrant/
standpipe (`PIP-HDR`, `PIP-LV`, `PIP-SC`, `PIP_SC-DL`)=1(red), Sprinkler
(`SP-BRN`, `SP-CMP`, `SP-DR`, `SPR-HP`, `SPR-LP`)=5(blue), Hose reel (`PIP-HR`,
`PIP_HRC`, `PIP_HRC-DL`)=3(green), Deluge (`PIP_DF`, `PIP_DF-SPR`)=2(yellow).
14 `_5_PIP` run-geometry layers were remapped; the 7 `_2_` symbol/equipment
layers and 3 `_2_TXT-` text layers were left untouched, same as mechanical and
plumbing. `scratch/apply_fire_print_hierarchy.py` has the full mapping.

**Simulated spot-check (2026-09-13):** without AutoCAD or a plotter available
in this pipeline, `scratch/spot_check_render.py` validates the three passes a
different way: it takes a representative layer from each system, looks up its
color from the git commit right before that pass (old) and from the current
sheet (new), resolves both through the same real Mech PLOT.ctb lineweight
table the passes were designed against, bakes those exact lineweights into
DXF `LINE` entities, and renders old-vs-new with ezdxf's drawing add-on so
relative thickness in the output PNG matches what the CTB defines. Every
remapped sample went from 0.13mm (old) to 0.35mm (new); the two untouched
control layers (one mechanical, one fire) were unchanged, as expected. This
confirms the color choices are correct against the actual CTB data — it is
not, however, a substitute for one real AutoCAD-to-PDF/paper plot, which
would additionally catch viewport plot-style overrides, layer freezes, or
other AutoCAD-specific quirks this simulation can't see.

## 12. Resolved: `drawings_list` check missed bundled-DWG layout tabs (2026-09-13)

Reviewing the acceptance run's 32 "folder completeness" FAILs (all in
`DrawingsList`, none in `FolderDeliverables`) against the real F12-04-233
package found the check itself was wrong, not the submission: this firm
routinely bundles several sheet numbers into one DWG as separate paperspace
layout tabs — e.g. `M0101 HVAC SYSTEM-05.dwg` has no separate files for
M0102/M0103/M0104, they're tabs inside that one DWG. `check_drawings`
(`src/fncsqaqc/checks/folder_completeness.py`) only ever matched a required
drawing's pattern against filenames in the folder, so every sheet number that
lives as a tab rather than its own file was flagged "missing."

Opening every cached DXF in `cad\MECH` and listing `doc.layouts.names_in_taborder()`
showed **29 of the 32** "missing" drawings existed as a tab somewhere; only 3
(`M0204`, `M0304`, `P0403`) were genuinely absent from any tab. Fixed by having
the pipeline (`src/fncsqaqc/pipeline.py`) collect each DXF's non-Model layout
names during the per-file check loop (the doc is already loaded, no extra
conversion cost) and passing that map into `check_drawings`, which now
matches a required drawing's pattern against layout tab names as well as
filenames. Real-project FAIL count: 278 → 249.

## 13. Reworked: equipment tag / schedule cross-check (2026-09-13)

The opt-in `equipment_tags` check (`--enable-equipment-tag-check`, still off
by default) was non-functional for real use, in two layers found by testing it
against the real project:

1. **Per-file, not project-wide.** It only compared a drawing's tags against
   a schedule found in the *same file* — but this firm always keeps the
   equipment schedule in its own drawing (`P0801 SCHEDULE-01.dwg`), separate
   from every layout drawing that actually places the tags. Fixed by
   splitting the check into `collect()` (per-file, runs during the main scan)
   and `reconcile()` (project-wide, runs once at the end and compares each
   file's tags against the tag/schedule sets gathered from every file).

2. **Schedules are AutoCAD tables, not text on a `*SCHED*` layer.** Even
   after the project-wide fix, the check still found nothing — this firm's
   schedules are native `ACAD_TABLE` entities, and there is no `*SCHED*`
   layer anywhere in the schedule drawing. ezdxf can't read table cells
   directly, but `entity.virtual_entities()` decomposes a table into the
   TEXT/MTEXT it's actually drawn from. Fixed by scanning that decomposition
   and treating any `ACAD_TABLE`'s content as schedule tags regardless of
   layer (a table only ever holds a schedule in this firm's drawings).

With both fixes in, the check surfaces real findings on the live project — a
firm-wide leading-zero tag-numbering inconsistency: drawing tag `SU-04` vs
schedule entry `SU-4`; `EXF-01/02/03` vs `EXF-1/2/3`; `GLD-01` vs `GLD-1`;
`IRRP-01` vs `IRRP-1`; and even inconsistency between two drawings for the
same equipment (`DHWC-1` vs `DHWC-01`; `P0201 WATER SYSTEM` itself uses both
`TWP-01` and `TWP-1` for what's clearly one pump). Some remaining findings are
expected false positives — the tag-pattern regex also matches non-equipment
text like drawing-index codes on `M0G00 LIST OF DRAWING.dwg` — this remains a
heuristic, not an exact check, hence still opt-in.
