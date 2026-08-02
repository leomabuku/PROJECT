from __future__ import annotations

import tkinter as tk

import pytest

from gui.app import ExecutionState, TongaLangGUI
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


def test_input_panel_hands_submitted_value_to_runtime_queue(ide: TongaLangGUI):
    ide.input_queue = BlockingInputQueue()
    ide._enter_waiting_for_input("Amupe namba: ")
    ide.output_input_entry.insert(0, "42")
    ide.submit_input()
    assert ide.input_queue.wait() == "42"
    assert ide.execution_state == ExecutionState.RUNNING
    assert "42" in ide.input_history.get("1.0", "end")


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
