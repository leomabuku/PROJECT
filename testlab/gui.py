from __future__ import annotations

from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from .runner import TestRunResult, run_test_suite


class TestLabGUI:
    def __init__(self, root: tk.Tk, project_root: Path, *, autorun: bool = False) -> None:
        self.root = root
        self.project_root = project_root
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.current_result: TestRunResult | None = None
        self.running = False

        root.title("TongaLang Failure Discovery Test Lab")
        root.geometry("1240x780")
        root.minsize(980, 640)
        root.configure(bg="#0b1020")
        self._configure_styles()
        self._build_ui()
        self._poll_events()
        if autorun:
            root.after(250, lambda: self.start_run("all"))

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#111827")
        style.configure("TLabel", background="#111827", foreground="#e5e7eb")
        style.configure("Treeview", background="#172033", fieldbackground="#172033", foreground="#e5e7eb", rowheight=27)
        style.configure("Treeview.Heading", background="#1f2937", foreground="#e5e7eb")
        style.map("Treeview", background=[("selected", "#1d4ed8")])
        style.configure("TNotebook", background="#0b1020", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1f2937", foreground="#e5e7eb", padding=(12, 7))
        style.map("TNotebook.Tab", background=[("selected", "#2563eb")])

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        header = tk.Frame(self.root, bg="#111827")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        tk.Label(header, text="TongaLang Test Lab", bg="#111827", fg="#f8fafc", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 2))
        tk.Label(header, text="Failure discovery, regression evidence, and coverage metrics", bg="#111827", fg="#94a3b8", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))
        self.status_var = tk.StringVar(value="Ready to test")
        tk.Label(header, textvariable=self.status_var, bg="#111827", fg="#93c5fd", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, rowspan=2, sticky="e", padx=18)

        controls = tk.Frame(self.root, bg="#0b1020")
        controls.grid(row=1, column=0, sticky="ew", padx=18, pady=12)
        self.run_all_button = tk.Button(controls, text="Run all tests", command=lambda: self.start_run("all"), bg="#22c55e", fg="#07130b", relief="flat", padx=16, pady=8, font=("Segoe UI", 10, "bold"))
        self.run_all_button.pack(side="left")
        self.run_weakness_button = tk.Button(controls, text="Run weakness probes", command=lambda: self.start_run("weakness"), bg="#f59e0b", fg="#1f1300", relief="flat", padx=16, pady=8, font=("Segoe UI", 10, "bold"))
        self.run_weakness_button.pack(side="left", padx=8)
        tk.Button(controls, text="Open results folder", command=self.open_results_folder, bg="#1f2937", fg="#e5e7eb", relief="flat", padx=14, pady=8).pack(side="left")
        self.progress = ttk.Progressbar(controls, mode="indeterminate", length=220)
        self.progress.pack(side="right")

        cards = tk.Frame(self.root, bg="#0b1020")
        cards.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 12))
        for column in range(7):
            cards.columnconfigure(column, weight=1)
        self.metric_vars: dict[str, tk.StringVar] = {}
        metrics = (
            ("Total", "total", "#60a5fa"),
            ("Passed", "passed", "#4ade80"),
            ("Failed", "failed", "#f87171"),
            ("Skipped", "skipped", "#cbd5e1"),
            ("Weakness probes", "weakness", "#fbbf24"),
            ("Line coverage", "coverage", "#a78bfa"),
            ("Duration", "duration", "#67e8f9"),
        )
        for column, (label, key, color) in enumerate(metrics):
            card = tk.Frame(cards, bg="#111827", highlightbackground="#263244", highlightthickness=1)
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 4, 0), ipadx=8, ipady=8)
            value = tk.StringVar(value="-")
            self.metric_vars[key] = value
            tk.Label(card, text=label, bg="#111827", fg="#94a3b8", font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(6, 0))
            tk.Label(card, textvariable=value, bg="#111827", fg=color, font=("Segoe UI", 17, "bold")).pack(anchor="w", padx=10, pady=(1, 6))

        notebook = ttk.Notebook(self.root)
        notebook.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 18))
        tests_tab = ttk.Frame(notebook)
        metrics_tab = ttk.Frame(notebook)
        output_tab = ttk.Frame(notebook)
        notebook.add(tests_tab, text="Test results")
        notebook.add(metrics_tab, text="Metrics and categories")
        notebook.add(output_tab, text="Raw output")

        tests_tab.columnconfigure(0, weight=3)
        tests_tab.columnconfigure(1, weight=2)
        tests_tab.rowconfigure(0, weight=1)
        self.results_tree = ttk.Treeview(tests_tab, columns=("status", "category", "time"), show="tree headings")
        self.results_tree.heading("#0", text="Test")
        self.results_tree.heading("status", text="Status")
        self.results_tree.heading("category", text="Category")
        self.results_tree.heading("time", text="Time")
        self.results_tree.column("#0", width=470)
        self.results_tree.column("status", width=90, anchor="center")
        self.results_tree.column("category", width=130)
        self.results_tree.column("time", width=80, anchor="e")
        self.results_tree.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.results_tree.tag_configure("passed", foreground="#4ade80")
        self.results_tree.tag_configure("failed", foreground="#f87171")
        self.results_tree.tag_configure("error", foreground="#fb7185")
        self.results_tree.tag_configure("skipped", foreground="#cbd5e1")
        self.results_tree.bind("<<TreeviewSelect>>", self._show_selected_test)
        self.detail_text = tk.Text(tests_tab, wrap="word", bg="#172033", fg="#e5e7eb", insertbackground="#e5e7eb", relief="flat", padx=12, pady=12, font=("Consolas", 10))
        self.detail_text.grid(row=0, column=1, sticky="nsew")
        self.detail_text.insert("1.0", "Select a test to see its purpose, duration, and failure detail.")
        self.detail_text.configure(state="disabled")

        metrics_tab.columnconfigure(0, weight=1)
        metrics_tab.rowconfigure(1, weight=1)
        self.run_summary_var = tk.StringVar(value="Run the suite to populate metrics.")
        ttk.Label(metrics_tab, textvariable=self.run_summary_var, font=("Segoe UI", 11)).grid(row=0, column=0, sticky="ew", padx=14, pady=14)
        self.metrics_canvas = tk.Canvas(metrics_tab, bg="#172033", highlightthickness=0)
        self.metrics_canvas.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

        output_tab.columnconfigure(0, weight=1)
        output_tab.rowconfigure(0, weight=1)
        self.output_text = tk.Text(output_tab, wrap="none", bg="#172033", fg="#e5e7eb", insertbackground="#e5e7eb", relief="flat", padx=12, pady=12, font=("Consolas", 10))
        self.output_text.grid(row=0, column=0, sticky="nsew")

    def start_run(self, scope: str) -> None:
        if self.running:
            return
        self.running = True
        self.status_var.set("Running the full suite..." if scope == "all" else "Trying to break the system...")
        self.progress.start(12)
        self.run_all_button.configure(state="disabled")
        self.run_weakness_button.configure(state="disabled")
        self.results_tree.delete(*self.results_tree.get_children(""))
        thread = threading.Thread(target=self._worker, args=(scope,), daemon=True)
        thread.start()

    def _worker(self, scope: str) -> None:
        try:
            result = run_test_suite(self.project_root, scope=scope)
        except Exception as error:
            self.events.put(("error", error))
        else:
            self.events.put(("complete", result))

    def _poll_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "complete":
                    self._display_result(payload)
                else:
                    self._display_error(payload)
        except queue.Empty:
            pass
        self.root.after(80, self._poll_events)

    def _display_result(self, result: TestRunResult) -> None:
        self.current_result = result
        self.running = False
        self.progress.stop()
        self.run_all_button.configure(state="normal")
        self.run_weakness_button.configure(state="normal")
        self.status_var.set("All checks passed" if result.success else "Weaknesses found - inspect failed tests")
        values = {
            "total": str(result.total),
            "passed": str(result.passed),
            "failed": str(result.failed),
            "skipped": str(result.skipped),
            "weakness": str(result.weakness_probes),
            "coverage": "n/a" if result.coverage_percent is None else f"{result.coverage_percent:.1f}%",
            "duration": f"{result.duration:.2f}s",
        }
        for key, value in values.items():
            self.metric_vars[key].set(value)
        for index, test in enumerate(result.tests):
            self.results_tree.insert(
                "",
                "end",
                iid=f"test-{index}",
                text=f"{test.classname}.{test.name}",
                values=(test.status.upper(), test.category, f"{test.duration:.3f}s"),
                tags=(test.status,),
            )
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", result.output)
        self.output_text.configure(state="disabled")
        branch = "n/a" if result.branch_coverage_percent is None else f"{result.branch_coverage_percent:.1f}%"
        self.run_summary_var.set(
            f"Scope: {result.scope}  |  line coverage: {values['coverage']}  |  branch coverage: {branch}  |  artifacts: {result.artifact_dir}"
        )
        self._draw_metrics(result)

    def _display_error(self, error: object) -> None:
        self.running = False
        self.progress.stop()
        self.run_all_button.configure(state="normal")
        self.run_weakness_button.configure(state="normal")
        self.status_var.set("Test Lab failed to start")
        messagebox.showerror("Test Lab error", str(error))

    def _show_selected_test(self, _event=None) -> None:
        if self.current_result is None:
            return
        selected = self.results_tree.selection()
        if not selected:
            return
        index = int(selected[0].split("-")[-1])
        test = self.current_result.tests[index]
        detail = (
            f"Test\n{test.classname}.{test.name}\n\n"
            f"Status\n{test.status.upper()}\n\n"
            f"Category\n{test.category}\n\n"
            f"Duration\n{test.duration:.6f} seconds\n\n"
            f"Failure / diagnostic detail\n{test.detail or 'No failure detail. The assertion passed.'}"
        )
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", detail)
        self.detail_text.configure(state="disabled")

    def _draw_metrics(self, result: TestRunResult) -> None:
        self.metrics_canvas.delete("all")
        self.metrics_canvas.update_idletasks()
        width = max(600, self.metrics_canvas.winfo_width())
        counts = result.category_counts()
        maximum = max(counts.values(), default=1)
        y = 32
        for category, count in counts.items():
            self.metrics_canvas.create_text(24, y, anchor="w", text=category, fill="#e5e7eb", font=("Segoe UI", 10, "bold"))
            bar_x = 180
            bar_width = (width - 250) * count / maximum
            self.metrics_canvas.create_rectangle(bar_x, y - 10, bar_x + bar_width, y + 10, fill="#2563eb", outline="")
            self.metrics_canvas.create_text(bar_x + bar_width + 10, y, anchor="w", text=str(count), fill="#93c5fd", font=("Segoe UI", 10, "bold"))
            y += 42
        self.metrics_canvas.configure(scrollregion=(0, 0, width, y + 20))

    def open_results_folder(self) -> None:
        folder = self.project_root / "test-results"
        folder.mkdir(exist_ok=True)
        try:
            import os

            os.startfile(folder)
        except OSError as error:
            messagebox.showerror("Open folder failed", str(error))
