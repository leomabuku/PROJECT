from __future__ import annotations

import tkinter as tk
from types import SimpleNamespace

import pytest

from tongalang import __version__
from tongalang.diagnostics import analyze_source
from gui.app import DockView, ExecutionState, TongaLangGUI
from gui.runtime import BlockingInputQueue
from tongalang.errors import UndefinedVariableError


@pytest.fixture(scope="module")
def ide():
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk display is unavailable: {error}")
    root.withdraw()
    app = TongaLangGUI(root)
    root.update_idletasks()
    yield app
    try:
        root.destroy()
    except tk.TclError:
        pass


def test_real_gui_builds_ast_diagram_outline_and_inspector(ide: TongaLangGUI):
    ide._set_editor_text(
        """
        mulimo matalikilo() {
            zina namba = 2 + 3 * 4
            amba(namba)
        }
        """
    )
    ide.refresh_ast()
    assert ide.active_view == "AST"
    assert len(ide.ast_rows) == len(ide.ast_canvas.layout) > 5
    assert "nodes" in ide.ast_status_var.get()
    assert ide.ast_tree.get_children("")
    assert "Purpose" in ide.ast_detail.get("1.0", "end")


def test_ast_find_and_jump_to_source(ide: TongaLangGUI):
    ide._set_editor_text("mulimo matalikilo() {\n zina cipimo = 7\n amba(cipimo)\n}")
    ide.refresh_ast()
    ide.ast_search_var.set("cipimo")
    ide.find_ast_node()
    selected = ide.ast_rows[ide.selected_ast_node_id]
    assert "cipimo" in selected.label
    ide.go_to_ast_source()
    assert ide.active_view == "Editor"
    assert int(ide.editor.index("insert").split(".")[0]) == selected.line


def test_gui_formats_error_with_editor_source_and_caret(ide: TongaLangGUI):
    ide._set_editor_text("mulimo matalikilo() {\n    amba(bula)\n}")
    message = ide._format_tongalang_error(UndefinedVariableError("bula", 2, 10))
    assert "TL-R101" in message
    assert "amba(bula)" in message
    assert "^" in message


def test_worker_executes_program_and_populates_output_and_ast(ide: TongaLangGUI):
    source = 'mulimo matalikilo() { amba("kabotu") }'
    ide.last_started_at = 0.0
    ide._set_execution_state(ExecutionState.RUNNING)
    ide._run_program_worker(source, BlockingInputQueue())
    assert "kabotu" in ide.output_text.get("1.0", "end")
    assert ide.execution_state == ExecutionState.FINISHED
    assert ide.ast_rows


def test_stop_button_sets_cooperative_cancellation_signal(ide: TongaLangGUI):
    ide.stop_event.clear()
    ide._set_execution_state(ExecutionState.RUNNING)
    ide.stop_program()
    assert ide.stop_event.is_set()
    assert "Stopping safely" in ide.execution_summary_var.get()
    ide.stop_event.clear()
    ide.input_queue = BlockingInputQueue()
    ide._enter_waiting_for_input("Value: ")
    ide.stop_program()
    assert ide.input_queue.wait() == ""
    assert ide.stop_event.is_set()
    assert not ide.pending_input
    assert str(ide.input_entry.cget("state")) == "disabled"
    assert not ide.dock_expanded


def test_input_dock_hands_submitted_value_to_runtime_queue_and_echoes_output(ide: TongaLangGUI):
    ide.switch_view("Editor")
    ide.show_dock(DockView.PROBLEMS, expand=False)
    assert ide.dock_view == DockView.PROBLEMS
    assert "Input / I/O" not in ide.views
    assert not hasattr(ide, "output_input_entry")
    assert not hasattr(ide, "input_history")
    assert ide.views["Output"].master is ide.workspace_main
    ide.clear_output()
    ide.input_queue = BlockingInputQueue()
    ide._enter_waiting_for_input("Amupe namba: ")
    assert ide.active_view == "Output"
    assert ide.dock_view == DockView.INPUT
    assert ide.dock_expanded
    assert ide.pending_input
    ide.input_entry.insert(0, "42")
    ide.submit_input()
    assert ide.input_queue.wait() == "42"
    assert ide.execution_state == ExecutionState.RUNNING
    transcript = ide.output_text.get("1.0", "end")
    assert "[Input requested] Amupe namba:" in transcript
    assert "> 42" in transcript
    assert ide.active_view == "Output"
    assert not ide.dock_expanded

    first_queue = BlockingInputQueue()
    ide.input_queue = first_queue
    ide._enter_waiting_for_input("Optional name: ")
    ide.submit_input()
    assert first_queue.wait() == ""
    assert "> [empty]" in ide.output_text.get("1.0", "end")

    second_queue = BlockingInputQueue()
    ide.input_queue = second_queue
    ide._enter_waiting_for_input("Age: ")
    assert ide.dock_expanded
    ide.input_entry.insert(0, "18")
    ide.submit_input()
    assert second_queue.wait() == "18"
    assert "> 18" in ide.output_text.get("1.0", "end")

    ide.input_queue = BlockingInputQueue()
    ide._enter_waiting_for_input("Choose: ")
    ide.toggle_problems(force=True, user_action=True)
    assert ide.pending_input
    assert ide.dock_view == DockView.PROBLEMS
    assert "needed" in ide.input_toggle_var.get().lower()
    ide.toggle_input_dock(force=True, user_action=True)
    assert ide.dock_view == DockView.INPUT
    assert ide.dock_expanded
    ide.input_entry.insert(0, "1")
    ide.submit_input()
    assert ide.input_queue.wait() == "1"


def test_theme_and_settings_apply_without_rebuilding_widgets(ide: TongaLangGUI):
    editor_id = str(ide.editor)
    ide.theme_var.set("light")
    ide.max_loop_var.set(123)
    ide.max_call_depth_var.set(17)
    ide.apply_editor_settings()
    assert str(ide.editor) == editor_id
    assert ide.state.theme_name == "light"
    assert ide.state.max_loop_iterations == 123
    assert ide.state.max_call_depth == 17


def test_navigation_history_and_sidebar_collapse_are_independent(ide: TongaLangGUI):
    ide.show_dock(DockView.INPUT, expand=True)
    ide.switch_view("Editor")
    ide.switch_view("Output")
    assert ide.dock_view == DockView.INPUT
    assert ide.dock_expanded
    ide.switch_view("Settings")
    ide.switch_view("About")
    ide.go_back()
    assert ide.active_view == "Settings"
    ide.go_forward()
    assert ide.active_view == "About"
    previous_view = ide.active_view
    ide.toggle_sidebar()
    assert ide.active_view == previous_view
    ide.toggle_sidebar()
    assert ide.root.bind("<Control-Shift-P>")
    assert ide.root.bind("<Control-Shift-I>")
    ide.collapse_dock()


def test_settings_scrolls_with_mouse_wheel(ide: TongaLangGUI):
    ide.switch_view("Settings")
    ide.root.geometry("980x620")
    ide.root.update_idletasks()
    ide.settings_scroll.canvas.yview_moveto(0.0)
    before = ide.settings_scroll.canvas.yview()[0]
    event = SimpleNamespace(widget=ide.settings_scroll.body, delta=-120, num=None)
    ide.settings_scroll._on_mousewheel(event)
    ide.root.update_idletasks()
    assert ide.settings_scroll.canvas.yview()[0] > before


def test_invalid_numeric_setting_is_reported_inline(ide: TongaLangGUI):
    ide.max_loop_var.set("not-a-number")
    assert ide.apply_editor_settings() is False
    assert "whole numbers" in ide.settings_error_var.get()
    ide.max_loop_var.set(10000)
    assert ide.apply_editor_settings() is True


def test_about_screen_is_structured_scrollable_and_uses_package_version(ide: TongaLangGUI):
    required = {
        "About TongaLang",
        "Project Author",
        "Academic Project Details",
        "Quick Start",
        "IDE Features",
        "Scope and Safety",
    }
    assert required.issubset(ide.about_section_titles)
    assert f"Version: {__version__}" in ide._about_content()
    assert hasattr(ide.about_scroll, "scrollbar")


def test_problem_fix_updates_editor_and_remains_undoable(ide: TongaLangGUI):
    source = 'mulimo matalikilo() { am ba("x") }'
    ide._set_editor_text(source)
    diagnostics = analyze_source(source)
    ide._set_diagnostics(diagnostics, expand=True)
    fix = next(item for item in diagnostics[0].fixes if item.is_editable)
    ide.apply_problem_fix(fix)
    assert 'amba("x")' in ide._get_source()
    ide.editor.edit_undo()
    assert ide._get_source() == source


def test_run_with_static_error_returns_to_editor_and_opens_problems(ide: TongaLangGUI):
    ide._set_editor_text("mulimo mataliklo() { }")
    ide._set_execution_state(ExecutionState.READY)
    ide.run_program()
    assert ide.execution_state == ExecutionState.ERROR
    assert ide.active_view == "Editor"
    assert ide.problems_expanded
    assert ide.current_diagnostics[0].code == "TL-R110"


def test_semantic_keyword_tags_do_not_leak_into_strings_or_comments(ide: TongaLangGUI):
    ide._set_editor_text('zina x = "kuti mulimo"\n// induluka\nmulimo matalikilo() { amba(x) }')
    ide.highlighter.highlight()

    def tags_for(word: str, start: str = "1.0") -> set[str]:
        index = ide.editor.search(word, start, stopindex="end")
        return set(ide.editor.tag_names(index))

    assert "declaration_keyword" in tags_for("zina")
    assert "function_keyword" in tags_for("mulimo", "3.0")
    assert "entry_point_keyword" in tags_for("matalikilo")
    assert "input_output_keyword" in tags_for("amba")
    assert "conditional_keyword" not in tags_for("kuti")
    assert "loop_keyword" not in tags_for("induluka")
