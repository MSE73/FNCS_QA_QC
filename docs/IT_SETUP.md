# FNCS QA/QC Tool — IT Setup Guide

This is the document to hand to IT when they need to install `fncsqaqc` on an
engineer's machine. It covers what the tool is (so IT understands what
they're installing and why) and the exact one-time setup steps, in order.

## 1. What this is

`fncsqaqc` is an internal command-line tool (no web UI, no server, no
accounts) that checks MEP AutoCAD drawing submissions for QA/QC issues
before they go to the client — layer naming, text standards, folder
completeness, and code-compliance sizing checks. Each engineer runs it
locally against their own project folder; it produces an Excel report.

It needs to be installed **once per engineer's machine**. There is no
central server or network service to stand up — just a Python package and
one free external converter utility.

## 2. One-time setup, per machine

Run these in order:

1. **Install Python 3.11 or newer** (standard installer from python.org,
   with "Add to PATH" checked).
2. **Install ODA File Converter** (free):
   https://www.opendesign.com/guestfiles/oda_file_converter — this is what
   converts DWG → DXF without needing AutoCAD installed. The default
   install location is fine; the tool finds it automatically.
3. **Install the tool itself**, from a terminal, pointed at this repo:
   ```
   pip install pipx
   pipx install .
   ```
4. **Verify it worked:**
   ```
   fncsqaqc check --help
   ```
   If that prints usage text, the install is good — IT's job is done at
   that point.

If ODA isn't found automatically (rare — only if it was installed somewhere
nonstandard), the engineer sets one of: `--oda-path` flag,
`FNCSQAQC_ODA_PATH` env var, or a line in `%APPDATA%\fncsqaqc\config.toml`.
That's an engineer/senior-engineer setting, not something IT needs to
pre-configure.

## 3. Shared firm files IT should make sure are accessible

These live on the firm's shared drive (not local, not in this repo), and
every engineer's machine needs read access to them. IT's role is just
making sure the network path is reachable from each PC — not maintaining
their content:

- `FNCS_Layer_Standard.xlsx` — firm-wide layer/text standard
- `VelocityLimits.xlsx`, `DrainageSlopeLimits.xlsx`,
  `ManholeSizeLimits.xlsx`, `LoadCalcChecklist.xlsx`,
  `CalcConsistencyRules.xlsx` — firm-wide code-compliance reference tables

These are senior-engineer-owned content; IT doesn't edit them, just ensures
the share is mounted/reachable.

## 4. If something breaks

See `docs/PROCEDURE.md` §9 ("Troubleshooting") in this repo — it has a
symptom → cause → fix table covering the common install/runtime errors.
Anything not covered there should go back to the tool/standards owner
rather than IT guessing at a fix, since most failures are a missing or
misnamed Excel column, not an installation issue.
