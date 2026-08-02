import importlib


def test_gui_module_exposes_application_class():
    gui_app = importlib.import_module("gui.app")

    assert hasattr(gui_app, "TongaLangGUI")
    assert hasattr(gui_app, "main")
    assert hasattr(gui_app, "IDEState")
    assert hasattr(gui_app, "ExecutionState")
    assert gui_app.IDEState().error_display_mode == "bilingual"


def test_gui_settings_language_tools_are_defined():
    gui_app = importlib.import_module("gui.app")

    assert hasattr(gui_app.TongaLangGUI, "view_ast_from_settings")
    assert hasattr(gui_app.TongaLangGUI, "view_console_from_settings")
    assert hasattr(gui_app.TongaLangGUI, "view_grammar_from_settings")
    assert hasattr(gui_app.TongaLangGUI, "refresh_grammar_reference")
    assert hasattr(gui_app.TongaLangGUI, "_grammar_content")
    assert hasattr(gui_app.TongaLangGUI, "_format_tongalang_error")
    assert hasattr(gui_app.TongaLangGUI, "_format_internal_error")


def test_gui_support_modules_import_without_display():
    assert importlib.import_module("gui.language_profile")
    assert importlib.import_module("gui.syntax_highlighter")
    assert importlib.import_module("gui.ast_tree")
    assert importlib.import_module("gui.runtime")
