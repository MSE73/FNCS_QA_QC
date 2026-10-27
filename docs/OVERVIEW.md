# FNCS QA/QC Tool — What It Does and How

A short brief for anyone asking "what is this tool" — engineers, IT, or
anyone outside the project who needs the gist without reading the full SOP
(`docs/PROCEDURE.md`) or design doc (`docs/PHASE1_PLAN.md`).

## What `fncsqaqc` does

It automates the manual "does this drawing package meet our standards"
review that currently happens by eye before a submission goes to the
client or to senior sign-off. It checks two kinds of things:

1. **Drawing cleanliness & completeness** (always runs) — layer naming
   against the firm standard, text style/font/height compliance, unused/
   purgeable CAD resources, and whether all required drawings and
   deliverables are actually present in the submission folder.
2. **Code-compliance technical audit** (opt-in, per project) — duct/pipe
   velocity, drainage minimum slope, equipment sizing vs. the calc,
   manhole sizing, and whether the load calc covers everything it should
   — each checked against either a firm-wide reference table (code-based
   limits) or the project's own calc document. Domestic water velocity
   limits are now confirmed against the real Jordanian plumbing code
   (`Codes/plumbing_Code.pdf`); drainage minimum slope has a known basis
   conflict against that same code, pending a senior decision — see
   `docs/PROCEDURE.md` §24.

## Running it

Either the command line (`fncsqaqc check ...`, see `README.md`) or the
desktop GUI (`fncsqaqc gui`, or the `fncsqaqc-gui` shortcut) — same checks,
same report, the GUI just wraps the CLI with file pickers, a live output
log, and an "Open report" button. The GUI remembers the firm-wide
reference files (layer standard, limit tables, checklists) between runs,
so only the per-project inputs need re-picking each time.

## How it works, step by step

1. The engineer points the tool at a project's submission folder plus a
   few Excel inputs: the firm-wide layer/text standard, a per-project list
   of required deliverables/drawings, and (if running the code-compliance
   checks) a per-project sizing-summary workbook and/or the calc PDF.
2. The tool converts every DWG in the folder to DXF (via the free ODA File
   Converter, since no AutoCAD license is needed), then reads the DXF
   content — layers, text, tables/schedules — with a Python library
   (`ezdxf`).
3. It runs each check against that data and the Excel inputs, and compares
   calc-document text against a checklist/consistency rules where
   relevant.
4. Everything gets written into one Excel report
   (`QAQC_Report_<project>_<timestamp>.xlsx`), with each check on its own
   sheet and a FAIL/WARN/INFO summary.
5. The engineer fixes anything flagged FAIL in AutoCAD, re-runs (only
   changed files get reconverted, so re-runs are fast), and repeats until
   clean or until remaining items are senior-approved exceptions.
6. The senior engineer reviews the report's summary sheet and signs off
   before the submission goes out.

It's purely local — no server, no shared database, no accounts. The only
"shared" pieces are the firm-wide standard/reference Excel files on the
network drive, which a senior engineer owns and updates as standards
evolve.
