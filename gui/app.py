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

from tongalang.ast_visualizer import format_ast
from tongalang.errors import ExecutionCancelledError, TongaLangError, TongaRuntimeError
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
        self.log_filter = tk.StringVar(value="All")
        self.console_events: list[tuple[str, str, str]] = []
        self.input_queue: BlockingInputQueue | None = None
        self.stop_event = threading.Event()
        self.pending_input = False
        self.last_started_at: float | None = None
        self.ast_rows: dict[str, ASTTreeNode] = {}
        self.ast_text = ""
        self.selected_ast_node_id: str | None = None
        self.ui_queue: queue.Queue = queue.Queue()
        self.color_swatches: dict[str, tk.Canvas] = {}

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
        self.topbar.columnconfigure(4, weight=1)

        self.sidebar_toggle = tk.Button(self.topbar, text="[<]", command=self.toggle_sidebar, width=5)
        self.sidebar_toggle.grid(row=0, column=0, padx=(10, 4), pady=8)

        self.run_button = tk.Button(self.topbar, text="Run", command=self.run_program, width=10)
        self.run_button.grid(row=0, column=1, padx=4, pady=8)
        tk.Button(self.topbar, text="Stop", command=self.stop_program, width=10).grid(row=0, column=2, padx=4, pady=8)
        tk.Button(self.topbar, text="Output", command=lambda: self.switch_view("Output"), width=10).grid(row=0, column=3, padx=4, pady=8)

        self.file_label_var = tk.StringVar(value="Untitled.tg")
        self.cursor_var = tk.StringVar(value="Ln 1, Col 1")
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(self.topbar, textvariable=self.status_var, anchor="e")
        self.status_label.grid(row=0, column=4, sticky="e", padx=12)

        self.sidebar = tk.Frame(self.root, width=190)
        self.sidebar.grid(row=1, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        self.content = tk.Frame(self.root)
        self.content.grid(row=1, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        self.nav_buttons: dict[str, tk.Button] = {}
        self.views: dict[str, tk.Frame] = {}
        self._build_sidebar()
        self._build_views()
        self.switch_view("Editor")

    def _build_sidebar(self) -> None:
        title = tk.Label(self.sidebar, text="TongaLang", font=("Segoe UI", 15, "bold"), anchor="w")
        title.pack(fill="x", padx=14, pady=(14, 6))
        subtitle = tk.Label(self.sidebar, text="Interpreter IDE", anchor="w")
        subtitle.pack(fill="x", padx=14, pady=(0, 12))

        for view in ("Editor", "Input / I/O", "Settings", "About"):
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
        self._build_input_view()
        self._build_ast_view()
        self._build_console_view()
        self._build_settings_view()
        self._build_grammar_view()
        self._build_about_view()

    def _new_view(self, name: str) -> tk.Frame:
        frame = tk.Frame(self.content)
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
        editor_shell.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
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
        self.editor.bind("<Tab>", self._insert_spaces)
        self.editor.bind("<Return>", self._auto_indent)

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
        self.output_text.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 8))
        self.output_text.configure(state="disabled")

        output_input = tk.Frame(frame)
        output_input.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 14))
        output_input.columnconfigure(1, weight=1)
        self.output_prompt_var = tk.StringVar(value="Input: no pending bala() request")
        tk.Label(output_input, textvariable=self.output_prompt_var, anchor="w").grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        tk.Label(output_input, text="Program input").grid(row=1, column=0, sticky="w", padx=(0, 8))
        self.output_input_entry = tk.Entry(output_input, state="disabled")
        self.output_input_entry.grid(row=1, column=1, sticky="ew")
        self.output_input_entry.bind("<Return>", lambda _event: self.submit_input())
        self.output_input_submit = tk.Button(output_input, text="Submit", command=self.submit_input, state="disabled")
        self.output_input_submit.grid(row=1, column=2, padx=(8, 0))

    def _build_input_view(self) -> None:
        frame = self._new_view("Input / I/O")
        frame.rowconfigure(4, weight=1)
        frame.columnconfigure(0, weight=1)

        tk.Label(frame, text="Interactive Input / Output", font=("Segoe UI", 15, "bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))
        self.input_prompt_var = tk.StringVar(value="No input request is pending.")
        self.pending_input_var = tk.StringVar(value="Status: idle")
        tk.Label(frame, textvariable=self.input_prompt_var, anchor="w").grid(row=1, column=0, sticky="ew", padx=14)
        tk.Label(frame, textvariable=self.pending_input_var, anchor="w").grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))

        row = tk.Frame(frame)
        row.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 8))
        row.columnconfigure(0, weight=1)
        self.input_entry = tk.Entry(row)
        self.input_entry.grid(row=0, column=0, sticky="ew")
        self.input_entry.bind("<Return>", lambda _event: self.submit_input())
        self.input_submit = tk.Button(row, text="Submit", command=self.submit_input, state="disabled")
        self.input_submit.grid(row=0, column=1, padx=(8, 0))

        self.input_history = ScrolledText(frame, wrap="word", font=("Consolas", 10), height=12)
        self.input_history.grid(row=4, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.input_history.configure(state="disabled")

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
        frame.columnconfigure(1, weight=1)
        tk.Label(frame, text="Settings", font=("Segoe UI", 15, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(12, 12))

        self.theme_var = tk.StringVar(value=self.state.theme_name)
        self.error_mode_var = tk.StringVar(value=self.state.error_display_mode)
        self.font_family_var = tk.StringVar(value=self.state.font_family)
        self.font_size_var = tk.IntVar(value=self.state.font_size)
        self.max_loop_var = tk.IntVar(value=self.state.max_loop_iterations)
        self.max_call_depth_var = tk.IntVar(value=self.state.max_call_depth)
        self.show_lines_var = tk.BooleanVar(value=self.state.show_line_numbers)
        self.current_line_var = tk.BooleanVar(value=self.state.highlight_current_line)
        self.auto_clear_var = tk.BooleanVar(value=self.state.auto_clear_output)

        row = 1
        self._setting_label(frame, "Theme", row)
        ttk.Combobox(frame, textvariable=self.theme_var, values=("dark", "light"), state="readonly").grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        self.theme_var.trace_add("write", lambda *_args: self._update_theme_from_settings())
        row += 1

        self._setting_label(frame, "Error language", row)
        ttk.Combobox(
            frame,
            textvariable=self.error_mode_var,
            values=("bilingual", "tonga"),
            state="readonly",
        ).grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        self.error_mode_var.trace_add("write", lambda *_args: self._update_error_mode_from_settings())
        row += 1

        self._setting_label(frame, "Editor font", row)
        ttk.Combobox(frame, textvariable=self.font_family_var, values=AVAILABLE_EDITOR_FONTS, state="readonly").grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        row += 1

        self._setting_label(frame, "Font size", row)
        tk.Spinbox(frame, from_=9, to=24, textvariable=self.font_size_var, command=self.apply_editor_settings).grid(row=row, column=1, sticky="w", padx=8, pady=4)
        row += 1

        self._setting_label(frame, "Max loop iterations", row)
        tk.Spinbox(frame, from_=1, to=1000000, textvariable=self.max_loop_var).grid(row=row, column=1, sticky="w", padx=8, pady=4)
        row += 1

        self._setting_label(frame, "Max function-call depth", row)
        tk.Spinbox(frame, from_=1, to=10000, textvariable=self.max_call_depth_var).grid(row=row, column=1, sticky="w", padx=8, pady=4)
        row += 1

        options = (
            ("Show line numbers", self.show_lines_var),
            ("Highlight current line", self.current_line_var),
            ("Auto-clear output on run", self.auto_clear_var),
        )
        for text, variable in options:
            tk.Checkbutton(frame, text=text, variable=variable, command=self.apply_editor_settings).grid(row=row, column=1, sticky="w", padx=8, pady=4)
            row += 1

        tk.Label(frame, text="Language Tools", font=("Segoe UI", 12, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", padx=14, pady=(16, 6))
        row += 1
        tools = tk.Frame(frame)
        tools.grid(row=row, column=1, columnspan=2, sticky="w", padx=8, pady=4)
        tk.Button(tools, text="View AST", command=self.view_ast_from_settings).pack(side="left")
        tk.Button(tools, text="View Console", command=self.view_console_from_settings).pack(side="left", padx=8)
        tk.Button(tools, text="View Grammar", command=self.view_grammar_from_settings).pack(side="left")
        row += 1

        tk.Label(frame, text="Syntax Colors", font=("Segoe UI", 12, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", padx=14, pady=(16, 6))
        row += 1
        self.color_swatches = {}
        for color_key in ("keywords", "strings", "comments", "numbers", "native_functions", "operators", "current_line", "error_line", "ast_highlight"):
            self._setting_label(frame, color_key.replace("_", " ").title(), row)
            swatch = tk.Canvas(frame, width=32, height=18, highlightthickness=1)
            swatch.grid(row=row, column=1, sticky="w", padx=8, pady=3)
            self.color_swatches[color_key] = swatch
            tk.Button(frame, text="Choose", command=lambda key=color_key: self.choose_syntax_color(key)).grid(row=row, column=2, sticky="w", padx=8, pady=3)
            row += 1

        buttons = tk.Frame(frame)
        buttons.grid(row=row, column=1, sticky="w", padx=8, pady=(12, 0))
        tk.Button(buttons, text="Apply Settings", command=self.apply_editor_settings).pack(side="left")
        tk.Button(buttons, text="Reset Defaults", command=self.reset_defaults).pack(side="left", padx=8)

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
        self.about_text = ScrolledText(frame, wrap="word", font=("Consolas", 10))
        self.about_text.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.about_text.insert("1.0", self._about_content())
        self.about_text.configure(state="disabled")

    # ========================================================
    # Navigation and Theme
    # ========================================================

    def switch_view(self, name: str) -> None:
        self.active_view = name
        self.views[name].tkraise()
        for view_name, button in self.nav_buttons.items():
            button.configure(relief="flat")
            if view_name == name:
                button.configure(relief="sunken")

    def toggle_sidebar(self) -> None:
        self.sidebar_collapsed = not self.sidebar_collapsed
        if self.sidebar_collapsed:
            self.sidebar.grid_remove()
            self.content.grid_configure(row=1, column=0, columnspan=2, sticky="nsew")
            self.sidebar_toggle.configure(text="[>]")
        else:
            self.content.grid_configure(row=1, column=1, columnspan=1, sticky="nsew")
            self.sidebar.grid(row=1, column=0, sticky="ns")
            self.sidebar_toggle.configure(text="[<]")

    def _apply_theme(self) -> None:
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
            elif isinstance(widget, tk.Label):
                widget.configure(bg=self._background_for(widget.master, colors), fg=colors["text"])
            elif isinstance(widget, tk.Button):
                bg = colors["run"] if widget is self.run_button else colors["button"]
                widget.configure(bg=bg, fg=colors["text"], activebackground=colors["button_active"], relief="flat", bd=0)
            elif isinstance(widget, tk.Checkbutton):
                master_bg = self._background_for(widget.master, colors)
                widget.configure(bg=master_bg, fg=colors["text"], selectcolor=colors["panel_alt"], activebackground=master_bg)
            elif isinstance(widget, (tk.Entry, tk.Spinbox)):
                widget.configure(bg=colors["entry"], fg=colors["text"], insertbackground=colors["text"], relief="flat")
            elif isinstance(widget, tk.Text):
                widget.configure(bg=colors["panel_alt"], fg=colors["text"], insertbackground=colors["text"], relief="flat")

        self.status_label.configure(fg=colors["muted"])
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

    def _configure_tree_style(self, colors: dict[str, str]) -> None:
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=colors["panel_alt"], foreground=colors["text"], fieldbackground=colors["panel_alt"], bordercolor=colors["border"])
        style.configure("Treeview.Heading", background=colors["panel"], foreground=colors["text"])

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
        except OSError as error:
            messagebox.showerror("Open failed", str(error))
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
            messagebox.showerror("Save failed", str(error))
            return
        self.file_label_var.set(path.name)
        self._log("Info", f"Saved {path}")

    def _get_source(self) -> str:
        return self.editor.get("1.0", "end-1c")

    def _set_editor_text(self, text: str) -> None:
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self.highlighter.highlight()
        self.highlighter.highlight_current_line()
        self._update_line_numbers()
        self._update_cursor()

    def _on_editor_activity(self, _event=None) -> None:
        self._update_line_numbers()
        self._update_cursor()

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
        self.last_started_at = time.time()
        self._set_execution_state(ExecutionState.RUNNING)
        self.switch_view("Output")

        source = self._get_source()
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
        output_value = self.output_input_entry.get() if hasattr(self, "output_input_entry") else ""
        panel_value = self.input_entry.get()
        value = output_value if output_value != "" else panel_value
        if not self.pending_input or self.input_queue is None:
            return
        self.input_entry.delete(0, "end")
        if hasattr(self, "output_input_entry"):
            self.output_input_entry.delete(0, "end")
        self._append_input_history(self.input_prompt_var.get(), value)
        self.pending_input = False
        self.pending_input_var.set("Status: input submitted, execution resuming")
        self.input_submit.configure(state="disabled")
        if hasattr(self, "output_input_submit"):
            self.output_input_submit.configure(state="disabled")
            self.output_input_entry.configure(state="disabled")
            self.output_prompt_var.set("Input submitted; execution resuming")
        self.input_queue.submit(value)
        self._set_execution_state(ExecutionState.RUNNING)
        self._log("Info", f"Input submitted: {value!r}")

    def stop_program(self) -> None:
        if self.execution_state not in (ExecutionState.RUNNING, ExecutionState.WAITING_FOR_INPUT):
            self._log("Warning", "No running program is available to stop")
            return
        self.stop_event.set()
        if self.execution_state == ExecutionState.WAITING_FOR_INPUT and self.input_queue is not None:
            self.input_queue.submit("")
        self.execution_summary_var.set("Stopping safely...")
        self._log("Warning", "Safe stop requested")

    def _enter_waiting_for_input(self, prompt: str) -> None:
        self.pending_input = True
        self.output_prompt_var.set(f"Input needed: {prompt}")
        self.input_prompt_var.set(f"Prompt: {prompt}")
        self.pending_input_var.set("Status: waiting for user input")
        self.input_submit.configure(state="normal")
        self.output_input_entry.configure(state="normal")
        self.output_input_submit.configure(state="normal")
        self._set_execution_state(ExecutionState.WAITING_FOR_INPUT)
        self.switch_view("Output")
        self.output_input_entry.focus_set()
        self._log("Info", f"Waiting for input: {prompt}")

    def _finish_execution(self) -> None:
        self._set_execution_state(ExecutionState.FINISHED)
        elapsed = self._elapsed_text()
        self.execution_summary_var.set(f"Finished in {elapsed}")
        self.pending_input_var.set("Status: idle")
        self._log("Info", f"Execution finished in {elapsed}")

    def _finish_cancelled(self) -> None:
        self._set_execution_state(ExecutionState.READY)
        elapsed = self._elapsed_text()
        self.execution_summary_var.set(f"Stopped safely after {elapsed}")
        self.pending_input = False
        self.pending_input_var.set("Status: stopped")
        self.input_submit.configure(state="disabled")
        self.output_input_submit.configure(state="disabled")
        self.output_input_entry.configure(state="disabled")
        self._append_output("\n[TL-R113] Program stopped safely.\n")
        self._log("Warning", f"Execution stopped safely after {elapsed}")

    def _handle_tongalang_error(self, error: TongaLangError) -> None:
        message = self._format_tongalang_error(error)
        self._append_output(message + "\n")
        line = getattr(error, "line", None)
        if isinstance(line, int):
            self.highlighter.highlight_error_line(line)
        self._set_execution_state(ExecutionState.ERROR)
        self.execution_summary_var.set("Program stopped with a TongaLang error")
        self._log("Error", message.replace("\n", " | "))
        self.switch_view("Output")

    def _handle_internal_error(self, error: Exception) -> None:
        message = self._format_internal_error(error)
        self._append_output(message + "\n")
        self._set_execution_state(ExecutionState.ERROR)
        self.execution_summary_var.set("Program stopped with an internal error")
        self._log("Error", f"Unexpected internal error: {error}")
        self.switch_view("Output")

    def _format_tongalang_error(self, error: TongaLangError) -> str:
        return error.format_message(mode=self.state.error_display_mode, source=self._get_source())

    def _format_internal_error(self, error: Exception) -> str:
        if self.state.error_display_mode == "tonga":
            return (
                "Mulubizyo: Kwaba mulubizyo uutazibidwe.\n"
                f"Langulukila: Bona code naa tumizya uthenga uyu: {error}"
            )
        return (
            "Mulubizyo: Kwaba mulubizyo uutazibidwe.\n"
            f"Error: Unexpected internal error: {error}"
        )

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
        self.output_prompt_var.set("Input: no pending bala() request")
        self.input_prompt_var.set("No input request is pending.")
        self.pending_input_var.set("Status: idle")
        self.input_submit.configure(state="disabled")
        self.output_input_submit.configure(state="disabled")
        self.output_input_entry.configure(state="disabled")

    def _append_input_history(self, prompt: str, value: str) -> None:
        self.input_history.configure(state="normal")
        self.input_history.insert("end", f"{prompt}\n> {value}\n\n")
        self.input_history.see("end")
        self.input_history.configure(state="disabled")

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
        self._log("Info", f"Error language switched to {self.state.error_display_mode}")

    def apply_editor_settings(self) -> None:
        self.state.font_family = self.font_family_var.get().strip() or "Consolas"
        self.state.font_size = int(self.font_size_var.get())
        self.state.error_display_mode = self.error_mode_var.get()
        self.state.max_loop_iterations = int(self.max_loop_var.get())
        self.state.max_call_depth = int(self.max_call_depth_var.get())
        self.state.show_line_numbers = bool(self.show_lines_var.get())
        self.state.highlight_current_line = bool(self.current_line_var.get())
        self.state.auto_clear_output = bool(self.auto_clear_var.get())
        self._apply_theme()
        self._log("Info", "Settings applied")

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
            "TongaLang Educational IDE\n\n"
            "Project: Implementation of a Programming Language Using Local Language\n"
            "Course: CS400 Project Seminars\n"
            "University: The Copperbelt University\n"
            "School: School of Information and Communication Technology\n"
            "Department: Department of Computer Science\n"
            "Author: Leo Mabuku\n"
            "Supervisor: Dr. Maybin Lengwe\n"
            "Version: 0.3.0\n\n"
            "Description:\n"
            "TongaLang is a minimal interpreted educational programming language using Tonga-derived keywords. "
            "It is intended to reduce the introductory programming barrier for learners who understand local "
            "languages more naturally than English, while still demonstrating formal language design concepts.\n\n"
            "Architecture Summary:\n"
            "Source code -> Lexer tokens -> Parser AST -> Interpreter runtime -> Output/Input events\n\n"
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


def main() -> None:
    root = tk.Tk()
    TongaLangGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
