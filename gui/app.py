from __future__ import annotations

import builtins
import contextlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Iterable

from tongalang import __version__
from tongalang.ast_visualizer import format_ast
from tongalang.diagnostics import (
    Diagnostic,
    SuggestedFix,
    analyze_source,
    apply_fix,
    diagnostic_from_error,
    diagnostic_from_exception,
)
from tongalang.errors import (
    ExecutionCancelledError,
    SourceEncodingError,
    SourceReadError,
    SourceWriteError,
    TongaLangError,
    TongaRuntimeError,
)
from tongalang.interpreter import Interpreter
from tongalang.parser import parse_source

from .ast_tree import ASTTreeNode, build_ast_tree_rows
from .ast_canvas import ASTCanvas
from .language_profile import LanguageProfile, build_language_profile
from .runtime import BlockingInputQueue, QueueTextWriter, RuntimeInputProvider
from .syntax_highlighter import DEFAULT_SYNTAX_THEMES, TongaSyntaxHighlighter


SAMPLE_PROGRAM = """// Cilangililo ca TongaLang: kubala, kuinduluka, amulimo
mulimo kumwaya(zyina) {
    pilula "Mwabonwa, " + zyina
}

mulimo matalikilo() {
    zina zyina = bala("Hena zyina lyanu ndinywe baani? ")
    amba(kumwaya(zyina))

    induluka i kuzwa 1 kusika 5 {
        amba("Namba: " + i)
    }
}
"""


class ExecutionState(str, Enum):
    READY = "Ready"
    RUNNING = "Running"
    WAITING_FOR_INPUT = "Waiting for input"
    FINISHED = "Finished"
    ERROR = "Error"


class DockView(str, Enum):
    PROBLEMS = "Problems"
    INPUT = "Program Input"


@dataclass
class IDEState:
    theme_name: str = "dark"
    font_family: str = "Consolas"
    font_size: int = 11
    error_display_mode: str = "bilingual"
    show_line_numbers: bool = True
    highlight_current_line: bool = True
    auto_clear_output: bool = True
    auto_show_ast: bool = False
    max_loop_iterations: int = 10000
    max_call_depth: int = 250
    syntax_colors: dict[str, str] = field(default_factory=dict)


THEMES = {
    "dark": {
        "bg": "#0b1020",
        "panel": "#111827",
        "panel_alt": "#172033",
        "editor_gutter": "#0f172a",
        "text": "#e5e7eb",
        "muted": "#94a3b8",
        "border": "#263244",
        "accent": "#3b82f6",
        "run": "#22c55e",
        "danger": "#ef4444",
        "warning": "#f59e0b",
        "button": "#1f2937",
        "button_active": "#2563eb",
        "entry": "#0f172a",
    },
    "light": {
        "bg": "#f3f4f6",
        "panel": "#ffffff",
        "panel_alt": "#eef2f7",
        "editor_gutter": "#e5e7eb",
        "text": "#111827",
        "muted": "#64748b",
        "border": "#cbd5e1",
        "accent": "#2563eb",
        "run": "#16a34a",
        "danger": "#dc2626",
        "warning": "#d97706",
        "button": "#e5e7eb",
        "button_active": "#dbeafe",
        "entry": "#ffffff",
    },
}


LOG_LEVELS = ("All", "Info", "Warning", "Error", "Debug")
AVAILABLE_EDITOR_FONTS = (
    "Consolas",
    "Cascadia Mono",
    "Courier New",
    "Lucida Console",
    "Segoe UI Mono",
)


class ScrollableFrame(tk.Frame):
    """A themed vertical form that supports scrollbar, wheel, and keyboard input."""

    def __init__(self, master: tk.Widget, **kwargs):
        super().__init__(master, **kwargs)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.body = tk.Frame(self.canvas)
        self.body.columnconfigure(0, weight=1)
        self.window_id = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", self._refresh_scroll_region)
        self.canvas.bind("<Configure>", self._resize_body)
        self.canvas.bind("<Button-1>", lambda _event: self.canvas.focus_set())
        self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.bind_all("<Button-4>", self._on_linux_wheel, add="+")
        self.bind_all("<Button-5>", self._on_linux_wheel, add="+")
        self.canvas.bind("<Prior>", lambda _event: self._scroll_pages(-1))
        self.canvas.bind("<Next>", lambda _event: self._scroll_pages(1))
        self.canvas.bind("<Home>", lambda _event: self.canvas.yview_moveto(0.0))
        self.canvas.bind("<End>", lambda _event: self.canvas.yview_moveto(1.0))

    def _refresh_scroll_region(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_body(self, event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _contains_widget(self, widget: tk.Widget | None) -> bool:
        while widget is not None:
            if widget in (self, self.canvas, self.body):
                return True
            widget = getattr(widget, "master", None)
        return False

    def _on_mousewheel(self, event):
        if not self._contains_widget(getattr(event, "widget", None)):
            return None
        delta = getattr(event, "delta", 0)
        if not delta:
            return None
        units = -max(1, abs(int(delta / 120))) if delta > 0 else max(1, abs(int(delta / 120)))
        self.canvas.yview_scroll(units, "units")
        return "break"

    def _on_linux_wheel(self, event):
        if not self._contains_widget(getattr(event, "widget", None)):
            return None
        self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")
        return "break"

    def _scroll_pages(self, pages: int):
        self.canvas.yview_scroll(pages, "pages")
        return "break"


class CollapsibleSection(tk.Frame):
    def __init__(self, master: tk.Widget, title: str, *, expanded: bool = True):
        super().__init__(master, bd=1, relief="solid")
        self.expanded = expanded
        self.header = tk.Button(self, anchor="w", command=self.toggle)
        self.header.pack(fill="x")
        self.body = tk.Frame(self)
        self.body.columnconfigure(1, weight=1)
        if expanded:
            self.body.pack(fill="x", padx=8, pady=(2, 8))
        self.title = title
        self._refresh_title()

    def toggle(self) -> None:
        self.expanded = not self.expanded
        if self.expanded:
            self.body.pack(fill="x", padx=8, pady=(2, 8))
        else:
            self.body.pack_forget()
        self._refresh_title()

    def _refresh_title(self) -> None:
        state = "Hide" if self.expanded else "Show"
        self.header.configure(text=f"{self.title}  ({state})")


class TongaLangGUI:
    """
    Modern educational IDE-style Tkinter environment for TongaLang.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.profile = build_language_profile()
        self.state = IDEState()
        self.current_file: Path | None = None
        self.execution_state = ExecutionState.READY
        self.sidebar_collapsed = False
        self.active_view = "Editor"
        self.navigation_history: list[str] = []
        self.navigation_index = -1
        self.log_filter = tk.StringVar(value="All")
        self.console_events: list[tuple[str, str, str]] = []
        self.input_queue: BlockingInputQueue | None = None
        self.stop_event = threading.Event()
        self.pending_input = False
        self.current_input_prompt = ""
        self.last_started_at: float | None = None
        self.ast_rows: dict[str, ASTTreeNode] = {}
        self.ast_text = ""
        self.selected_ast_node_id: str | None = None
        self.ui_queue: queue.Queue = queue.Queue()
        self.color_swatches: dict[str, tk.Canvas] = {}
        self.current_diagnostics: tuple[Diagnostic, ...] = ()
        self.selected_diagnostic_index: int | None = None
        self.dock_view = DockView.PROBLEMS
        self.dock_expanded = False
        self.dock_height = 220
        self.problems_expanded = False
        self.problems_pinned_open = False
        self._analysis_after_id: str | None = None
        self._editor_revision = 0
        self._editor_viewport = (0.0, 0.0)
        self._restore_editor_viewport_on_show = False

        self.root.title("TongaLang Educational IDE")
        self.root.geometry("1280x760")
        self.root.minsize(980, 620)

        self._build_ui()
        self._bind_shortcuts()
        self._set_editor_text(SAMPLE_PROGRAM)
        self._apply_theme()
        self._set_execution_state(ExecutionState.READY)
        self._log("Info", "IDE initialized")
        self._poll_ui_queue()

    # ========================================================
    # UI Construction
    # ========================================================

    def _build_ui(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.topbar = tk.Frame(self.root, height=46)
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.topbar.columnconfigure(6, weight=1)

        self.back_button = tk.Button(self.topbar, text="Back", command=self.go_back, width=8, state="disabled")
        self.back_button.grid(row=0, column=0, padx=(10, 4), pady=8)
        self.forward_button = tk.Button(self.topbar, text="Forward", command=self.go_forward, width=8, state="disabled")
        self.forward_button.grid(row=0, column=1, padx=4, pady=8)
        self.sidebar_toggle = tk.Button(self.topbar, text="Menu", command=self.toggle_sidebar, width=8)
        self.sidebar_toggle.grid(row=0, column=2, padx=4, pady=8)

        self.run_button = tk.Button(self.topbar, text="Run", command=self.run_program, width=10)
        self.run_button.grid(row=0, column=3, padx=(12, 4), pady=8)
        tk.Button(self.topbar, text="Stop", command=self.stop_program, width=10).grid(row=0, column=4, padx=4, pady=8)
        tk.Button(self.topbar, text="Output", command=lambda: self.switch_view("Output"), width=10).grid(row=0, column=5, padx=4, pady=8)

        self.file_label_var = tk.StringVar(value="Untitled.tg")
        self.cursor_var = tk.StringVar(value="Ln 1, Col 1")
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(self.topbar, textvariable=self.status_var, anchor="e")
        self.status_label.grid(row=0, column=6, sticky="e", padx=12)

        self.sidebar = tk.Frame(self.root, width=190)
        self.sidebar.grid(row=1, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        self.content = tk.Frame(self.root)
        self.content.grid(row=1, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        self.nav_buttons: dict[str, tk.Button] = {}
        self.views: dict[str, tk.Frame] = {}
        self.workspace_view_names = {"Editor", "Output"}
        self.workspace = tk.Frame(self.content)
        self.workspace.grid(row=0, column=0, sticky="nsew")
        self.workspace.rowconfigure(0, weight=1)
        self.workspace.columnconfigure(0, weight=1)
        self.workspace_paned = tk.PanedWindow(
            self.workspace,
            orient="vertical",
            sashwidth=6,
            bd=0,
            relief="flat",
        )
        self.workspace_paned.grid(row=0, column=0, sticky="nsew")
        self.workspace_main = tk.Frame(self.workspace_paned)
        self.workspace_main.rowconfigure(0, weight=1)
        self.workspace_main.columnconfigure(0, weight=1)
        self.workspace_paned.add(self.workspace_main, stretch="always", minsize=220)
        self._build_sidebar()
        self._build_views()
        self._build_shared_dock()
        self.switch_view("Editor")

    def _build_sidebar(self) -> None:
        title = tk.Label(self.sidebar, text="TongaLang", font=("Segoe UI", 15, "bold"), anchor="w")
        title.pack(fill="x", padx=14, pady=(14, 6))
        subtitle = tk.Label(self.sidebar, text="Interpreter IDE", anchor="w")
        subtitle.pack(fill="x", padx=14, pady=(0, 12))

        for view in ("Editor", "Settings", "About"):
            button = tk.Button(
                self.sidebar,
                text=view,
                anchor="w",
                command=lambda name=view: self.switch_view(name),
                padx=14,
                pady=9,
                relief="flat",
            )
            button.pack(fill="x", padx=8, pady=2)
            self.nav_buttons[view] = button

    def _build_views(self) -> None:
        self._build_editor_view()
        self._build_output_view()
        self._build_ast_view()
        self._build_console_view()
        self._build_settings_view()
        self._build_grammar_view()
        self._build_about_view()

    def _new_view(self, name: str) -> tk.Frame:
        parent = self.workspace_main if name in self.workspace_view_names else self.content
        frame = tk.Frame(parent)
        frame.grid(row=0, column=0, sticky="nsew")
        self.views[name] = frame
        return frame

    def _build_editor_view(self) -> None:
        frame = self._new_view("Editor")
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(0, weight=1)

        header = tk.Frame(frame)
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        header.columnconfigure(1, weight=1)
        tk.Label(header, text="Source Editor", font=("Segoe UI", 15, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(header, textvariable=self.file_label_var).grid(row=0, column=1, sticky="e")

        controls = tk.Frame(frame)
        controls.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        tk.Button(controls, text="Open", command=self.open_file).pack(side="left")
        tk.Button(controls, text="Save", command=self.save_file).pack(side="left", padx=6)
        tk.Button(controls, text="Save As", command=self.save_file_as).pack(side="left")
        tk.Button(controls, text="Run F5", command=self.run_program).pack(side="left", padx=(16, 6))
        tk.Label(controls, textvariable=self.cursor_var).pack(side="right")

        editor_shell = tk.Frame(frame, bd=1)
        editor_shell.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 8))
        editor_shell.rowconfigure(0, weight=1)
        editor_shell.columnconfigure(1, weight=1)

        self.line_numbers = tk.Text(editor_shell, width=5, padx=6, pady=10, state="disabled", wrap="none")
        self.line_numbers.grid(row=0, column=0, sticky="ns")

        self.editor = tk.Text(editor_shell, undo=True, wrap="none", tabs=("32p",))
        self.editor.grid(row=0, column=1, sticky="nsew")

        yscroll = ttk.Scrollbar(editor_shell, orient="vertical", command=self._scroll_editor)
        yscroll.grid(row=0, column=2, sticky="ns")
        xscroll = ttk.Scrollbar(editor_shell, orient="horizontal", command=self.editor.xview)
        xscroll.grid(row=1, column=1, sticky="ew")
        self.editor.configure(yscrollcommand=lambda first, last: self._on_editor_scroll(first, last, yscroll), xscrollcommand=xscroll.set)

        self.highlighter = TongaSyntaxHighlighter(
            self.editor,
            profile=self.profile,
            theme_name=self.state.theme_name,
            font_family=self.state.font_family,
            font_size=self.state.font_size,
        )

        for event in ("<KeyRelease>", "<ButtonRelease-1>", "<MouseWheel>", "<Configure>"):
            self.editor.bind(event, self._on_editor_activity, add="+")
        self.editor.bind("<<Modified>>", self._on_editor_modified, add="+")
        self.editor.bind("<Tab>", self._insert_spaces)
        self.editor.bind("<Return>", self._auto_indent)
        self.editor.bind("<Shift-MouseWheel>", self._scroll_editor_horizontally)

    def _build_output_view(self) -> None:
        frame = self._new_view("Output")
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(0, weight=1)

        tk.Label(frame, text="Program Output", font=("Segoe UI", 15, "bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))
        toolbar = tk.Frame(frame)
        toolbar.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        tk.Button(toolbar, text="Clear Output", command=self.clear_output).pack(side="left")
        tk.Button(toolbar, text="Copy Output", command=lambda: self.copy_text(self.output_text)).pack(side="left", padx=6)
        self.execution_summary_var = tk.StringVar(value="No program has run yet.")
        tk.Label(toolbar, textvariable=self.execution_summary_var).pack(side="right")

        self.output_text = ScrolledText(frame, wrap="word", font=("Consolas", 11))
        self.output_text.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.output_text.configure(state="disabled")

    def _build_shared_dock(self) -> None:
        """Build the single Problems/Program Input dock shared by Editor and Output."""
        self.dock_shell = tk.Frame(self.workspace_paned, bd=1)
        self.dock_shell.columnconfigure(0, weight=1)
        self.dock_shell.rowconfigure(1, weight=1)

        selector = tk.Frame(self.dock_shell)
        selector.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        selector.columnconfigure(2, weight=1)
        self.problems_heading_var = tk.StringVar(value="Problems (0)")
        self.problems_toggle = tk.Button(
            selector,
            textvariable=self.problems_heading_var,
            command=lambda: self.toggle_problems(user_action=True),
        )
        self.problems_toggle.grid(row=0, column=0, padx=(0, 6))
        self.input_toggle_var = tk.StringVar(value="Program Input")
        self.input_toggle = tk.Button(
            selector,
            textvariable=self.input_toggle_var,
            command=lambda: self.toggle_input_dock(user_action=True),
        )
        self.input_toggle.grid(row=0, column=1, padx=(0, 8))
        self.dock_status_var = tk.StringVar(value="Problems is the default dock view")
        tk.Label(selector, textvariable=self.dock_status_var, anchor="e").grid(row=0, column=2, sticky="e", padx=8)
        self.dock_collapse_button = tk.Button(selector, text="Collapse", command=lambda: self.collapse_dock(user_action=True))
        self.dock_collapse_button.grid(row=0, column=3, padx=(6, 0))

        self.dock_body = tk.Frame(self.dock_shell)
        self.dock_body.grid(row=1, column=0, sticky="nsew")
        self.dock_body.rowconfigure(0, weight=1)
        self.dock_body.columnconfigure(0, weight=1)

        self.problems_panel = tk.Frame(self.dock_body)
        self.problems_panel.grid(row=0, column=0, sticky="nsew")
        self.problems_panel.rowconfigure(1, weight=1)
        self.problems_panel.columnconfigure(0, weight=1)
        problems_actions = tk.Frame(self.problems_panel)
        problems_actions.grid(row=0, column=0, sticky="ew", padx=8, pady=(0, 4))
        problems_actions.columnconfigure(0, weight=1)
        tk.Label(problems_actions, text="Select a problem to see beginner-friendly guidance.", anchor="w").grid(row=0, column=0, sticky="w")
        tk.Button(problems_actions, text="Go to Code", command=self.go_to_selected_problem).grid(row=0, column=1, padx=4)
        tk.Button(problems_actions, text="Copy Details", command=self.copy_problem_details).grid(row=0, column=2, padx=(4, 0))

        problems_body = tk.PanedWindow(self.problems_panel, orient="horizontal", sashwidth=5, bd=0)
        problems_body.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        list_shell = tk.Frame(problems_body)
        list_shell.rowconfigure(0, weight=1)
        list_shell.columnconfigure(0, weight=1)
        self.problems_tree = ttk.Treeview(
            list_shell,
            columns=("code", "location", "message"),
            show="headings",
            height=5,
            selectmode="browse",
        )
        self.problems_tree.heading("code", text="Code")
        self.problems_tree.heading("location", text="Location")
        self.problems_tree.heading("message", text="Problem")
        self.problems_tree.column("code", width=85, stretch=False)
        self.problems_tree.column("location", width=90, stretch=False)
        self.problems_tree.column("message", width=360)
        self.problems_tree.grid(row=0, column=0, sticky="nsew")
        problem_scroll = ttk.Scrollbar(list_shell, orient="vertical", command=self.problems_tree.yview)
        problem_scroll.grid(row=0, column=1, sticky="ns")
        self.problems_tree.configure(yscrollcommand=problem_scroll.set)
        self.problems_tree.bind("<<TreeviewSelect>>", self._on_problem_selected)
        self.problems_tree.bind("<Return>", lambda _event: self.go_to_selected_problem())
        problems_body.add(list_shell, minsize=340, stretch="always")

        detail_shell = tk.Frame(problems_body)
        detail_shell.columnconfigure(0, weight=1)
        self.problem_detail_var = tk.StringVar(value="No problems detected. The code is ready to run.")
        self.problem_detail_label = tk.Label(
            detail_shell,
            textvariable=self.problem_detail_var,
            justify="left",
            anchor="nw",
            wraplength=280,
        )
        self.problem_detail_label.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 8))
        detail_shell.bind(
            "<Configure>",
            lambda event: self.problem_detail_label.configure(wraplength=max(180, event.width - 24)),
            add="+",
        )
        self.problem_fix_frame = tk.Frame(detail_shell)
        self.problem_fix_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        problems_body.add(detail_shell, minsize=300, stretch="always")

        self.input_panel = tk.Frame(self.dock_body)
        self.input_panel.grid(row=0, column=0, sticky="nsew")
        self.input_panel.columnconfigure(0, weight=1)
        self.input_prompt_var = tk.StringVar(value="No bala() input request is pending.")
        self.pending_input_var = tk.StringVar(value="Status: idle")
        tk.Label(self.input_panel, text="Program Input", font=("Segoe UI", 11, "bold"), anchor="w").grid(
            row=0, column=0, sticky="ew", padx=12, pady=(8, 2)
        )
        tk.Label(self.input_panel, textvariable=self.input_prompt_var, anchor="w").grid(
            row=1, column=0, sticky="ew", padx=12
        )
        tk.Label(self.input_panel, textvariable=self.pending_input_var, anchor="w").grid(
            row=2, column=0, sticky="ew", padx=12, pady=(0, 8)
        )
        input_row = tk.Frame(self.input_panel)
        input_row.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
        input_row.columnconfigure(0, weight=1)
        self.input_entry = tk.Entry(input_row, state="disabled")
        self.input_entry.grid(row=0, column=0, sticky="ew")
        self.input_entry.bind("<Return>", lambda _event: self.submit_input())
        self.input_submit = tk.Button(input_row, text="Submit Input", command=self.submit_input, state="disabled")
        self.input_submit.grid(row=0, column=1, padx=(8, 0))

        self.workspace_paned.add(self.dock_shell, stretch="never", minsize=42)
        self.dock_body.grid_remove()
        self.problems_panel.tkraise()
        self._refresh_dock_controls()
        self.root.after_idle(self._position_dock_sash)

    def _build_ast_view(self) -> None:
        frame = self._new_view("AST")
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(0, weight=1)

        header = tk.Frame(frame)
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        header.columnconfigure(1, weight=1)
        tk.Label(header, text="Abstract Syntax Tree", font=("Segoe UI", 15, "bold")).grid(row=0, column=0, sticky="w")
        self.ast_status_var = tk.StringVar(value="No syntax tree has been generated.")
        tk.Label(header, textvariable=self.ast_status_var).grid(row=0, column=1, sticky="e")

        toolbar = tk.Frame(frame)
        toolbar.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        tk.Button(toolbar, text="Refresh", command=self.refresh_ast).pack(side="left")
        tk.Button(toolbar, text="Fit tree", command=lambda: self.ast_canvas.fit_to_window()).pack(side="left", padx=6)
        tk.Button(toolbar, text="Zoom -", command=lambda: self.ast_canvas.zoom_out()).pack(side="left")
        tk.Button(toolbar, text="Zoom +", command=lambda: self.ast_canvas.zoom_in()).pack(side="left", padx=6)
        tk.Button(toolbar, text="Expand outline", command=lambda: self._set_tree_open(True)).pack(side="left", padx=(10, 6))
        tk.Button(toolbar, text="Collapse outline", command=lambda: self._set_tree_open(False)).pack(side="left")
        tk.Button(toolbar, text="Copy tree text", command=self.copy_ast).pack(side="left", padx=6)
        self.ast_search_var = tk.StringVar()
        search = tk.Entry(toolbar, textvariable=self.ast_search_var, width=24)
        search.pack(side="right")
        search.bind("<Return>", lambda _event: self.find_ast_node())
        tk.Button(toolbar, text="Find node", command=self.find_ast_node).pack(side="right", padx=6)

        split = ttk.PanedWindow(frame, orient="horizontal")
        split.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))

        explorer = ttk.Notebook(split)
        diagram_tab = ttk.Frame(explorer)
        outline_tab = ttk.Frame(explorer)
        explorer.add(diagram_tab, text="Tree diagram")
        explorer.add(outline_tab, text="Accessible outline")
        split.add(explorer, weight=4)

        diagram_tab.rowconfigure(0, weight=1)
        diagram_tab.columnconfigure(0, weight=1)
        self.ast_canvas = ASTCanvas(diagram_tab, on_select=self._on_ast_select)
        self.ast_canvas.grid(row=0, column=0, sticky="nsew")

        outline_tab.rowconfigure(0, weight=1)
        outline_tab.columnconfigure(0, weight=1)
        self.ast_tree = ttk.Treeview(outline_tab, columns=("type", "line"), show="tree headings")
        self.ast_tree.heading("#0", text="Node")
        self.ast_tree.heading("type", text="Type")
        self.ast_tree.heading("line", text="Line")
        self.ast_tree.column("#0", width=360)
        self.ast_tree.column("type", width=120)
        self.ast_tree.column("line", width=70, anchor="center")
        outline_scroll = ttk.Scrollbar(outline_tab, orient="vertical", command=self.ast_tree.yview)
        self.ast_tree.configure(yscrollcommand=outline_scroll.set)
        self.ast_tree.grid(row=0, column=0, sticky="nsew")
        outline_scroll.grid(row=0, column=1, sticky="ns")
        self.ast_tree.bind("<<TreeviewSelect>>", self._on_ast_select)

        inspector = ttk.Frame(split, padding=10)
        inspector.rowconfigure(2, weight=1)
        inspector.columnconfigure(0, weight=1)
        split.add(inspector, weight=2)
        tk.Label(inspector, text="Node inspector", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(
            inspector,
            text="Select a box to see its role, source location, and nearby TongaLang code.",
            justify="left",
            wraplength=310,
        ).grid(row=1, column=0, sticky="ew", pady=(2, 8))
        self.ast_detail = ScrolledText(inspector, wrap="word", font=("Consolas", 10), width=38)
        self.ast_detail.grid(row=2, column=0, sticky="nsew")
        self.ast_detail.configure(state="disabled")
        inspector_actions = tk.Frame(inspector)
        inspector_actions.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        tk.Button(inspector_actions, text="Go to source line", command=self.go_to_ast_source).pack(side="left")
        tk.Label(
            inspector_actions,
            text="Tip: Ctrl + mouse wheel zooms; middle-drag pans.",
        ).pack(side="right")

    def _build_console_view(self) -> None:
        frame = self._new_view("Console")
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(0, weight=1)

        tk.Label(frame, text="Console Logs", font=("Segoe UI", 15, "bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))
        toolbar = tk.Frame(frame)
        toolbar.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        tk.Label(toolbar, text="Filter").pack(side="left")
        ttk.Combobox(toolbar, textvariable=self.log_filter, values=LOG_LEVELS, state="readonly", width=12).pack(side="left", padx=6)
        self.log_filter.trace_add("write", lambda *_args: self._render_console())
        tk.Button(toolbar, text="Clear Logs", command=self.clear_console).pack(side="left", padx=6)

        self.console_text = ScrolledText(frame, wrap="word", font=("Consolas", 10))
        self.console_text.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.console_text.configure(state="disabled")

    def _build_settings_view(self) -> None:
        frame = self._new_view("Settings")
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        tk.Label(frame, text="Settings", font=("Segoe UI", 15, "bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 8))
        self.settings_scroll = ScrollableFrame(frame)
        self.settings_scroll.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        settings_body = self.settings_scroll.body

        self.theme_var = tk.StringVar(value=self.state.theme_name)
        self.error_mode_var = tk.StringVar(value=self.state.error_display_mode)
        self.font_family_var = tk.StringVar(value=self.state.font_family)
        self.font_size_var = tk.IntVar(value=self.state.font_size)
        self.max_loop_var = tk.IntVar(value=self.state.max_loop_iterations)
        self.max_call_depth_var = tk.IntVar(value=self.state.max_call_depth)
        self.show_lines_var = tk.BooleanVar(value=self.state.show_line_numbers)
        self.current_line_var = tk.BooleanVar(value=self.state.highlight_current_line)
        self.auto_clear_var = tk.BooleanVar(value=self.state.auto_clear_output)

        def add_section(title: str, *, expanded: bool = True) -> CollapsibleSection:
            section = CollapsibleSection(settings_body, title, expanded=expanded)
            section.pack(fill="x", pady=(0, 8))
            return section

        def label(parent: tk.Widget, text: str, row: int) -> None:
            tk.Label(parent, text=text, anchor="w").grid(row=row, column=0, sticky="w", padx=8, pady=5)

        appearance = add_section("Appearance")
        label(appearance.body, "Theme", 0)
        ttk.Combobox(appearance.body, textvariable=self.theme_var, values=("dark", "light"), state="readonly").grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        self.theme_var.trace_add("write", lambda *_args: self._update_theme_from_settings())
        label(appearance.body, "Editor font", 1)
        ttk.Combobox(appearance.body, textvariable=self.font_family_var, values=AVAILABLE_EDITOR_FONTS, state="readonly").grid(row=1, column=1, sticky="ew", padx=8, pady=5)
        label(appearance.body, "Font size", 2)
        tk.Spinbox(appearance.body, from_=9, to=24, width=10, textvariable=self.font_size_var, command=self.apply_editor_settings).grid(row=2, column=1, sticky="w", padx=8, pady=5)

        guidance = add_section("Error Guidance")
        label(guidance.body, "Error language", 0)
        ttk.Combobox(
            guidance.body,
            textvariable=self.error_mode_var,
            values=("bilingual", "tonga"),
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        self.error_mode_var.trace_add("write", lambda *_args: self._update_error_mode_from_settings())

        editor_section = add_section("Editor")
        tk.Checkbutton(editor_section.body, text="Show line numbers", variable=self.show_lines_var, command=self.apply_editor_settings).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=5)
        tk.Checkbutton(editor_section.body, text="Highlight current line", variable=self.current_line_var, command=self.apply_editor_settings).grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=5)

        safety = add_section("Execution Safety")
        label(safety.body, "Max loop iterations", 0)
        tk.Spinbox(safety.body, from_=1, to=1000000, width=12, textvariable=self.max_loop_var).grid(row=0, column=1, sticky="w", padx=8, pady=5)
        label(safety.body, "Max function-call depth", 1)
        tk.Spinbox(safety.body, from_=1, to=10000, width=12, textvariable=self.max_call_depth_var).grid(row=1, column=1, sticky="w", padx=8, pady=5)
        tk.Checkbutton(safety.body, text="Auto-clear output on run", variable=self.auto_clear_var, command=self.apply_editor_settings).grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=5)

        language_tools = add_section("Language Tools")
        tools = tk.Frame(language_tools.body)
        tools.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=5)
        tk.Button(tools, text="View AST", command=self.view_ast_from_settings).pack(side="left")
        tk.Button(tools, text="View Console", command=self.view_console_from_settings).pack(side="left", padx=8)
        tk.Button(tools, text="View Grammar", command=self.view_grammar_from_settings).pack(side="left")

        syntax = add_section("Syntax Colors")
        self.color_swatches = {}
        color_keys = (
            "declarations", "input_output", "conditionals", "loops", "functions", "entry_point",
            "booleans", "word_operators", "strings", "comments", "numbers", "native_functions",
            "operators", "current_line", "error_line", "ast_highlight",
        )
        for row, color_key in enumerate(color_keys):
            label(syntax.body, color_key.replace("_", " ").title(), row)
            swatch = tk.Canvas(syntax.body, width=32, height=18, highlightthickness=1)
            swatch.grid(row=row, column=1, sticky="w", padx=8, pady=3)
            self.color_swatches[color_key] = swatch
            tk.Button(syntax.body, text="Choose", command=lambda key=color_key: self.choose_syntax_color(key)).grid(row=row, column=2, sticky="w", padx=8, pady=3)

        buttons = tk.Frame(settings_body)
        buttons.pack(fill="x", pady=(4, 8))
        tk.Button(buttons, text="Apply Settings", command=self.apply_editor_settings).pack(side="left")
        tk.Button(buttons, text="Reset Defaults", command=self.reset_defaults).pack(side="left", padx=8)
        self.settings_error_var = tk.StringVar(value="")
        self.settings_error_label = tk.Label(settings_body, textvariable=self.settings_error_var, anchor="w")
        self.settings_error_label.pack(fill="x", pady=(0, 12))

    def _build_grammar_view(self) -> None:
        frame = self._new_view("Grammar")
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(0, weight=1)

        tk.Label(frame, text="Grammar Reference", font=("Segoe UI", 15, "bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))
        toolbar = tk.Frame(frame)
        toolbar.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        tk.Button(toolbar, text="Refresh Grammar", command=self.refresh_grammar_reference).pack(side="left")
        tk.Button(toolbar, text="Copy Grammar", command=lambda: self.copy_text(self.grammar_text)).pack(side="left", padx=6)

        self.grammar_text = ScrolledText(frame, wrap="word", font=("Consolas", 10))
        self.grammar_text.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.grammar_text.insert("1.0", self._grammar_content())
        self.grammar_text.configure(state="disabled")

    def _build_about_view(self) -> None:
        frame = self._new_view("About")
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        tk.Label(frame, text="About TongaLang", font=("Segoe UI", 15, "bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 8))
        self.about_scroll = ScrollableFrame(frame)
        self.about_scroll.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        body = self.about_scroll.body
        self.about_section_titles: list[str] = []

        sections = (
            (
                "About TongaLang",
                f"TongaLang is a small interpreted programming language for beginner education. "
                f"It uses Tonga-derived words to explain core programming ideas in a familiar way.\n\nVersion: {__version__}",
            ),
            (
                "Project Author",
                "Author: Leo Mabuku",
            ),
            (
                "Academic Project Details",
                "Project: Implementation of a Programming Language Using Local Language\n"
                "Course: CS400 Project Seminars\n"
                "University: The Copperbelt University\n"
                "School: School of Information and Communication Technology\n"
                "Department: Department of Computer Science\n"
                "Supervisor: Dr. Maybin Lengwe",
            ),
            (
                "Why the Project Exists",
                "Programming is often introduced with unfamiliar English terms. TongaLang explores whether familiar local-language words can make the first steps easier while learners still practise variables, decisions, loops, functions, input, and output.",
            ),
            (
                "How TongaLang Works",
                "Your source code is read by the lexer, arranged into an abstract syntax tree by the parser, and executed by the interpreter. Program output and input are then shown in the IDE.\n\nSource code  →  Lexer  →  Parser and AST  →  Interpreter  →  Input and output",
            ),
            (
                "Quick Start",
                "1. Type code in the Source Editor or open a .tg file.\n"
                "2. Start the program with mulimo matalikilo() { ... }.\n"
                "3. Select Run or press F5.\n"
                "4. When bala() pauses the program, enter a value in the Program Input dock.\n"
                "5. Read the Problems pane if the code needs correction.\n"
                "6. Apply a safe fix when one is offered, or follow the example shown.\n"
                "7. Save the finished program.",
            ),
            (
                "IDE Features",
                "- Live bilingual diagnostics and guarded one-click fixes\n"
                "- Semantic keyword colors, dark and light themes\n"
                "- Shared Problems and Program Input dock below Editor and Output\n"
                "- Visible input transcripts that continue in Program Output\n"
                "- Source-linked AST explorer and internal console\n"
                "- Scrollable settings, Back and Forward navigation, and a collapsible menu\n"
                "- Loop, recursion, and safe-stop limits for beginner programs",
            ),
            (
                "Language at a Glance",
                "Declare data with zina, display output with amba, read input with bala, make decisions with kuti, repeat work with the loop keywords, and define reusable code with mulimo. Open the Grammar Reference for the complete language summary.",
            ),
            (
                "Scope and Safety",
                "TongaLang is an educational language rather than a production application platform. The interpreter limits loops and nested function calls, supports safe cancellation, and reports controlled errors instead of exposing Python failures whenever possible.",
            ),
        )

        for row, (title, content) in enumerate(sections):
            self.about_section_titles.append(title)
            card = tk.Frame(body, bd=1, relief="solid")
            card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
            card.columnconfigure(0, weight=1)
            tk.Label(card, text=title, font=("Segoe UI", 12, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
            content_label = tk.Label(
                card,
                text=content,
                font=("Segoe UI", 10),
                justify="left",
                anchor="w",
                wraplength=620,
            )
            content_label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
            card.bind(
                "<Configure>",
                lambda event, label=content_label: label.configure(wraplength=max(240, event.width - 24)),
                add="+",
            )

        actions = tk.Frame(body)
        actions.grid(row=len(sections), column=0, sticky="w", pady=(4, 14))
        tk.Button(actions, text="View Grammar", command=self.view_grammar_from_settings).pack(side="left")
        tk.Button(actions, text="Open Editor", command=lambda: self.switch_view("Editor")).pack(side="left", padx=8)
        tk.Button(actions, text="Open Settings", command=lambda: self.switch_view("Settings")).pack(side="left")

    # ========================================================
    # Navigation and Theme
    # ========================================================

    def switch_view(self, name: str, *, record_history: bool = True) -> None:
        if name not in self.views:
            return
        if self.active_view == "Editor" and name != "Editor":
            self._editor_viewport = (self.editor.yview()[0], self.editor.xview()[0])
        if record_history and (not self.navigation_history or self.navigation_history[self.navigation_index] != name):
            if self.navigation_index < len(self.navigation_history) - 1:
                self.navigation_history = self.navigation_history[: self.navigation_index + 1]
            self.navigation_history.append(name)
            self.navigation_index = len(self.navigation_history) - 1
        self.active_view = name
        if name in self.workspace_view_names:
            self.workspace.tkraise()
            self.views[name].tkraise()
        else:
            self.views[name].tkraise()
        if name == "Editor" and self._restore_editor_viewport_on_show:
            self.root.update_idletasks()
            self.editor.yview_moveto(self._editor_viewport[0])
            self.editor.xview_moveto(self._editor_viewport[1])
            self._update_line_numbers()
            self._restore_editor_viewport_on_show = False
        for view_name, button in self.nav_buttons.items():
            button.configure(relief="flat")
            if view_name == name:
                button.configure(relief="sunken")
        self._update_navigation_buttons()

    def go_back(self) -> None:
        if self.navigation_index <= 0:
            return
        self.navigation_index -= 1
        self.switch_view(self.navigation_history[self.navigation_index], record_history=False)

    def go_forward(self) -> None:
        if self.navigation_index >= len(self.navigation_history) - 1:
            return
        self.navigation_index += 1
        self.switch_view(self.navigation_history[self.navigation_index], record_history=False)

    def _update_navigation_buttons(self) -> None:
        if not hasattr(self, "back_button"):
            return
        self.back_button.configure(state="normal" if self.navigation_index > 0 else "disabled")
        self.forward_button.configure(
            state="normal" if 0 <= self.navigation_index < len(self.navigation_history) - 1 else "disabled"
        )

    def toggle_sidebar(self) -> None:
        self.sidebar_collapsed = not self.sidebar_collapsed
        if self.sidebar_collapsed:
            self.sidebar.grid_remove()
            self.content.grid_configure(row=1, column=0, columnspan=2, sticky="nsew")
            self.sidebar_toggle.configure(text="Show Menu")
        else:
            self.content.grid_configure(row=1, column=1, columnspan=1, sticky="nsew")
            self.sidebar.grid(row=1, column=0, sticky="ns")
            self.sidebar_toggle.configure(text="Hide Menu")

    def _apply_theme(self) -> None:
        if self.active_view == "Editor":
            editor_y_position = self.editor.yview()[0]
            editor_x_position = self.editor.xview()[0]
            self._editor_viewport = (editor_y_position, editor_x_position)
        else:
            editor_y_position, editor_x_position = self._editor_viewport
            self._restore_editor_viewport_on_show = True
        colors = THEMES[self.state.theme_name]
        self.root.configure(bg=colors["bg"])
        self.topbar.configure(bg=colors["panel"])
        self.sidebar.configure(bg=colors["panel"])
        self.content.configure(bg=colors["bg"])

        self._configure_tree_style(colors)
        for widget in self._walk_widgets(self.root):
            # ttk widgets are styled through ttk.Style and do not accept the
            # classic Tk bg/fg option names used by Frame, Text, and Entry.
            if widget.winfo_class().startswith("T"):
                continue
            if isinstance(widget, tk.Frame):
                widget.configure(bg=colors["bg"] if widget is self.content else colors["panel"])
            elif isinstance(widget, tk.PanedWindow):
                widget.configure(bg=colors["border"], sashrelief="flat")
            elif isinstance(widget, tk.Canvas):
                widget.configure(bg=colors["panel_alt"], highlightbackground=colors["border"])
            elif isinstance(widget, tk.Label):
                widget.configure(bg=self._background_for(widget.master, colors), fg=colors["text"])
            elif isinstance(widget, tk.Button):
                bg = colors["run"] if widget is self.run_button else colors["button"]
                widget.configure(
                    bg=bg,
                    fg=colors["text"],
                    activebackground=colors["button_active"],
                    relief="flat",
                    bd=0,
                    highlightthickness=1,
                    highlightbackground=colors["panel"],
                    highlightcolor=colors["accent"],
                    takefocus=True,
                )
            elif isinstance(widget, tk.Checkbutton):
                master_bg = self._background_for(widget.master, colors)
                widget.configure(bg=master_bg, fg=colors["text"], selectcolor=colors["panel_alt"], activebackground=master_bg)
            elif isinstance(widget, (tk.Entry, tk.Spinbox)):
                widget.configure(bg=colors["entry"], fg=colors["text"], insertbackground=colors["text"], relief="flat")
            elif isinstance(widget, tk.Text):
                widget.configure(bg=colors["panel_alt"], fg=colors["text"], insertbackground=colors["text"], relief="flat")

        self.status_label.configure(fg=colors["muted"])
        # ScrolledText wraps its Text widget in an internal frame, so apply
        # the output palette explicitly rather than relying on widget walking.
        self.output_text.configure(
            bg=colors["panel_alt"],
            fg=colors["text"],
            insertbackground=colors["text"],
            selectbackground=colors["accent"],
            relief="flat",
        )
        # Keep the learner's single input field visually distinct in both
        # themes, including when keyboard focus moves into the dock.
        self.input_entry.configure(
            bg=colors["entry"],
            fg=colors["text"],
            insertbackground=colors["text"],
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=colors["border"],
            highlightcolor=colors["accent"],
        )
        if hasattr(self, "settings_error_label"):
            self.settings_error_label.configure(fg=colors["danger"])
        self.highlighter.set_current_line_enabled(self.state.highlight_current_line)
        self.highlighter.apply_theme(
            self.state.theme_name,
            font_family=self.state.font_family,
            font_size=self.state.font_size,
            custom_colors=self.state.syntax_colors,
        )
        self.line_numbers.configure(
            bg=colors["editor_gutter"],
            fg=colors["muted"],
            font=(self.state.font_family, self.state.font_size),
            relief="flat",
            spacing1=2,
            spacing3=2,
        )
        if hasattr(self, "ast_canvas"):
            self.ast_canvas.set_palette(
                {
                    "canvas": colors["panel_alt"],
                    "text": colors["text"],
                    "muted": colors["muted"],
                    "line": colors["border"],
                    "outline": colors["muted"],
                    "selected": colors["accent"],
                }
            )
        self._update_line_numbers()
        self._refresh_color_swatches()
        self._refresh_dock_controls()

        # A Text widget can reveal the insertion cursor when its font changes
        # while the Editor view is hidden. Restore both panes once geometry has
        # settled so line numbers and source remain aligned.
        def restore_editor_viewport() -> None:
            self.editor.yview_moveto(editor_y_position)
            self.editor.xview_moveto(editor_x_position)
            self._update_line_numbers()

        if self.active_view == "Editor":
            self.root.after_idle(restore_editor_viewport)

    def _configure_tree_style(self, colors: dict[str, str]) -> None:
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=colors["panel_alt"], foreground=colors["text"], fieldbackground=colors["panel_alt"], bordercolor=colors["border"])
        style.configure("Treeview.Heading", background=colors["panel"], foreground=colors["text"])
        style.configure(
            "TCombobox",
            fieldbackground=colors["entry"],
            foreground=colors["text"],
            background=colors["button"],
            arrowcolor=colors["text"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["entry"])],
            foreground=[("readonly", colors["text"])],
            selectbackground=[("readonly", colors["entry"])],
            selectforeground=[("readonly", colors["text"])],
        )
        style.configure(
            "TScrollbar",
            background=colors["button"],
            troughcolor=colors["panel_alt"],
            arrowcolor=colors["text"],
            bordercolor=colors["border"],
        )

    @staticmethod
    def _background_for(widget: tk.Widget, colors: dict[str, str]) -> str:
        try:
            return str(widget.cget("bg"))
        except tk.TclError:
            return colors["panel"]

    def _walk_widgets(self, widget: tk.Widget):
        for child in widget.winfo_children():
            yield child
            yield from self._walk_widgets(child)

    # ========================================================
    # File and Editor Actions
    # ========================================================

    def open_file(self) -> None:
        path = filedialog.askopenfilename(title="Open TongaLang file", filetypes=[("TongaLang files", "*.tg"), ("All files", "*.*")])
        if not path:
            return
        file_path = Path(path)
        try:
            self._set_editor_text(file_path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            self._handle_tongalang_error(SourceEncodingError(file_path))
            return
        except OSError as error:
            self._handle_tongalang_error(SourceReadError(file_path, str(error)))
            return
        self.current_file = file_path
        self.file_label_var.set(file_path.name)
        self._log("Info", f"Opened {file_path}")

    def save_file(self) -> None:
        if self.current_file is None:
            self.save_file_as()
            return
        self._write_current_file(self.current_file)

    def save_file_as(self) -> None:
        path = filedialog.asksaveasfilename(title="Save TongaLang file", defaultextension=".tg", filetypes=[("TongaLang files", "*.tg"), ("All files", "*.*")])
        if not path:
            return
        self.current_file = Path(path)
        self._write_current_file(self.current_file)

    def _write_current_file(self, path: Path) -> None:
        try:
            path.write_text(self._get_source(), encoding="utf-8")
        except OSError as error:
            self._handle_tongalang_error(SourceWriteError(path, str(error)))
            return
        self.file_label_var.set(path.name)
        self._log("Info", f"Saved {path}")

    def _get_source(self) -> str:
        return self.editor.get("1.0", "end-1c")

    def _set_editor_text(self, text: str) -> None:
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self.editor.edit_modified(False)
        self._editor_revision += 1
        self.highlighter.highlight()
        self.highlighter.highlight_current_line()
        self._update_line_numbers()
        self._update_cursor()
        self._schedule_live_analysis()

    def _on_editor_activity(self, _event=None) -> None:
        self._update_line_numbers()
        self._update_cursor()

    def _on_editor_modified(self, _event=None) -> None:
        if not self.editor.edit_modified():
            return
        self.editor.edit_modified(False)
        self._editor_revision += 1
        self._on_editor_activity()
        self._schedule_live_analysis()

    def _schedule_live_analysis(self) -> None:
        if not hasattr(self, "editor"):
            return
        if self._analysis_after_id is not None:
            try:
                self.root.after_cancel(self._analysis_after_id)
            except tk.TclError:
                pass
        self._analysis_after_id = self.root.after(350, self._start_live_analysis)

    def _start_live_analysis(self) -> None:
        self._analysis_after_id = None
        source = self._get_source()
        revision = self._editor_revision

        def worker() -> None:
            try:
                diagnostics = analyze_source(source)
            except Exception as error:
                diagnostics = (diagnostic_from_exception(error),)
            self._schedule(lambda: self._accept_live_diagnostics(revision, source, diagnostics))

        threading.Thread(target=worker, daemon=True).start()

    def _accept_live_diagnostics(self, revision: int, source: str, diagnostics: tuple[Diagnostic, ...]) -> None:
        if revision != self._editor_revision or source != self._get_source():
            return
        previous = tuple((item.code, item.span) for item in self.current_diagnostics)
        incoming = tuple((item.code, item.span) for item in diagnostics)
        self._set_diagnostics(diagnostics, expand=bool(diagnostics) and incoming != previous)

    def _set_diagnostics(self, diagnostics: Iterable[Diagnostic], *, expand: bool = False) -> None:
        self.current_diagnostics = tuple(diagnostics)
        self.selected_diagnostic_index = None
        self.problems_tree.delete(*self.problems_tree.get_children(""))
        for index, diagnostic in enumerate(self.current_diagnostics):
            if diagnostic.span is None:
                location = "General"
            else:
                location = f"{diagnostic.span.start_line}:{diagnostic.span.start_column}"
            self.problems_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(diagnostic.code, location, diagnostic.summary(self.state.error_display_mode)),
            )
        count = len(self.current_diagnostics)
        self.problems_heading_var.set(f"Problems ({count})")
        if count:
            self.problems_tree.selection_set("0")
            self.problems_tree.focus("0")
            self._show_problem(0)
            if expand and not (self.pending_input and self.dock_view == DockView.INPUT):
                self.show_dock(DockView.PROBLEMS, expand=True)
        else:
            self.problem_detail_var.set("No problems detected. The code is ready to run.")
            self.highlighter.clear_error_highlight()
            for child in self.problem_fix_frame.winfo_children():
                child.destroy()
            if self.problems_expanded and not self.problems_pinned_open:
                self.collapse_dock()
        self._refresh_dock_controls()

    def toggle_problems(self, *, force: bool | None = None, user_action: bool = False) -> None:
        if user_action and self.active_view not in self.workspace_view_names:
            self.switch_view("Editor")
        target = not (self.dock_view == DockView.PROBLEMS and self.dock_expanded) if force is None else force
        if target:
            self.show_dock(DockView.PROBLEMS, expand=True, user_action=user_action)
        elif self.dock_view == DockView.PROBLEMS:
            self.collapse_dock(user_action=user_action)
        if user_action:
            self.problems_pinned_open = target
            self._log("Info", "Problems pane expanded" if target else "Problems pane collapsed")

    def toggle_input_dock(self, *, force: bool | None = None, user_action: bool = False) -> None:
        if user_action and self.active_view not in self.workspace_view_names:
            self.switch_view("Output")
        target = not (self.dock_view == DockView.INPUT and self.dock_expanded) if force is None else force
        if target:
            self.show_dock(DockView.INPUT, expand=True, user_action=user_action)
        elif self.dock_view == DockView.INPUT:
            self.collapse_dock(user_action=user_action)

    def show_dock(self, view: DockView, *, expand: bool = True, user_action: bool = False) -> None:
        self.dock_view = DockView(view)
        if self.dock_view == DockView.PROBLEMS:
            self.problems_panel.tkraise()
        else:
            self.input_panel.tkraise()
        if expand:
            self.expand_dock()
        else:
            self.collapse_dock(user_action=user_action)
        self._refresh_dock_controls()

    def expand_dock(self) -> None:
        self.dock_body.grid()
        self.workspace_paned.paneconfigure(self.dock_shell, minsize=145)
        self.dock_expanded = True
        self.problems_expanded = self.dock_view == DockView.PROBLEMS
        self.root.after_idle(self._position_dock_sash)
        self._refresh_dock_controls()

    def collapse_dock(self, *, user_action: bool = False) -> None:
        if self.dock_expanded:
            current_height = self.dock_shell.winfo_height()
            if current_height >= 145:
                self.dock_height = current_height
        self.dock_body.grid_remove()
        self.workspace_paned.paneconfigure(self.dock_shell, minsize=42)
        self.dock_expanded = False
        self.problems_expanded = False
        if user_action and self.dock_view == DockView.PROBLEMS:
            self.problems_pinned_open = False
        self.root.after_idle(self._position_dock_sash)
        self._refresh_dock_controls()

    def _refresh_dock_controls(self) -> None:
        if not hasattr(self, "problems_toggle"):
            return
        self.problems_expanded = self.dock_expanded and self.dock_view == DockView.PROBLEMS
        self.problems_toggle.configure(relief="sunken" if self.dock_view == DockView.PROBLEMS else "flat")
        self.input_toggle.configure(relief="sunken" if self.dock_view == DockView.INPUT else "flat")
        self.input_toggle_var.set("Program Input (needed)" if self.pending_input else "Program Input")
        self.dock_collapse_button.configure(state="normal" if self.dock_expanded else "disabled")
        if self.dock_view == DockView.PROBLEMS:
            count = len(self.current_diagnostics)
            self.dock_status_var.set(f"{count} problem{'s' if count != 1 else ''} detected")
        else:
            self.dock_status_var.set("Waiting for program input" if self.pending_input else "No input request is pending")

    def _position_problem_sash(self) -> None:
        self._position_dock_sash()

    def _position_dock_sash(self) -> None:
        try:
            height = self.workspace_paned.winfo_height()
            reserve = self.dock_height if self.dock_expanded else max(42, self.dock_shell.winfo_reqheight())
            self.workspace_paned.sash_place(0, 0, max(150, height - reserve))
        except tk.TclError:
            return

    def _on_problem_selected(self, _event=None) -> None:
        selected = self.problems_tree.selection()
        if not selected:
            return
        self._show_problem(int(selected[0]))

    def _show_problem(self, index: int) -> None:
        if not 0 <= index < len(self.current_diagnostics):
            return
        self.selected_diagnostic_index = index
        diagnostic = self.current_diagnostics[index]
        if self.state.error_display_mode == "tonga":
            text = f"[{diagnostic.code}] {diagnostic.summary_tonga}\n\n{diagnostic.detail_tonga}"
        else:
            text = (
                f"[{diagnostic.code}] {diagnostic.summary_english}\n"
                f"Mulubizyo: {diagnostic.summary_tonga}\n\n"
                f"How to fix it: {diagnostic.detail_english}\n"
                f"Langulukila: {diagnostic.detail_tonga}"
            )
        guidance = [fix.explanation_english for fix in diagnostic.fixes if not fix.is_editable]
        if guidance and self.state.error_display_mode != "tonga":
            text += "\n\n" + "\n".join(guidance)
        self.problem_detail_var.set(text)
        for child in self.problem_fix_frame.winfo_children():
            child.destroy()
        editable = [fix for fix in diagnostic.fixes if fix.is_editable]
        for fix in editable:
            title = fix.title_tonga if self.state.error_display_mode == "tonga" else fix.title_english
            tk.Button(
                self.problem_fix_frame,
                text=f"Apply Fix: {title}",
                command=lambda selected_fix=fix: self.apply_problem_fix(selected_fix),
            ).pack(side="left", padx=(0, 6), pady=2)
        self._highlight_diagnostic(diagnostic)

    def _highlight_diagnostic(self, diagnostic: Diagnostic) -> None:
        if diagnostic.span is None:
            self.highlighter.clear_error_highlight()
            return
        start = f"{diagnostic.span.start_line}.{diagnostic.span.start_column - 1}"
        end = f"{diagnostic.span.end_line}.{diagnostic.span.end_column - 1}"
        self.highlighter.highlight_error_span(start, end)

    def go_to_selected_problem(self) -> None:
        if self.selected_diagnostic_index is None:
            return
        diagnostic = self.current_diagnostics[self.selected_diagnostic_index]
        if diagnostic.span is None:
            return
        self.switch_view("Editor")
        index = f"{diagnostic.span.start_line}.{diagnostic.span.start_column - 1}"
        self.editor.mark_set("insert", index)
        self.editor.see(index)
        self.editor.focus_set()
        self._highlight_diagnostic(diagnostic)

    def apply_problem_fix(self, fix: SuggestedFix) -> None:
        source = self._get_source()
        try:
            apply_fix(source, fix)
        except ValueError as error:
            self.problem_detail_var.set(str(error))
            self._schedule_live_analysis()
            return
        auto_separators = bool(int(self.editor.cget("autoseparators")))
        self.editor.configure(autoseparators=False)
        self.editor.edit_separator()
        ordered_edits = sorted(
            fix.edits,
            key=lambda edit: (edit.span.start_line, edit.span.start_column),
            reverse=True,
        )
        for edit in ordered_edits:
            start = f"{edit.span.start_line}.{edit.span.start_column - 1}"
            end = f"{edit.span.end_line}.{edit.span.end_column - 1}"
            self.editor.delete(start, end)
            if edit.replacement:
                self.editor.insert(start, edit.replacement)
        self.editor.edit_separator()
        self.editor.configure(autoseparators=auto_separators)
        self.editor.edit_modified(False)
        self._editor_revision += 1
        self.highlighter.highlight()
        self._update_line_numbers()
        self._update_cursor()
        self._log("Info", f"Applied suggested fix: {fix.fix_id}")
        self._start_live_analysis()
        self.editor.focus_set()

    def copy_problem_details(self) -> None:
        if self.selected_diagnostic_index is None:
            return
        diagnostic = self.current_diagnostics[self.selected_diagnostic_index]
        details = diagnostic.technical_details or self.problem_detail_var.get()
        self.root.clipboard_clear()
        self.root.clipboard_append(details)
        self._log("Info", f"Copied diagnostic details for {diagnostic.code}")

    def _select_relative_problem(self, direction: int):
        if not self.current_diagnostics:
            return "break"
        current = self.selected_diagnostic_index if self.selected_diagnostic_index is not None else -1
        index = (current + direction) % len(self.current_diagnostics)
        self.problems_tree.selection_set(str(index))
        self.problems_tree.focus(str(index))
        self.problems_tree.see(str(index))
        self._show_problem(index)
        return "break"

    def _update_cursor(self) -> None:
        line, column = self.editor.index("insert").split(".")
        self.cursor_var.set(f"Ln {line}, Col {int(column) + 1}")

    def _insert_spaces(self, _event=None):
        self.editor.insert("insert", "    ")
        return "break"

    def _auto_indent(self, _event=None):
        current_line = self.editor.get("insert linestart", "insert")
        indent = current_line[: len(current_line) - len(current_line.lstrip())]
        if current_line.rstrip().endswith("{"):
            indent += "    "
        self.editor.insert("insert", "\n" + indent)
        return "break"

    def _scroll_editor(self, *args) -> None:
        self.editor.yview(*args)
        self.line_numbers.yview(*args)

    def _scroll_editor_horizontally(self, event):
        delta = getattr(event, "delta", 0)
        if not delta:
            return None
        units = -max(1, abs(int(delta / 120))) if delta > 0 else max(1, abs(int(delta / 120)))
        self.editor.xview_scroll(units, "units")
        return "break"

    def _on_editor_scroll(self, first: str, last: str, scrollbar: ttk.Scrollbar) -> None:
        scrollbar.set(first, last)
        self.line_numbers.yview_moveto(first)
        self._update_line_numbers()

    def _update_line_numbers(self) -> None:
        if not self.state.show_line_numbers:
            self.line_numbers.grid_remove()
            return
        self.line_numbers.grid()
        source = self.editor.get("1.0", "end-1c")
        line_count = max(1, source.count("\n") + 1)
        text = "\n".join(str(i) for i in range(1, line_count + 1)) + "\n"
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", text)
        self.line_numbers.configure(state="disabled")
        self.line_numbers.yview_moveto(self.editor.yview()[0])

    # ========================================================
    # Execution
    # ========================================================

    def run_program(self) -> None:
        if self.execution_state in (ExecutionState.RUNNING, ExecutionState.WAITING_FOR_INPUT):
            self._log("Warning", "Program is already running")
            return

        self.highlighter.clear_error_highlight()
        if self.state.auto_clear_output:
            self.clear_output()
        self.clear_input_state()
        source = self._get_source()
        try:
            static_diagnostics = analyze_source(source)
        except Exception as error:
            static_diagnostics = (diagnostic_from_exception(error),)
        if static_diagnostics:
            self._set_diagnostics(static_diagnostics, expand=True)
            self._set_execution_state(ExecutionState.ERROR)
            self.execution_summary_var.set("Correct the highlighted problem before running")
            self._append_output(self._format_diagnostic(static_diagnostics[0]) + "\n")
            self._log("Error", f"Static check stopped execution: {static_diagnostics[0].code}")
            self.switch_view("Editor")
            self.go_to_selected_problem()
            return

        self._set_diagnostics((), expand=False)
        self.collapse_dock()
        self.last_started_at = time.time()
        self._set_execution_state(ExecutionState.RUNNING)
        self.switch_view("Output")

        self._log("Info", "Tokenizer and parser starting")
        self.input_queue = BlockingInputQueue()
        self.stop_event.clear()

        thread = threading.Thread(target=self._run_program_worker, args=(source, self.input_queue), daemon=True)
        thread.start()

    def _run_program_worker(self, source: str, input_queue: BlockingInputQueue) -> None:
        original_input = builtins.input
        writer = QueueTextWriter(lambda text: self._schedule(lambda: self._append_output(text)))
        provider = RuntimeInputProvider(
            on_prompt=lambda prompt: self._schedule(lambda: self._enter_waiting_for_input(prompt)),
            wait_for_value=input_queue.wait,
        )
        builtins.input = provider

        try:
            with contextlib.redirect_stdout(writer):
                self._schedule(lambda: self._log("Info", "Parsing started"))
                program = parse_source(source)
                self._schedule(lambda: self._log("Info", "AST generated"))
                self._schedule(lambda: self._load_ast_tree(program))
                self._schedule(lambda: self._log("Info", "Execution started"))
                Interpreter(
                    max_loop_iterations=self.state.max_loop_iterations,
                    max_call_depth=self.state.max_call_depth,
                    should_stop=self.stop_event.is_set,
                ).interpret(program)
        except ExecutionCancelledError:
            self._schedule(self._finish_cancelled)
        except TongaLangError as error:
            self._schedule(lambda error=error: self._handle_tongalang_error(error))
        except Exception as error:
            self._schedule(lambda error=error: self._handle_internal_error(error))
        else:
            self._schedule(self._finish_execution)
        finally:
            builtins.input = original_input

    def submit_input(self) -> None:
        if not self.pending_input or self.input_queue is None:
            return
        value = self.input_entry.get()
        self.input_entry.delete(0, "end")
        self.pending_input = False
        self.pending_input_var.set("Status: input submitted, execution resuming")
        self.input_submit.configure(state="disabled")
        self.input_entry.configure(state="disabled")
        visible_value = value if value != "" else "[empty]"
        self._append_output(f"> {visible_value}\n")
        self.input_queue.submit(value)
        self._set_execution_state(ExecutionState.RUNNING)
        self.switch_view("Output")
        self.collapse_dock()
        self._refresh_dock_controls()
        self._log("Info", f"Input submitted: {value!r}")

    def stop_program(self) -> None:
        if self.execution_state not in (ExecutionState.RUNNING, ExecutionState.WAITING_FOR_INPUT):
            self._log("Warning", "No running program is available to stop")
            return
        self.stop_event.set()
        if self.execution_state == ExecutionState.WAITING_FOR_INPUT and self.input_queue is not None:
            self.pending_input = False
            self.input_entry.configure(state="disabled")
            self.input_submit.configure(state="disabled")
            self.input_queue.submit("")
            self.collapse_dock()
            self._refresh_dock_controls()
        self.execution_summary_var.set("Stopping safely...")
        self._log("Warning", "Safe stop requested")

    def _enter_waiting_for_input(self, prompt: str) -> None:
        self.pending_input = True
        self.current_input_prompt = prompt
        self.input_prompt_var.set(f"Prompt: {prompt}")
        self.pending_input_var.set("Status: waiting for user input")
        self.input_entry.configure(state="normal")
        self.input_submit.configure(state="normal")
        self._set_execution_state(ExecutionState.WAITING_FOR_INPUT)
        self.switch_view("Output")
        self._append_output(f"\n[Input requested] {prompt}\n")
        self.show_dock(DockView.INPUT, expand=True)
        self.input_entry.focus_set()
        self._log("Info", f"Waiting for input: {prompt}")

    def _finish_execution(self) -> None:
        self._set_execution_state(ExecutionState.FINISHED)
        elapsed = self._elapsed_text()
        self.execution_summary_var.set(f"Finished in {elapsed}")
        self.pending_input = False
        self.pending_input_var.set("Status: idle")
        self.input_entry.configure(state="disabled")
        self.input_submit.configure(state="disabled")
        if self.dock_view == DockView.INPUT and self.dock_expanded:
            self.collapse_dock()
        self._refresh_dock_controls()
        self._log("Info", f"Execution finished in {elapsed}")

    def _finish_cancelled(self) -> None:
        self._set_execution_state(ExecutionState.READY)
        elapsed = self._elapsed_text()
        self.execution_summary_var.set(f"Stopped safely after {elapsed}")
        self.pending_input = False
        self.pending_input_var.set("Status: stopped")
        self.input_submit.configure(state="disabled")
        self.input_entry.configure(state="disabled")
        if self.dock_view == DockView.INPUT and self.dock_expanded:
            self.collapse_dock()
        self._refresh_dock_controls()
        self._append_output("\n[TL-R113] Program stopped safely.\n")
        self._log("Warning", f"Execution stopped safely after {elapsed}")

    def _handle_tongalang_error(self, error: TongaLangError) -> None:
        message = self._format_tongalang_error(error)
        self._append_output(message + "\n")
        diagnostic = diagnostic_from_error(error, self._get_source())
        self._set_diagnostics((diagnostic,), expand=True)
        self._set_execution_state(ExecutionState.ERROR)
        self.execution_summary_var.set("Program stopped with a TongaLang error")
        self._log("Error", message.replace("\n", " | "))
        self.switch_view("Editor")
        self.go_to_selected_problem()

    def _handle_internal_error(self, error: Exception) -> None:
        message = self._format_internal_error(error)
        self._append_output(message + "\n")
        self._set_diagnostics((diagnostic_from_exception(error),), expand=True)
        self._set_execution_state(ExecutionState.ERROR)
        self.execution_summary_var.set("Program stopped with an internal error")
        self._log("Error", f"Unexpected internal error: {error}")
        self.switch_view("Editor")

    def _format_tongalang_error(self, error: TongaLangError) -> str:
        return error.format_message(mode=self.state.error_display_mode, source=self._get_source())

    def _format_internal_error(self, error: Exception) -> str:
        if self.state.error_display_mode == "tonga":
            return (
                "Mulubizyo: Kwaba mulubizyo uutazibidwe.\n"
                "Langulukila: Code yako tiyasandulwa. Kobweza naa kopa technical details."
            )
        return (
            "Mulubizyo: Kwaba mulubizyo uutazibidwe.\n"
            "Error: The IDE encountered an unexpected internal problem.\n"
            "Hint: Your code was not changed. Try again or copy the technical details."
        )

    def _format_diagnostic(self, diagnostic: Diagnostic) -> str:
        if self.state.error_display_mode == "tonga":
            parts = [f"[{diagnostic.code}] {diagnostic.category_tonga}"]
        else:
            parts = [f"[{diagnostic.code}] {diagnostic.category_english}"]
        if diagnostic.span is not None:
            parts.append(f"Line {diagnostic.span.start_line}, Column {diagnostic.span.start_column}")
            source_lines = self._get_source().splitlines()
            if 1 <= diagnostic.span.start_line <= len(source_lines):
                text = source_lines[diagnostic.span.start_line - 1]
                caret = " " * max(0, diagnostic.span.start_column - 1) + "^"
                parts.extend((f"{diagnostic.span.start_line:>4} | {text}", f"     | {caret}"))
        parts.append(f"Mulubizyo: {diagnostic.summary_tonga}")
        if self.state.error_display_mode != "tonga":
            parts.append(f"Error: {diagnostic.summary_english}")
        parts.append(f"Langulukila: {diagnostic.detail_tonga}")
        if self.state.error_display_mode != "tonga":
            parts.append(f"Hint: {diagnostic.detail_english}")
        return "\n".join(parts)

    def _set_execution_state(self, state: ExecutionState) -> None:
        self.execution_state = state
        self.status_var.set(f"Status: {state.value}")

    def _elapsed_text(self) -> str:
        if self.last_started_at is None:
            return "0.00s"
        return f"{time.time() - self.last_started_at:.2f}s"

    def _schedule(self, callback) -> None:
        if threading.current_thread() is threading.main_thread():
            callback()
            return
        self.ui_queue.put(callback)

    def _poll_ui_queue(self) -> None:
        while True:
            try:
                callback = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            callback()
        try:
            self.root.after(30, self._poll_ui_queue)
        except tk.TclError:
            return

    # ========================================================
    # Output, Input, Console
    # ========================================================

    def _append_output(self, text: str) -> None:
        self.output_text.configure(state="normal")
        self.output_text.insert("end", text)
        self.output_text.see("end")
        self.output_text.configure(state="disabled")

    def clear_output(self) -> None:
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        self.execution_summary_var.set("Output cleared")

    def clear_input_state(self) -> None:
        self.pending_input = False
        self.current_input_prompt = ""
        self.input_prompt_var.set("No bala() input request is pending.")
        self.pending_input_var.set("Status: idle")
        self.input_entry.delete(0, "end")
        self.input_entry.configure(state="disabled")
        self.input_submit.configure(state="disabled")
        if self.dock_view == DockView.INPUT and self.dock_expanded:
            self.collapse_dock()
        self._refresh_dock_controls()

    def clear_console(self) -> None:
        self.console_events.clear()
        self._render_console()

    def _log(self, level: str, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.console_events.append((timestamp, level, message))
        self._render_console()

    def _render_console(self) -> None:
        if not hasattr(self, "console_text"):
            return
        selected = self.log_filter.get()
        self.console_text.configure(state="normal")
        self.console_text.delete("1.0", "end")
        for timestamp, level, message in self.console_events:
            if selected != "All" and selected != level:
                continue
            self.console_text.insert("end", f"[{timestamp}] {level.upper():7} {message}\n")
        self.console_text.configure(state="disabled")

    # ========================================================
    # AST
    # ========================================================

    def refresh_ast(self) -> None:
        self._log("Info", "AST refresh requested")
        try:
            program = parse_source(self._get_source())
        except TongaLangError as error:
            self._handle_tongalang_error(error)
            return
        self._load_ast_tree(program)
        self.switch_view("AST")

    def _load_ast_tree(self, program) -> None:
        self.ast_tree.delete(*self.ast_tree.get_children(""))
        self.ast_rows.clear()
        rows = build_ast_tree_rows(program)
        for row in rows:
            self.ast_rows[row.node_id] = row
            line_text = "" if row.line is None else str(row.line)
            self.ast_tree.insert(
                row.parent_id,
                "end",
                iid=row.node_id,
                text=row.label,
                values=(row.node_type, line_text),
                open=row.depth < 2,
            )
        self.ast_canvas.set_rows(rows)
        self.ast_text = format_ast(program)
        max_depth = max((row.depth for row in rows), default=0)
        located = sum(1 for row in rows if row.line is not None)
        self.ast_status_var.set(f"{len(rows)} nodes  |  depth {max_depth}  |  {located} linked to source")
        self.selected_ast_node_id = rows[0].node_id if rows else None
        if rows:
            self.ast_canvas.select(rows[0].node_id)
        else:
            self._set_ast_detail("No AST nodes were generated.")
        self._log("Debug", "AST tree loaded")

    def _set_ast_detail(self, text: str) -> None:
        self.ast_detail.configure(state="normal")
        self.ast_detail.delete("1.0", "end")
        self.ast_detail.insert("1.0", text)
        self.ast_detail.configure(state="disabled")

    def _on_ast_select(self, event_or_node_id=None) -> None:
        if isinstance(event_or_node_id, str):
            node_id = event_or_node_id
            if self.ast_tree.exists(node_id):
                self.ast_tree.selection_set(node_id)
                self.ast_tree.see(node_id)
        else:
            selected = self.ast_tree.selection()
            if not selected:
                return
            node_id = selected[0]
            if self.ast_canvas.selected_id != node_id:
                self.ast_canvas.selected_id = node_id
                self.ast_canvas.redraw()
        row = self.ast_rows.get(node_id)
        if row is None:
            return
        self.selected_ast_node_id = node_id
        location = "unknown" if row.line is None else f"line {row.line}, column {row.column or 1}"
        child_count = sum(1 for item in self.ast_rows.values() if item.parent_id == row.node_id)
        source_excerpt = self._ast_source_excerpt(row.line, row.column)
        self._set_ast_detail(
            f"Node: {row.label}\n"
            f"Type: {row.node_type}\n"
            f"Source: {location}\n\n"
            f"Purpose\n{row.detail}\n\n"
            f"Structure\nDepth: {row.depth}\nChildren: {child_count}\n\n"
            f"Source excerpt\n{source_excerpt}\n"
        )

    def _ast_source_excerpt(self, line: int | None, column: int | None) -> str:
        if line is None:
            return "No source location is attached to this node."
        source_lines = self._get_source().splitlines()
        if not 1 <= line <= len(source_lines):
            return "The recorded source line is outside the current editor content."
        text = source_lines[line - 1]
        caret = " " * max(0, (column or 1) - 1) + "^"
        return f"{line:>4} | {text}\n     | {caret}"

    def go_to_ast_source(self) -> None:
        row = self.ast_rows.get(self.selected_ast_node_id or "")
        if row is None or row.line is None:
            return
        self.switch_view("Editor")
        index = f"{row.line}.{max(0, (row.column or 1) - 1)}"
        self.editor.mark_set("insert", index)
        self.editor.see(index)
        self.editor.focus_set()
        self.highlighter.highlight_current_line()

    def find_ast_node(self) -> None:
        query = self.ast_search_var.get().strip().lower()
        if not query:
            return
        ordered_ids = list(self.ast_rows)
        if self.selected_ast_node_id in ordered_ids:
            start = ordered_ids.index(self.selected_ast_node_id) + 1
            ordered_ids = ordered_ids[start:] + ordered_ids[:start]
        for node_id in ordered_ids:
            row = self.ast_rows[node_id]
            if query in row.label.lower() or query in row.node_type.lower():
                self.ast_canvas.select(node_id)
                return
        self.ast_status_var.set(f'No AST node matches "{query}".')

    def _set_tree_open(self, open_value: bool) -> None:
        def visit(item: str) -> None:
            self.ast_tree.item(item, open=open_value)
            for child in self.ast_tree.get_children(item):
                visit(child)

        for root_item in self.ast_tree.get_children(""):
            visit(root_item)

    def copy_ast(self) -> None:
        text = self.ast_text or self.ast_detail.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._log("Info", "AST detail copied")

    # ========================================================
    # Settings
    # ========================================================

    def _setting_label(self, parent: tk.Widget, text: str, row: int) -> None:
        tk.Label(parent, text=text, anchor="w").grid(row=row, column=0, sticky="w", padx=14, pady=4)

    def _update_theme_from_settings(self) -> None:
        self.state.theme_name = self.theme_var.get()
        self._apply_theme()
        self._log("Info", f"Theme switched to {self.state.theme_name}")

    def _update_error_mode_from_settings(self) -> None:
        self.state.error_display_mode = self.error_mode_var.get()
        if self.current_diagnostics:
            selected = self.selected_diagnostic_index or 0
            self._set_diagnostics(self.current_diagnostics, expand=self.problems_expanded)
            if selected < len(self.current_diagnostics):
                self.problems_tree.selection_set(str(selected))
                self._show_problem(selected)
        self._log("Info", f"Error language switched to {self.state.error_display_mode}")

    def apply_editor_settings(self) -> bool:
        try:
            font_size = int(self.font_size_var.get())
            max_loop_iterations = int(self.max_loop_var.get())
            max_call_depth = int(self.max_call_depth_var.get())
        except (ValueError, tk.TclError):
            self.settings_error_var.set("Use whole numbers for font size and execution safety limits.")
            return False
        if not 9 <= font_size <= 24:
            self.settings_error_var.set("Font size must be between 9 and 24.")
            return False
        if not 1 <= max_loop_iterations <= 1_000_000:
            self.settings_error_var.set("Max loop iterations must be between 1 and 1,000,000.")
            return False
        if not 1 <= max_call_depth <= 10_000:
            self.settings_error_var.set("Max function-call depth must be between 1 and 10,000.")
            return False

        self.settings_error_var.set("")
        self.state.font_family = self.font_family_var.get().strip() or "Consolas"
        self.state.font_size = font_size
        self.state.error_display_mode = self.error_mode_var.get()
        self.state.max_loop_iterations = max_loop_iterations
        self.state.max_call_depth = max_call_depth
        self.state.show_line_numbers = bool(self.show_lines_var.get())
        self.state.highlight_current_line = bool(self.current_line_var.get())
        self.state.auto_clear_output = bool(self.auto_clear_var.get())
        self.highlighter.set_current_line_enabled(self.state.highlight_current_line)
        self._apply_theme()
        self._log("Info", "Settings applied")
        return True

    def choose_syntax_color(self, color_key: str) -> None:
        current = self.state.syntax_colors.get(color_key, getattr(DEFAULT_SYNTAX_THEMES[self.state.theme_name], color_key))
        _, value = colorchooser.askcolor(color=current, title=f"Choose {color_key} color")
        if not value:
            return
        self.state.syntax_colors[color_key] = value
        self.highlighter.update_color(color_key, value)
        self._refresh_color_swatches()
        self._log("Info", f"Syntax color changed: {color_key}")

    def reset_defaults(self) -> None:
        self.state = IDEState(theme_name=self.theme_var.get())
        self.theme_var.set(self.state.theme_name)
        self.error_mode_var.set(self.state.error_display_mode)
        self.font_family_var.set(self.state.font_family)
        self.font_size_var.set(self.state.font_size)
        self.max_loop_var.set(self.state.max_loop_iterations)
        self.max_call_depth_var.set(self.state.max_call_depth)
        self.show_lines_var.set(self.state.show_line_numbers)
        self.current_line_var.set(self.state.highlight_current_line)
        self.auto_clear_var.set(self.state.auto_clear_output)
        self.highlighter.reset_custom_colors()
        self.settings_error_var.set("")
        self._apply_theme()
        self._log("Info", "Settings reset to defaults")

    def _syntax_color_value(self, color_key: str) -> str:
        return self.state.syntax_colors.get(color_key, getattr(DEFAULT_SYNTAX_THEMES[self.state.theme_name], color_key))

    def _refresh_color_swatches(self) -> None:
        for color_key, swatch in getattr(self, "color_swatches", {}).items():
            swatch.configure(
                bg=self._syntax_color_value(color_key),
                highlightbackground=THEMES[self.state.theme_name]["border"],
            )

    def view_ast_from_settings(self) -> None:
        self.refresh_ast()

    def view_console_from_settings(self) -> None:
        self._render_console()
        self.switch_view("Console")

    def view_grammar_from_settings(self) -> None:
        self.refresh_grammar_reference()
        self.switch_view("Grammar")

    def refresh_grammar_reference(self) -> None:
        self.grammar_text.configure(state="normal")
        self.grammar_text.delete("1.0", "end")
        self.grammar_text.insert("1.0", self._grammar_content())
        self.grammar_text.configure(state="disabled")
        self._log("Info", "Grammar reference refreshed")

    # ========================================================
    # Utilities and About
    # ========================================================

    def copy_text(self, widget: tk.Text) -> None:
        text = widget.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._log("Info", "Text copied to clipboard")

    def _grammar_content(self) -> str:
        profile = self.profile
        grammar = (
            "program -> top_level_item*\n"
            "top_level_item -> function_decl | statement\n"
            "function_decl -> mulimo IDENT '(' parameters? ')' block\n"
            "main_entry -> mulimo matalikilo '(' ')' block\n"
            "block -> '{' statement* '}'\n"
            "statement -> variable_decl | assignment | output | if_stmt | while_stmt | for_range_stmt | do_until_stmt | break | return | expression\n"
            "variable_decl -> zina IDENT ('=' expression)?\n"
            "assignment -> IDENT '=' expression\n"
            "output -> amba '(' expression? ')'\n"
            "input_expression -> bala '(' expression? ')'\n"
            "if_stmt -> kuti expression block (naaba expression block)* (nakunyina block)?\n"
            "while_stmt -> kufumbwa expression block\n"
            "for_range_stmt -> induluka IDENT kuzwa expression kusika expression block\n"
            "do_until_stmt -> cita block kusikila expression\n"
            "break -> leka\n"
            "return -> pilula expression?\n"
            "expression -> logical_or, comparison, arithmetic, unary, call, literal, identifier, grouped expression\n"
        )
        return (
            "TongaLang Grammar Reference\n"
            "Generated from the current lexer, language profile, native function registry, and parser grammar.\n\n"
            "Keywords\n"
            f"{', '.join(profile.keywords)}\n\n"
            "Boolean Literals\n"
            f"{', '.join(profile.booleans)}\n\n"
            "Native Functions\n"
            f"{', '.join(profile.native_functions)}\n\n"
            "Operators and Symbols\n"
            f"Arithmetic: {', '.join(profile.arithmetic_operators)}\n"
            f"Assignment: {', '.join(profile.assignment_operators)}\n"
            f"Comparison: {', '.join(profile.comparison_operators)}\n"
            f"Logical: {', '.join(profile.logical_operators)}\n"
            f"Grouping and separators: {', '.join(profile.grouping_symbols)}\n\n"
            "High-Level Grammar Summary\n"
            f"{grammar}\n"
            "Notes\n"
            "- Execution starts from mulimo matalikilo().\n"
            "- bala(...) is implemented as an expression and can be stored with zina or assignment.\n"
            "- amba(...) writes output; GUI error language settings do not translate user program output.\n"
            "- AST and console tools are intentionally opened from Settings only.\n"
        )

    def _about_content(self) -> str:
        return (
            "About TongaLang\n\n"
            f"Version: {__version__}\n\n"
            "Project Author\n"
            "Author: Leo Mabuku\n\n"
            "Academic Project Details\n"
            "Project: Implementation of a Programming Language Using Local Language\n"
            "Course: CS400 Project Seminars\n"
            "University: The Copperbelt University\n"
            "School: School of Information and Communication Technology\n"
            "Department: Department of Computer Science\n"
            "Author: Leo Mabuku\n"
            "Supervisor: Dr. Maybin Lengwe\n"
            "\nWhy the Project Exists\n"
            "TongaLang is a minimal interpreted educational programming language using Tonga-derived keywords. "
            "It is intended to reduce the introductory programming barrier for learners who understand local "
            "languages more naturally than English, while still demonstrating formal language design concepts.\n\n"
            "How TongaLang Works\n"
            "Source code -> Lexer tokens -> Parser AST -> Interpreter runtime -> Output/Input events\n\n"
            "IDE Input and Recovery\n"
            "Editor and Output share a collapsible dock. Problems is the default view. When bala() needs a "
            "value, Program Input opens automatically; the submitted value is recorded in Output before execution resumes.\n\n"
            "Supported Keywords:\n"
            f"{', '.join(self.profile.keywords)}\n\n"
            "Booleans:\n"
            f"{', '.join(self.profile.booleans)}\n\n"
            "Native Functions:\n"
            f"{', '.join(self.profile.native_functions)}\n\n"
            "Operators:\n"
            f"Logical: {', '.join(self.profile.logical_operators)}\n"
            f"Comparison: {', '.join(self.profile.comparison_operators)}\n"
            f"Arithmetic: {', '.join(self.profile.arithmetic_operators)}\n\n"

        )

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-o>", lambda _event: self.open_file())
        self.root.bind("<Control-s>", lambda _event: self.save_file())
        self.root.bind("<F5>", lambda _event: self.run_program())
        self.root.bind("<Control-r>", lambda _event: self.run_program())
        self.root.bind("<Alt-Left>", lambda _event: self.go_back())
        self.root.bind("<Alt-Right>", lambda _event: self.go_forward())
        self.root.bind("<Control-m>", lambda _event: self.toggle_sidebar())
        self.root.bind("<Control-Shift-P>", lambda _event: self.toggle_problems(force=True, user_action=True))
        self.root.bind("<Control-Shift-I>", lambda _event: self.toggle_input_dock(force=True, user_action=True))
        self.root.bind("<F8>", lambda _event: self._select_relative_problem(1))
        self.root.bind("<Shift-F8>", lambda _event: self._select_relative_problem(-1))


def main() -> None:
    root = tk.Tk()
    TongaLangGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
