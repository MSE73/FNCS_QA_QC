"""Desktop GUI front-end for the `fncsqaqc check` command.

Wraps the CLI as a subprocess (python -m fncsqaqc.cli check ...) rather than
calling the pipeline directly, so this stays a thin front-end: argument
validation, Excel-loading errors, and exit-code rules all live in cli.py and
don't need to be duplicated here.
"""
from __future__ import annotations

import datetime as dt
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from fncsqaqc.checks.registry import CHECKS
from fncsqaqc.gui_settings import load_firm_wide_paths, save_firm_wide_paths

FAIL_ON_CHOICES = ["fail", "warn", "none"]


class PathRow:
    """A labeled entry + Browse button for a file or folder path."""

    def __init__(self, parent: tk.Widget, row: int, label: str, *, mode: str, filetypes=None) -> None:
        self.mode = mode
        self.filetypes = filetypes or [("Excel files", "*.xlsx *.xlsm"), ("All files", "*.*")]
        self.var = tk.StringVar()

        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
        entry = ttk.Entry(parent, textvariable=self.var, width=60)
        entry.grid(row=row, column=1, sticky="ew", pady=2)
        ttk.Button(parent, text="Browse...", command=self._browse).grid(row=row, column=2, padx=(6, 0), pady=2)

    def _browse(self) -> None:
        if self.mode == "folder":
            path = filedialog.askdirectory(title="Select folder")
        elif self.mode == "save":
            path = filedialog.asksaveasfilename(title="Save report as", defaultextension=".xlsx",
                                                 filetypes=[("Excel workbook", "*.xlsx")])
        else:
            path = filedialog.askopenfilename(title="Select file", filetypes=self.filetypes)
        if path:
            self.var.set(path)

    def get(self) -> str:
        return self.var.get().strip()


class FncsQaQcGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("FNCS QA/QC Checker")
        root.geometry("900x720")

        self._proc: subprocess.Popen | None = None
        self._log_queue: queue.Queue[str] = queue.Queue()
        self._pending_report_path: Path | None = None

        container = ttk.Frame(root)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)
        self.scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        container.grid_rowconfigure(0, weight=3)

        self.scroll_frame.columnconfigure(1, weight=1)
        self._build_required_section()
        self._build_compliance_section()
        self._build_options_section()
        self._build_advanced_section()

        self._build_run_bar(container)
        self._build_log_pane(container)

        self._load_firm_wide_defaults()
        self.root.after(100, self._drain_log_queue)

    def _firm_wide_rows(self) -> dict[str, PathRow]:
        return {
            "layers_excel": self.layers_row,
            "velocity_limits_excel": self.velocity_limits_row,
            "slope_limits_excel": self.slope_limits_row,
            "manhole_limits_excel": self.manhole_limits_row,
            "calc_checklist_excel": self.calc_checklist_row,
            "calc_consistency_excel": self.calc_consistency_row,
        }

    def _load_firm_wide_defaults(self) -> None:
        saved = load_firm_wide_paths()
        for key, row in self._firm_wide_rows().items():
            value = saved.get(key)
            if value and Path(value).is_file():
                row.var.set(value)

    def _save_firm_wide_defaults(self) -> None:
        save_firm_wide_paths({key: row.get() for key, row in self._firm_wide_rows().items()})

    # -- sections ---------------------------------------------------------

    def _build_required_section(self) -> None:
        frame = ttk.LabelFrame(self.scroll_frame, text="1. Submission folder & required standards")
        frame.pack(fill="x", pady=(0, 8))
        frame.columnconfigure(1, weight=1)

        self.folder_row = PathRow(frame, 0, "Submission folder", mode="folder")
        self.layers_row = PathRow(frame, 1, "Layer standard Excel *", mode="file")
        self.deliverables_row = PathRow(frame, 2, "Deliverables list Excel", mode="file")
        self.drawings_row = PathRow(frame, 3, "Drawings list Excel", mode="file")
        ttk.Label(
            frame, text="* Firm-wide reference files are remembered automatically -- "
            "no need to browse for them again next run.",
            foreground="#666666",
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(4, 0))

    def _build_compliance_section(self) -> None:
        outer = ttk.LabelFrame(self.scroll_frame, text="2. Code-compliance checks (optional, per project)")
        outer.pack(fill="x", pady=(0, 8))
        outer.columnconfigure(0, weight=1)

        self.compliance_enabled = tk.BooleanVar(value=False)
        toggle = ttk.Checkbutton(
            outer, text="Enable code-compliance audit", variable=self.compliance_enabled,
            command=self._toggle_compliance_fields,
        )
        toggle.grid(row=0, column=0, sticky="w", pady=(2, 6))

        self.compliance_frame = ttk.Frame(outer)
        self.compliance_frame.grid(row=1, column=0, sticky="ew")
        self.compliance_frame.columnconfigure(1, weight=1)

        self.velocity_row = PathRow(self.compliance_frame, 0, "Velocity sizing (per-project)", mode="file")
        self.velocity_limits_row = PathRow(self.compliance_frame, 1, "Velocity limits (firm-wide) *", mode="file")
        self.slope_row = PathRow(self.compliance_frame, 2, "Drainage slope sizing (per-project)", mode="file")
        self.slope_limits_row = PathRow(
            self.compliance_frame, 3, "Drainage slope limits (firm-wide) *", mode="file"
        )
        self.equipment_sizing_row = PathRow(self.compliance_frame, 4, "Equipment sizing (per-project)", mode="file")
        self.manhole_row = PathRow(self.compliance_frame, 5, "Manhole sizing (per-project)", mode="file")
        self.manhole_limits_row = PathRow(
            self.compliance_frame, 6, "Manhole size limits (firm-wide) *", mode="file"
        )
        self.calc_file_row = PathRow(
            self.compliance_frame, 7, "Calc source document (.pdf/.xlsx)", mode="file",
            filetypes=[("Calc documents", "*.pdf *.xlsx *.xlsm"), ("All files", "*.*")],
        )
        self.calc_checklist_row = PathRow(
            self.compliance_frame, 8, "Load-calc checklist (firm-wide) *", mode="file"
        )
        self.calc_consistency_row = PathRow(
            self.compliance_frame, 9, "Calc consistency rules (firm-wide) *", mode="file"
        )
        ttk.Label(
            self.compliance_frame,
            text="* Firm-wide reference files are remembered automatically -- "
            "no need to browse for them again next run.",
            foreground="#666666",
        ).grid(row=10, column=0, columnspan=3, sticky="w", pady=(4, 0))
        self._toggle_compliance_fields()

    def _toggle_compliance_fields(self) -> None:
        state = "normal" if self.compliance_enabled.get() else "disabled"
        for child in self.compliance_frame.winfo_children():
            child.configure(state=state)

    def _build_options_section(self) -> None:
        frame = ttk.LabelFrame(self.scroll_frame, text="3. Options")
        frame.pack(fill="x", pady=(0, 8))
        frame.columnconfigure(1, weight=1)

        self.equipment_tag_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, text="Enable equipment-tag reconciliation check", variable=self.equipment_tag_var
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=2)

        self.no_cache_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, text="Force reconversion of every DWG (ignore cache)", variable=self.no_cache_var
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=2)

        ttk.Label(frame, text="Fail build on").grid(row=2, column=0, sticky="w", pady=2)
        self.fail_on_var = tk.StringVar(value="fail")
        ttk.Combobox(
            frame, textvariable=self.fail_on_var, values=FAIL_ON_CHOICES, state="readonly", width=10
        ).grid(row=2, column=1, sticky="w", pady=2)

        self.report_row = PathRow(frame, 3, "Report output path (optional)", mode="save")

        ttk.Label(frame, text="Disable checks:").grid(row=4, column=0, sticky="nw", pady=(6, 2))
        checks_frame = ttk.Frame(frame)
        checks_frame.grid(row=4, column=1, columnspan=2, sticky="w")
        self.disable_check_vars: dict[str, tk.BooleanVar] = {}
        for i, spec in enumerate(CHECKS):
            var = tk.BooleanVar(value=False)
            self.disable_check_vars[spec.id] = var
            ttk.Checkbutton(checks_frame, text=f"{spec.name} ({spec.id})", variable=var).grid(
                row=i, column=0, sticky="w"
            )

    def _build_advanced_section(self) -> None:
        frame = ttk.LabelFrame(self.scroll_frame, text="Advanced (leave blank to use defaults)")
        frame.pack(fill="x", pady=(0, 8))
        frame.columnconfigure(1, weight=1)

        self.oda_path_row = PathRow(frame, 0, "ODA File Converter .exe", mode="file",
                                     filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        self.cache_dir_row = PathRow(frame, 1, "Cache directory", mode="folder")
        self.config_row = PathRow(frame, 2, "Project config.toml", mode="file",
                                   filetypes=[("TOML", "*.toml"), ("All files", "*.*")])

    def _build_run_bar(self, parent: ttk.Frame) -> None:
        bar = ttk.Frame(parent)
        bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 4))

        self.run_button = ttk.Button(bar, text="Run check", command=self._on_run)
        self.run_button.pack(side="left")
        self.cancel_button = ttk.Button(bar, text="Cancel", command=self._on_cancel, state="disabled")
        self.cancel_button.pack(side="left", padx=(6, 0))
        self.open_report_button = ttk.Button(
            bar, text="Open report", command=self._on_open_report, state="disabled"
        )
        self.open_report_button.pack(side="left", padx=(6, 0))

        self.progress = ttk.Progressbar(bar, mode="indeterminate", length=150)
        self.progress.pack(side="left", padx=(12, 0))

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(bar, textvariable=self.status_var).pack(side="left", padx=(12, 0))

    def _build_log_pane(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Output")
        frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        parent.grid_rowconfigure(2, weight=2)
        parent.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(frame, height=14, wrap="word", state="disabled", font=("Consolas", 9))
        log_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

    # -- run / cancel -------------------------------------------------------

    def _on_run(self) -> None:
        folder = self.folder_row.get()
        layers = self.layers_row.get()
        deliverables = self.deliverables_row.get()
        drawings = self.drawings_row.get()
        missing = [
            name for name, val in [
                ("Submission folder", folder),
                ("Layer standard Excel", layers),
                ("Deliverables list Excel", deliverables),
                ("Drawings list Excel", drawings),
            ] if not val
        ]
        if missing:
            messagebox.showerror("Missing required fields", "Please set:\n- " + "\n- ".join(missing))
            return

        self._save_firm_wide_defaults()

        argv = [sys.executable, "-m", "fncsqaqc.cli", "check", folder,
                "--layers-excel", layers,
                "--deliverables-excel", deliverables,
                "--drawings-excel", drawings]

        report_path = self.report_row.get()
        if not report_path:
            timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = str(Path(folder).parent / f"QAQC_Report_{Path(folder).name}_{timestamp}.xlsx")
        argv += ["--output", report_path]
        self._pending_report_path = Path(report_path)

        if self.compliance_enabled.get():
            pairs = [
                (self.velocity_row, "--velocity-excel"),
                (self.velocity_limits_row, "--velocity-limits-excel"),
                (self.slope_row, "--slope-excel"),
                (self.slope_limits_row, "--slope-limits-excel"),
                (self.equipment_sizing_row, "--equipment-sizing-excel"),
                (self.manhole_row, "--manhole-excel"),
                (self.manhole_limits_row, "--manhole-limits-excel"),
                (self.calc_file_row, "--calc-file"),
                (self.calc_checklist_row, "--calc-checklist-excel"),
                (self.calc_consistency_row, "--calc-consistency-excel"),
            ]
            for row, flag in pairs:
                value = row.get()
                if value:
                    argv += [flag, value]

        if self.equipment_tag_var.get():
            argv.append("--enable-equipment-tag-check")
        if self.no_cache_var.get():
            argv.append("--no-cache")
        argv += ["--fail-on", self.fail_on_var.get()]

        for check_id, var in self.disable_check_vars.items():
            if var.get():
                argv += ["--disable-check", check_id]

        if self.oda_path_row.get():
            argv += ["--oda-path", self.oda_path_row.get()]
        if self.cache_dir_row.get():
            argv += ["--cache-dir", self.cache_dir_row.get()]
        if self.config_row.get():
            argv += ["--config", self.config_row.get()]

        self._clear_log()
        self._append_log(f"Running: {' '.join(argv)}\n\n")
        self.run_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.open_report_button.configure(state="disabled")
        self.status_var.set("Running...")
        self.progress.start(12)

        threading.Thread(target=self._run_subprocess, args=(argv,), daemon=True).start()

    def _run_subprocess(self, argv: list[str]) -> None:
        try:
            self._proc = subprocess.Popen(
                argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
            )
            assert self._proc.stdout is not None
            for line in self._proc.stdout:
                self._log_queue.put(line)
            returncode = self._proc.wait()
        except OSError as exc:
            self._log_queue.put(f"\nFailed to launch: {exc}\n")
            returncode = -1
        self._log_queue.put(("__DONE__", returncode))

    def _on_cancel(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
            self._append_log("\nCancelled by user.\n")

    def _on_open_report(self) -> None:
        if self._pending_report_path and self._pending_report_path.exists():
            os.startfile(self._pending_report_path)  # noqa: S606 -- Windows-only tool

    # -- log queue polling ---------------------------------------------------

    def _drain_log_queue(self) -> None:
        try:
            while True:
                item = self._log_queue.get_nowait()
                if isinstance(item, tuple) and item[0] == "__DONE__":
                    self._on_run_finished(item[1])
                else:
                    self._append_log(item)
        except queue.Empty:
            pass
        self.root.after(100, self._drain_log_queue)

    def _on_run_finished(self, returncode: int) -> None:
        self.progress.stop()
        self.run_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        if returncode == 0:
            self.status_var.set("Passed.")
        elif returncode == 2:
            self.status_var.set("Setup error (see output above).")
        else:
            self.status_var.set("Completed with FAIL/WARN findings.")
        if self._pending_report_path and self._pending_report_path.exists():
            self.open_report_button.configure(state="normal")

    def _append_log(self, text: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")


def main() -> None:
    root = tk.Tk()
    FncsQaQcGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
