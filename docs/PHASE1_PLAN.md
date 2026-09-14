# FNCS QA/QC CLI — Phase 1 Plan

## Context

FNCS is a small MEP design firm (mostly junior engineers, one part-time senior, plus the user who is senior/part-time). Work is produced mainly in AutoCAD (DWG), occasionally Revit. Today, drawing cleanliness and deliverable completeness are checked manually before a senior signs off and the project goes to the client — this is slow and inconsistent across junior engineers.

The goal is a **command-line tool** the user runs against a project's submission folder that automatically catches:
- **Drawing cleanliness** issues (wrong fonts/text styles per system, wrong text heights, un-purged/unused resources, non-standard layer names)
- **Submission completeness** issues (missing calculations, drawings, specs, BOQs, preambles vs. what's required)

No web UI, no database, no run history — each invocation is a stateless one-shot check that reads a folder and a few firm-maintained Excel reference files, and produces a report.

**Scope decision (confirmed with user):** the firm's technical code-compliance review (Jordanian codes: ventilation/HVAC load calcs, water tank sizing, drainage slopes, manholes, pipe velocity, duct sizing; SBC compliance) is a much larger effort — calc sources today are an unstandardized mix of Excel, PDF exports, and tools like HAP/Elite. That entire category is **deferred to Phase 2**. This plan (Phase 1) covers only Drawing Cleanliness + Folder/Deliverables Completeness, built so Phase 2 slots in later without a rewrite.

**Revit note:** the user wants Revit supported eventually, but Revit has no ODA-equivalent headless library for reading `.rvt` without Revit itself installed (realistic options are a Revit add-in or the pyRevit CLI, both requiring Revit on the machine). Phase 1 therefore routes `.rvt` files through the same dispatch layer as everything else but only emits an "deferred — not yet checked" result for them, rather than building real Revit checks now. This keeps the door open without taking on Revit automation complexity in v1.

**Equipment tagging** (item 12 — every equipment tagged + present in an equipment schedule) ships as an **opt-in, disabled-by-default** check, since tags today are plain TEXT/MTEXT near equipment (not attributed blocks) and there's no strict current standard — it's heuristic (proximity text-match), not a hard drawing-cleanliness rule.

## Status (2026-09-13)

Phase 1 is implemented, tested (37 passing tests), pushed to `origin/main`, and
the real-folder acceptance gate has run and closed out (`docs/PROCEDURE.md`
§10–11). The operating procedure — roles, step-by-step usage, severity/exception
handling, troubleshooting — is in `docs/PROCEDURE.md`.

Since the acceptance run (all 2026-09-12/13, see `docs/PROCEDURE.md` for detail):
- Fixed a crash on AutoCAD extension entities (e.g. `ARCALIGNEDTEXT`) in the
  reference scanner.
- Resolved the mechanical layer-naming drift the acceptance run surfaced: hyphen
  separator adopted as the go-forward standard, per-instance-numbered layers
  rejected in favor of category layers. `FNCS_CAD_Layers.ods` rebuilt to match.
- Fixed a second bug found while re-verifying that decision: the `layer_names`
  check only skipped still-attached xref layers (`xref|layer`), not AutoCAD's
  Bind-renamed form (`xref$0$layer`) — was misattributing the architect's
  background layers to the mechanical file.
- Reassigned mechanical (37 layers), plumbing (103 layers), and fire (14
  layers) colors for a clear print hierarchy, checked against the firm's
  actual plot style table (`Mech PLOT.ctb`) rather than guessed —
  system/duct/pipe run geometry now plots bolder than its own annotation.
  Simulated a spot-check (`scratch/spot_check_render.py`, no AutoCAD/plotter
  available): rendered old-vs-new for a representative sample using the real
  CTB lineweight table baked into DXF entities — every remapped sample
  confirmed 0.13mm to 0.35mm as designed. Still not verified with one real
  AutoCAD-to-PDF/paper plot (would additionally catch viewport overrides or
  other AutoCAD-specific quirks).

- Fixed a third bug found while reviewing the acceptance run's folder-
  completeness FAILs: the `drawings_list` check only matched a required
  drawing against filenames in the folder, never the paperspace layout tabs
  inside a DWG — this firm routinely bundles several sheet numbers into one
  DWG as separate tabs (e.g. `M0101 HVAC SYSTEM-05.dwg` internally contains
  tabs `M0101`/`M0102`/`M0103`/`M0104`). 29 of the 32 "missing drawing" FAILs
  on the real project were this false positive; only 3 (`M0204`, `M0304`,
  `P0403`) were genuinely absent from any tab anywhere. `check_drawings` now
  also matches against layout tab names, sourced from the DXF already loaded
  for the per-file checks (no extra conversion/parsing cost). FAIL count on
  the real project: 278 → 249.

- Reworked the opt-in `equipment_tags` check (`--enable-equipment-tag-check`,
  still off by default) — it was previously non-functional for real use in
  two ways, both found by testing it against the real project: (1) it only
  ever compared a drawing's tags against a schedule in the *same file*, but
  this firm always keeps the schedule in its own drawing (`P0801
  SCHEDULE-01.dwg`), separate from the layout drawings that place the tags;
  (2) even after fixing that, it still found nothing, because this firm's
  schedules are native AutoCAD table objects (`ACAD_TABLE`), not TEXT/MTEXT
  on a layer named `*SCHED*` — ezdxf can't read table cells directly, but
  `entity.virtual_entities()` decomposes a table into the TEXT/MTEXT it's
  actually drawn from, which is now scanned as schedule content regardless
  of layer. `collect()` now runs per-file during the main scan (cheap, reuses
  the already-loaded doc) and `reconcile()` compares each file's tags against
  the tag/schedule sets from every file in the run. Once both fixes were in,
  the check surfaced genuinely real findings on the live project: widespread
  leading-zero tag-numbering inconsistency (drawing tag `SU-04` vs schedule
  entry `SU-4`; `EXF-01/02/03` vs `EXF-1/2/3`; `GLD-01` vs `GLD-1`; `IRRP-01`
  vs `IRRP-1`), and even inconsistency between drawings for the same
  equipment (`DHWC-1` in one file vs `DHWC-01` in another; `P0201 WATER
  SYSTEM` uses both `TWP-01` and `TWP-1` for what's clearly the same pump).
  Some remaining findings are known false positives from the tag-pattern
  regex matching non-equipment text (e.g. drawing-index codes on `M0G00 LIST
  OF DRAWING.dwg`) — expected, since this is a heuristic, not an exact check.

**Outstanding, not this tool's job:** retrain drafters off per-instance
numbering now that the master template uses hyphenated/category mechanical
layers (template itself updated 2026-09-14, see below); do the same naming-drift check for plumbing (deferred — too
inconsistent across projects so far); do one real AutoCAD plot to confirm the
new colors, now that the simulated check has de-risked it; the 3 genuinely
missing drawings (`M0204`, `M0304`, `P0403`) on the real project need producing
or a client-side scope decision, not a tool fix; the leading-zero tag-numbering
inconsistency the equipment-tag check surfaced is resolved as a standard
(2-digit zero-padded, `docs/PROCEDURE.md` §14) but not yet enforced as a hard
FAIL — that's a follow-up once drafters know the standard exists.

**2026-09-13, applied to the real master template:** the firm's actual
AutoCAD template (`MEP - Sharing\CAD Standard\MECHANICAL STANDARD.dwg`, not
this repo) still had the *old* fire layer colors — the earlier print-hierarchy
pass only ever updated this repo's `FNCS_CAD_Layers.ods` mirror. Backed up the
template (`MECHANICAL STANDARD.backup_20260913_235647.dwg`, same folder),
round-tripped it through ODA (DWG→DXF), updated the 14 `_5_PIP` fire layer
colors with `ezdxf` to match the decided mapping, converted back (DXF→DWG),
and verified layer/block/entity counts matched before replacing the original.

**2026-09-14, mechanical + plumbing colors pushed too:** same procedure,
same template (backed up again first:
`MECHANICAL STANDARD.backup_20260914_000250.dwg`). Mechanical layers in the
template still use the pre-decision underscore naming (e.g.
`M_HVAC_5_DUCT_S-HP`) — translating `name.replace('_', '-')` gives the
`FNCS_CAD_Layers.ods` name exactly (same transform `rebuild_layers_ods.py`
used originally), so each of the 37 run-geometry mechanical layers was
matched and recolored under its real template name; the 3 `*-IDEN` tag
layers from `apply_print_hierarchy.py`'s `COLOR_CHANGES` don't exist in the
template at all (newly-observed real-project layers, never part of the
master standard) and were correctly skipped. Plumbing layers already share
identical names between template and ods (no naming decision was ever made
for plumbing), so all 103 matched directly with no translation. Verified the
same way (layer/block/entity counts unchanged) before replacing. **The
template's mechanical layer *naming* (still underscore, not hyphenated) and
the plumbing naming-drift question are still open** — this only pushed
colors, not the naming-convention decision itself.

**2026-09-14, mechanical layer naming renamed to hyphenated in the template:**
closed the naming half too. ezdxf has no built-in layer-rename helper, so
this was done by hand: backed up again
(`MECHANICAL STANDARD.backup_20260914_001029.dwg`), then for each of the 71
`M_`-prefixed layers, renamed the LAYER table entry via
`name.replace('_', '-')` and updated every entity across every block
definition and layout whose `.dxf.layer` referenced the old name (only one
layer, `M_HVAC_2_GRL-S`, was actually referenced by any entity — 13 entities
inside a grille symbol block; everything else in this template is a bare
layer-table entry with zero usage, confirmed via a full entity scan across
blocks + layouts before touching anything). Checked for name collisions and
duplicate rename targets first — none. Verified after: 231 layers (unchanged
count), 0 leftover underscore `M_` names, 72 hyphenated `M-` layers (71
renamed + the pre-existing `M-XREF`), 19 blocks, colors intact, and the 13
entity references correctly repointed to the new name. The master template
now matches `FNCS_CAD_Layers.ods` on both naming and color for mechanical,
plumbing, and fire. Plumbing naming drift (deferred, too inconsistent across
projects to standardize yet) remains the only open naming question.

## Tech stack

- **Python 3.11+** (3.14.4 already on this machine)
- **ODA File Converter** (free, external Windows exe from opendesign.com, user installs once) — batch-converts DWG → DXF, driven via `subprocess`. Chosen so the tool never needs AutoCAD installed/licensed to run checks.
- **`ezdxf`** — parses the resulting DXF: layers, text styles/fonts, text heights, block/xref structure. No PURGE call exists in ezdxf, so "file is clean" is implemented as a custom reference-usage scan (see below).
- **`openpyxl`** — reads the 3 input Excel files (layers/text-styles, deliverables list, drawings list) and writes the Excel report (with pass/fail cell coloring).
- **`click`** — CLI framework (grouped commands, `--help`, `Path` validation) — chosen over argparse for maintainability and over Typer to avoid pulling in pydantic-adjacent machinery for a tool this size.
- **`rich`** — colored terminal pass/fail summary after each run.
- **`platformdirs`** — per-user config location on Windows (`%APPDATA%`) for caching the ODA install path.
- **`pytest`** — tests build synthetic DXF docs in-memory via `ezdxf.new()`, so most logic is testable with no real DWGs and no ODA/AutoCAD in the loop.
- **Packaging:** `pyproject.toml`, `hatchling` backend, `src/` layout, console-script entry point, distributed via `pipx install .` on each engineer's machine (no venv literacy required).

## Project structure

```
FNCS_QA_QC/
├── pyproject.toml
├── config/fncsqaqc.example.toml
├── docs/excel_templates/           # sample Layer/TextStyle, Deliverables, DrawingsList workbooks
├── src/fncsqaqc/
│   ├── cli.py                      # click group + `check` command
│   ├── config.py                   # resolves ODA path: flag > env > user config > project config > default glob
│   ├── pipeline.py                 # discover -> convert -> inspect -> aggregate -> report
│   ├── models.py                   # CheckResult, Severity, RunResult, FileResult
│   ├── discovery/file_classifier.py    # walk + classify by extension, dispatch table incl. .rvt
│   ├── converters/
│   │   ├── oda_converter.py        # subprocess wrapper, staging-folder logic for partial reconversion
│   │   └── conversion_cache.py     # manifest.json, staleness via size+mtime_ns
│   ├── dxf/
│   │   ├── loader.py               # ezdxf.readfile w/ ezdxf.recover fallback; never raises past this layer
│   │   └── reference_scanner.py    # single-pass "used-by" graph — the purge engine
│   ├── checks/
│   │   ├── registry.py             # CHECKS list — Phase 2 extension point
│   │   ├── dwg_layer_names.py
│   │   ├── dwg_text_style_fonts.py
│   │   ├── dwg_text_heights.py
│   │   ├── dwg_purge.py
│   │   ├── dwg_equipment_tags.py   # registered, enabled_by_default=False
│   │   └── folder_completeness.py
│   ├── revit/handler.py            # stub: routes .rvt -> INFO "deferred" result
│   ├── excelio/{layer_list,deliverables_list,drawings_list}.py
│   └── report/{workbook_builder,console_summary}.py
└── tests/
    ├── factories.py                # ezdxf.new()-based synthetic doc builders
    ├── test_reference_scanner.py
    ├── test_checks_*.py
    ├── test_oda_converter.py       # subprocess mocked
    └── test_report_workbook.py
```

## CLI design

```
fncsqaqc check FOLDER
    --layers-excel PATH            (required) approved layer names + text-style/font mapping
    --deliverables-excel PATH      (required) deliverables checklist
    --drawings-excel PATH          (required) expected drawings list
    --output PATH                  (optional) default: ./QAQC_Report_<foldername>_<timestamp>.xlsx in CWD
    --cache-dir PATH               (optional) default: platformdirs user cache dir
    --oda-path PATH                (optional) override ODA File Converter location
    --no-cache                     force full reconversion
    --enable-equipment-tag-check   opt-in stretch check
    --disable-check TEXT           repeatable, disable by check id
    --fail-on [none|warn|fail]     default=fail; controls process exit code for scripting
    -v/--verbose, -q/--quiet
```

Report and cache default to the **current working directory / user cache dir, never inside the scanned folder** — the scanned folder is often the exact thing that gets zipped and sent to the client, so an internal QA report must never land inside it by default.

## Pipeline flow

1. Resolve config (ODA path, cache dir).
2. Load the 3 Excel inputs into typed rule sets; fail fast with a specific sheet/column error on malformed input (most likely real-world failure mode, since these are hand-maintained).
3. Walk `FOLDER` recursively, classify every file by extension (DWG/DXF/RVT/PDF/XLSX/OTHER).
4. DWGs needing conversion go through `oda_converter.ensure_converted`: cache-aware — first run converts the whole folder in one ODA batch call; later runs stage only changed files (hardlink/copy) into a temp folder, convert just those, merge into the persistent cache (manifest keyed by relative path → size/mtime_ns/dxf_path).
5. Native DXFs skip conversion. RVTs route to `revit/handler.py` → INFO "deferred" row (never silently dropped).
6. Each resolved DXF loads via `ezdxf.readfile`, falling back to `ezdxf.recover.readfile` on structural errors (WARN "needed repair"); a file that still fails to open logs a FAIL row and the run **continues** to the next file.
7. `reference_scanner.scan(doc)` builds the shared used-by graph once per file (reused by the purge check).
8. Run all registered per-file checks against a shared context (doc, usage graph, rule sets, file metadata).
9. After all files: folder-level deliverables + drawings-list checks run once against the full discovered-file list.
10. Aggregate → write Excel report → print `rich` console summary → exit code per `--fail-on`.

## Phase 1 checks

- **Layer names** — compare `doc.layers` (excluding xref-bound `XREF|LAYER` names) against the approved list; case-insensitive/trimmed match; `difflib.get_close_matches` suggests the likely intended name on typos.
- **Font/text-style compliance** — per named STYLE (the firm's standard already encodes "system" as a text style, e.g. `MEP-DUCT-TAG` → `simplex.shx`): compare each style's font against the expected mapping; flag unknown styles; scan for inline `\f...;` font-override codes in MTEXT that bypass the style standard.
- **Text heights** — iterate TEXT/MTEXT in modelspace, all layouts, and nested block inserts (via `virtual_entities()` for correct world-space height); compare to expected height per style with a tolerance (default 5%); dedupe repeated identical rows with an occurrence count. Fixed-height-per-style only in Phase 1 — a scale-aware multiplier table is designed but deferred since reliably detecting "drawing scale" without a firm title-block convention is unreliable.
- **Purge/unused resources** — custom reference scan since ezdxf has no PURGE: layers/styles/linetypes/blocks/dimstyles are "used" if referenced anywhere (entities, block definitions, VIEWPORT frozen-layer lists, DIMSTYLE references), with reserved names (`0`, `Defpoints`, `Standard`, `Continuous`, `ByLayer`, `ByBlock`) always kept and anonymous/xref/layout blocks excluded from reporting as noise.
- **Folder/deliverables completeness** — deliverables checklist matched by glob pattern per category (calcs/drawings/specs/BOQ/preambles); drawings list matched per drawing number, reporting both Missing (required, unmatched) and Unexpected/Unlisted (discovered drawing files matching no expected row).
- **Equipment tagging** (opt-in) — regex-match TEXT/MTEXT near equipment INSERTs, cross-reference against an equipment schedule TABLE or Excel.

## Excel input schemas

**Layers & Text Styles workbook** (`--layers-excel`, firm-wide standard, reused across projects):
- Sheet `Layers`: `Layer Name | Discipline | Description | Active (Y/N)`
- Sheet `TextStyles`: `Style Name | System/Discipline | Expected Font | Expected Height | Height Scales With Drawing (Y/N) | Height Tolerance % | Active (Y/N)`
- Sheet `ScaleMultipliers` (optional): `Drawing Scale | Multiplier`

**Deliverables checklist** (`--deliverables-excel`, per project): `Category | Item | Expected Pattern | Required (Y/N) | Discipline | Notes`

**Drawings list** (`--drawings-excel`, per project): `Drawing No. | Title | Discipline | Expected Filename Pattern | Required (Y/N) | Notes`

Every loader does case-insensitive/trimmed header matching and raises a specific error naming the exact sheet/column on mismatch.

## Report schema (Excel output)

`Summary` (run metadata, per-category counts, color-filled rollup) · `LayerCompliance` · `TextStyleFonts` · `TextHeights` · `PurgeUnusedResources` · `FolderDeliverables` · `DrawingsList` (+ Unexpected/Unlisted block) · `ConversionLog` · `Errors` · `CodeCompliance` (empty, explicitly labeled "Reserved for Phase 2"). Plus a `rich` console summary at the end of the run.

## Extension points (for later phases)

- `checks/registry.py` is a flat list of check specs — Phase 2's code-compliance checks (ventilation, HVAC load, tank sizing, drainage, manholes, velocity, duct sizing) register the same way, keyed to new file kinds (calc Excel/PDF), writing into the reserved `CodeCompliance` sheet. Requires deciding a standard calc-input template or building per-source parsers (Excel/PDF/HAP/Elite) as a Phase 2 prerequisite.
- `revit/handler.py` stub swaps for real logic (pyRevit CLI subprocess call, or a compiled add-in) as a one-file change once Revit automation is worth the investment.
- Any check can be disabled per run via `--disable-check <id>` for gradual rollout.

### Phase 2 overall scope: the technical/code-compliance audit basket (drafted 2026-09-14)

Drafted after realizing the velocity spec below had been built in isolation
without ever laying out the rest of Phase 2 as a list — easy to lose the
forest for the trees across sessions on a project this long-running.
Restating the intended three-tier structure of the whole tool, since it's
the frame everything else hangs off:

1. **Drafting cleanliness** — done, shipped (Phase 1): layer names/colors,
   text style/font/height compliance, purge/unused resources.
2. **Equipment has schedules** — done, shipped (Phase 1, `equipment_tags`):
   every tag placed on a drawing cross-referenced against the project's
   `ACAD_TABLE` schedules.
3. **Technical audit** — the senior-engineer sign-off review: load calcs,
   equipment sizing, duct/pipe sizing, manhole sizing, and levels/slopes.
   This is "Phase 2" and, before this drafting pass, only had one sub-item
   (velocity) actually spec'd. The rest is scoped below.

**Five sub-checks, scoped individually because they need genuinely
different mechanisms — this is not one check, it's a basket:**

| # | Sub-check | Mechanism | Code basis status | Built? |
|---|---|---|---|---|
| 1 | Duct/pipe velocity | Sizing-summary Excel (flow+size) vs. reference table | Decided (ASHRAE/SMACNA/ASPE/NFPA) | Reference table only |
| 2 | Drainage slope/levels | Sizing-summary Excel (invert levels+length) vs. min-slope table | Not researched yet, but IPC-style min-slope-by-diameter tables are well-published — low risk | Not started |
| 3 | Equipment sizing vs. calc | Sizing-summary Excel (calc-required vs. installed capacity), tag-matched | N/A (comparison, not a code table) | Not started |
| 4 | Manhole sizing | Sizing-summary Excel (manhole dims + connecting pipe sizes) vs. code table | Not researched — lowest confidence of the five | Not started |
| 5 | Load calc presence/completeness | Text/keyword search over the calc PDF/Excel itself — no drawing side at all | N/A (checklist, not numeric) | Not started |

**Why these five and not others:** this is the breakdown the user gave
directly (load, equipment sizing, duct/pipe sizing, manholes, levels) —
not independently re-derived, just decomposed into checkable mechanisms.

**#1 Duct/pipe velocity** — spec'd and reference table built below. Closest
to done; finish this one first since the sizing-summary Excel it needs is
mostly shared infrastructure the others can reuse.

**#2 Drainage slope/levels** — a pipe run's slope (invert drop ÷ horizontal
length) must clear a minimum self-cleansing gradient — same physical
principle as the 0.6 m/s minimum already in `VelocityLimits.xlsx`'s
Drainage row, just expressed as slope instead of velocity (IPC-style
tables publish minimum slope by pipe diameter directly, e.g. commonly
cited 2% for 4", 1% for 6"+ — not yet verified via research the way the
velocity table was). Manhole invert *drops* (minimum elevation change
required across a manhole when pipe size changes) are a related but
separate code value, also not yet researched. Mechanically this is the
closest sibling to #1 — same sizing-summary-Excel-vs-reference-table
shape, could plausibly share one input file and one code-basis table with
velocity rather than being a fully separate check. Recommended as the
**second** build target, right after velocity, because the pattern is
already proven and the code basis looks low-risk to source.

**#3 Equipment sizing vs. calc** — distinct from velocity: this asks "does
the installed unit meet the calc's required capacity," not "is the flow
velocity in range." Reuses the tag-matching infrastructure already built
for `equipment_tags` (same fragility already known: leading-zero drift,
tags that don't match cleanly between sources — see `docs/PROCEDURE.md`
§13/§14). No code-basis research needed (it's a direct calc-vs-drawing
comparison, not a published limit), so this could plausibly be **built
before** #2/#4 if the user wants a quicker win, at the cost of not
reusing the slope/velocity code-basis-table pattern.

**#4 Manhole sizing** — lowest confidence: no code basis researched yet,
and unclear whether manhole dimensions are even captured in a schedule
today (unlike pumps/tanks, which the `equipment_tags` work confirmed exist
as `ACAD_TABLE` schedules on this firm's drawings) or only as annotation
text. **Needs a firm-side check** (does the user have manhole schedules on
real projects at all?) before this can be spec'd concretely — recommended
**last** among the four sizing-summary-style checks, pending that answer.

**#5 Load calc presence/completeness** — mechanically unlike the other
four: no drawing side, no sizing-summary Excel, no numeric comparison. It
formalizes what was already done manually in `docs/PROCEDURE.md`'s
follow-up #5 (F12-04-233 calc review) — search the calc PDF/Excel's text
for expected section headers/content (weather data, zone-level loads,
system input/output, tank-capacity derivation, pump head+flow) and flag
what's missing, the same way that manual review found HAP's weather-data
and system-level reports absent. Does **not** re-derive or verify the load
numbers themselves (out of scope — would mean independently re-running the
load calc, unrealistic). Because it needs none of the shared
sizing-summary infrastructure, this could be built **in parallel** with
any of #1-#4 rather than strictly sequenced after them.

**Consolidation to decide before building #2-#4:** each of #1-#4 wants a
per-project "sizing summary" Excel with a similar Tag/Type/System/values
shape. Worth deciding whether that's one unified workbook (multiple
sheets: Velocity, Slope, EquipmentSizing, Manholes) that the engineer fills
in once, or separate files per check — one workbook is almost certainly
better for the engineer filling it in (one place, not four), but it's a
CLI/schema decision, not just a content one, worth confirming before #2 is
built so #1 doesn't need reworking right after.

**Proposed build order:** #1 (finish velocity) → #2 (slope/levels, same
pattern, code basis needs a quick research pass) → #3 (equipment sizing,
no code-basis research needed) → #4 (manholes, pending the schedule-format
check) → #5 (load-calc presence, can slot in anytime, lowest coupling to
the rest). Each gated by the same F12-04-233 real-project acceptance test
Phase 1 used, not released to junior engineers individually as each lands.

### Phase 2 spec: duct/pipe velocity check (drafted 2026-09-14; reference table built 2026-09-14)

**Build status:** the firm-wide velocity-limit reference table described
below is built — `docs/excel_templates/VelocityLimits.xlsx`, sourcing
documented in `docs/PROCEDURE.md` §15. The sizing-summary Excel input and
the check module itself are still not built (next steps).

Scoped in more detail after this session's manual review of F12-04-233 found
no velocity verification anywhere in that project's calc package (see
`docs/PROCEDURE.md`'s calc-review note) — this is the first Phase 2 item
worth designing concretely rather than leaving as a one-line deferral.

**The core problem:** verifying velocity needs two numbers per run — a
design flow rate and an installed size — and today those live in different,
disconnected places. Flow rate comes from whatever calc source the engineer
used (HAP export, a pump-duty PDF, a spreadsheet — unstandardized per
§Scope decision above). Installed size sometimes exists on the drawing side
as a schedule (this session's `equipment_tags` work proved `ACAD_TABLE`
schedules can be read via `entity.virtual_entities()` — e.g. the real
project's Pumps Schedule has a `FLOW (L/S)` column, and other schedules list
diameters), but schedule columns and coverage aren't standardized across
disciplines or projects, and — as the equipment-tag leading-zero findings
showed — tag names between calc and drawing don't always match cleanly
either. Auto-deriving both flow and size reliably from arbitrary sources is
not realistic as a first cut.

**Proposed MVP: a structured sizing-summary input, not auto-parsing.**
Mirrors how `Deliverables.xlsx`/`DrawingsList.xlsx` already work — a
per-project Excel the engineer fills in (they already have this data from
their own calc; this just asks them to summarize it in one place) rather
than the tool trying to extract it from HAP/PDF/schedule sources directly:

| Tag | Type (duct/pipe) | System | Design Flow (L/s) | Installed Size | Notes |
|---|---|---|---|---|---|

The check computes velocity from flow ÷ cross-sectional area (duct WxH or
pipe Ø) and compares against a **firm-wide velocity-limit reference table**
(by type + system category — supply/return/exhaust duct, domestic
cold/hot water, drainage self-cleansing minimum, fire protection, etc.),
analogous to how `FNCS_Layer_Standard.xlsx` is the senior-owned firm-wide
reference today.

**Code basis decided: ASHRAE/SMACNA (duct), ASPE Data Book / IPC (piping),
as the default numeric source.** Reasoning: Jordan's own national codes in
this area — the National Building Council's Mechanical Ventilation & A/C
Code (1988) and Natural Ventilation & Plumbing Code (1992) — are old,
narrow-scope regulatory documents; regional MEP practice (this firm's own
calc package included — it's a Carrier HAP export, an ASHRAE-methodology
tool, with no Jordanian-code reference anywhere in it) overwhelmingly relies
on ASHRAE/SMACNA/ASPE for the actual numeric design criteria rather than an
independently-authored national velocity table. **Caveat — this was not
independently verified against the literal 1988/1992 code text** (not
practically searchable/digitized); if the user or a colleague has direct
access and finds a specific mandatory Jordanian value that conflicts with
ASHRAE/SMACNA for a given category, that value should override the default.
This is exactly why the reference table is planned as a firm-owned, editable
Excel input rather than a hardcoded constant — swapping in a Jordan-specific
number later is a data edit, not a code change.

**Fire protection piping gets its own code basis: NFPA, not ASHRAE/SMACNA/ASPE.**
Fire protection has its own dedicated, near-universally-used international
standard body, with specific documented numeric velocity limits (unlike the
general ASHRAE/SMACNA/ASPE decision above, these are confirmed, published
values, not an inference from regional practice):

| System (this firm's fire layer categories) | Standard | Max velocity |
|---|---|---|
| Standpipe / hydrant / landing valve / siamese connection | NFPA 14 | 20 ft/s (6.1 m/s) — mandatory |
| Fire pump suction piping (10 pipe diameters upstream of the pump) | NFPA 20 | 15 ft/s (4.6 m/s) |
| Sprinkler (branch, cross-main, drain) | NFPA 13 | No fixed limit — velocity is self-correcting under NFPA 13's required hydraulic calculation (minimum pressure/flow at the most remote head governs, not a velocity ceiling). Use FM Global's practical ceiling of 30 ft/s (9.1 m/s) only as a sanity-check bound above which Hazen-Williams itself becomes unreliable, not as a real limit to enforce. |
| Hose reel (small-bore, occupant-use — distinct from NFPA 14's larger hose-station standpipe) | **Unconfirmed** — this firm's naming (`HOSE REEL CABINET` vs `HOSE RACK CABINET`) follows the British/European convention (BS EN 671-1/671-3), not NFPA's terminology, since NFPA doesn't have a directly equivalent small-reel category. Needs confirming against BS EN 671 before a limit is set here. |

Deluge systems aren't a distinct NFPA velocity category — treat as sprinkler
piping (NFPA 13) downstream of the deluge valve. Jordan Civil Defence
enforces its own acceptance criteria (e.g. specific hydrostatic test
pressures) but design-methodology practice regionally still follows NFPA for
the actual hydraulic/velocity basis — same caveat as above applies if a
specific Civil Defence circular is later found to mandate a different value.

**Stretch goal, not MVP:** once schedule formats are more standardized,
auto-populate/cross-check the sizing summary from `ACAD_TABLE` schedules
using the same decoding approach already built for `equipment_tags`, instead
of requiring fully manual entry. Not attempted first because schedule
column layout still varies per discipline/project (as seen this session:
the Pumps Schedule has flow but not pipe size; no schedule in the real
project has both together).

**Registration:** a new check module (e.g. `checks/code_compliance_velocity.py`)
registered in `checks/registry.py` like every other check, writing FAIL
(over limit) / WARN (missing size or flow data) into the already-reserved
`CodeCompliance` report sheet. A new `--sizing-excel` CLI input, following
the same case-insensitive header-matching and fail-fast-on-schema-error
pattern as the three existing inputs.

## Testing/verification

- Unit tests build synthetic in-memory DXF docs via `ezdxf.new()` — covers layer/style/height/purge logic without any real DWG or ODA involved.
- `reference_scanner` tests specifically cover: layer used only inside a never-inserted block, layer referenced only via VIEWPORT frozen list, anonymous `*D` block, xref-bound layer name — asserting correct include/exclude per the rules above.
- `oda_converter` tests mock `subprocess.run` to verify staging/cache logic without needing the real ODA binary in dev/CI.
- `excelio` tests build throwaway `.xlsx` fixtures (valid and deliberately malformed) asserting specific, actionable schema-error messages.
- One integration test (skipped unless `FNCSQAQC_ODA_PATH` is set) runs the full CLI via `click.testing.CliRunner` against native `.dxf` fixtures.
- **Real acceptance gate:** run the finished tool against one known-messy legacy project folder and compare its findings against what the user already knows is wrong in it — synthetic fixtures validate mechanics, not real firm drawing conventions, so this manual pass is the actual go/no-go before rollout to the junior engineers.

## Rollout of this plan

Once approved: this plan is saved as `docs/PHASE1_PLAN.md` in the repo, committed, and pushed to GitHub (`origin/main`) as the first step. Implementation then proceeds automatically through the structure above (scaffolding → converters → dxf/reference scanner → checks → excelio → report → CLI wiring → tests) without pausing for approval between files, committing progress along the way; the user will be notified when Phase 1 is functional and ready for the real-folder acceptance test described in Testing/verification.

**Done:** implementation, tests, and the operating procedure (`docs/PROCEDURE.md`)
are complete and pushed. The real-folder acceptance test described above has now
run (2026-09-12, against F12-04-233 Bashar Villa's Mechanical Package): it found
and fixed a real crash bug (the reference scanner choked on AutoCAD extension
entities like `ARCALIGNEDTEXT`), completed cleanly afterward, and surfaced a
genuine firm-wide layer-naming drift between the written standard and current
drafting practice. The senior owner has since decided the go-forward mechanical
layer standard (hyphen separator, category-based, no per-instance numbering) and
`FNCS_CAD_Layers.ods` has been rebuilt to match — see `docs/PROCEDURE.md` §11.
**Remaining:** the master AutoCAD template has been updated to the new
hyphenated layer set (2026-09-14); retraining drafters off per-instance
numbering is still outside this tool's scope. Once that's done, this plan can
be considered closed and superseded by whatever Phase 2 planning follows.

## One-time setup

- Python 3.11+ (present).
- `pip install pipx` then `pipx install .` on each engineer's machine.
- Download/install ODA File Converter (free) from opendesign.com; default path glob `C:\Program Files\ODA\ODAFileConverter_*\ODAFileConverter.exe`, overridable via config/env/flag.
- No AutoCAD or Revit license required for Phase 1.
- Firm fills in `docs/excel_templates/` once: a shared `FNCS_Layer_Standard.xlsx`, plus per-project `Deliverables.xlsx` and `DrawingsList.xlsx`.
