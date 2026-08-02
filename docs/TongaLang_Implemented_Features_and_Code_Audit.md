# TongaLang Implemented Features and Code Audit

**Project:** Native Language Programming Environment in Tonga  
**Student:** Leo Mabuku  
**Institution:** The Copperbelt University, Department of Computer Science  
**Date Generated:** May 14, 2026

## 1. Audit Scope

This audit records the implemented features and inactive/partial code found in the current workspace. It is based on direct inspection of the source files, tests, examples, README, and GUI code.

## 2. Fully Implemented Features

| Feature | Description | Code Evidence |
| --- | --- | --- |
| Variable declaration | Yes | `zina x = expr` | parser VarDecl; interpreter _exec; Environment.declare |
| Assignment | Yes | `x = expr` | parser Assign; Environment.assign |
| Output | Yes | `amba(expr), amba()` | OutputStmt; Interpreter._exec |
| Input | Yes as expression | `bala(), bala(prompt)` | Call callee=bala; Interpreter._call_bala; GUI RuntimeInputProvider |
| If/else-if/else | Yes | `kuti (...) {...} naaba (...) {...} nakunyina {...}` | IfStmt; Interpreter._exec_if |
| While | Yes | `kufumbwa (...) {...}` | WhileStmt; Interpreter._exec_while |
| For range | Yes | `induluka i kuzwa a kusika b {...}` | ForRangeStmt; inclusive ascending/descending |
| Do until | Yes | `cita {...} kusikila (...)` | DoUntilStmt; Interpreter._exec_do_until |
| Break | Yes | `leka` | BreakStmt; BreakSignal; loop_depth checks |
| Continue | No | `not implemented` | No token, AST node, or interpreter branch |
| Functions | Yes | `mulimo name(params) {...}` | FunctionDecl; Interpreter._collect_functions |
| Main entry | Yes required | `mulimo matalikilo() {...}` | Interpreter._require_main_function/_run_main |
| Return | Yes | `pilula expr` | ReturnStmt; ReturnSignal |
| Native functions | Yes | `mpati, inini, ngamabala, ninamba, namba, mabala` | NATIVE_FUNCTIONS |
| Arrays/lists | No | `not implemented` | No lexer tokens, parser rules, AST nodes |
| String interpolation | Yes | `$name and ${name}` | Interpreter._interpolate |
| GUI AST | Yes, Settings access | `Settings -> View AST` | gui/app.py refresh_ast; gui/ast_tree.py |
| GUI Console | Yes, Settings access | `Settings -> View Console` | gui/app.py _log/_render_console |
| GUI Grammar | Yes | `Settings -> View Grammar` | gui/app.py _grammar_content |
| Error language mode | Yes in GUI | `bilingual/tonga` | IDEState.error_display_mode; TongaLangError.format_message |

## 3. Partial Features and Unused Code

| Item | Status | Evidence | Recommendation |
| --- | --- | --- | --- |
| `InputStmt` | Unused/inactive | Defined in `tongalang/ast_nodes.py`, but parser creates `Call(callee="bala")` instead. Interpreter has no `InputStmt` branch. | Keep as future design note or remove to avoid confusion. |
| `InvalidInputUsageError` | Unused/inactive | Defined in `tongalang/errors.py`, but current `bala` grammar treats input as a normal expression. | Use only if a future statement-style `bala(x)` is implemented. |
| `IDEState.auto_show_ast` | Inactive after Settings-only AST change | Field remains in `gui/app.py`, but visible checkbox was removed and `switch_view` no longer auto-refreshes AST. | Remove later or repurpose as internal cache behavior. |
| `Environment.snapshot()` | Debug helper, not currently displayed | Defined in `tongalang/environment.py`; no GUI environment inspector currently calls it. | Useful for future debugger/environment panel. |
| GUI About version | Metadata inconsistency | `tongalang/__init__.py` reports `0.2.0`; About text says `0.3.0`. | Align release/version metadata before submission. |

## 4. GUI Features and Handlers

| GUI Feature | User Action | Handler / File | Information Flow |
| --- | --- | --- | --- |
| Run program | Topbar Run or F5 | `TongaLangGUI.run_program`, `_run_program_worker` in `gui/app.py` | Editor text -> parser -> AST -> interpreter -> redirected stdout/output panel |
| Input submit | Submit button or Enter | `submit_input` in `gui/app.py`; `BlockingInputQueue` in `gui/runtime.py` | Entry value -> queue -> `RuntimeInputProvider` -> interpreter `input()` |
| Syntax highlighting | Typing in editor | `TongaSyntaxHighlighter.schedule_highlight/highlight` | Text widget content -> regex tags derived from language profile |
| Theme/color settings | Settings controls | `_update_theme_from_settings`, `choose_syntax_color`, `_apply_theme` | Tk variables -> IDEState/custom colors -> widget tag colors |
| View AST | Settings -> View AST | `view_ast_from_settings`, `refresh_ast`, `_load_ast_tree` | Editor text -> parse_source -> AST rows -> Treeview/detail |
| View Console | Settings -> View Console | `view_console_from_settings`, `_render_console` | `console_events` list -> ScrolledText log view |
| View Grammar | Settings -> View Grammar | `view_grammar_from_settings`, `_grammar_content` | Lexer/profile/native/parser summary -> read-only ScrolledText |
| Error language mode | Settings combobox | `_update_error_mode_from_settings`, `_format_tongalang_error` | `IDEState.error_display_mode` -> `TongaLangError.format_message(mode)` |
| Open/save files | Editor buttons | `open_file`, `save_file`, `save_file_as` | `.tg` path -> editor text or editor text -> file |

## 5. Error Handling Catalog

| Error Type | Base | Trigger / Role |
| --- | --- | --- |
| BreakOutsideLoopError | TongaRuntimeError | Runtime diagnostic emitted by environment, interpreter, or native functions. |
| ConversionError | TongaRuntimeError | Runtime diagnostic emitted by environment, interpreter, or native functions. |
| DivisionByZeroError | TongaRuntimeError | Runtime diagnostic emitted by environment, interpreter, or native functions. |
| FunctionNotDefinedError | TongaRuntimeError | Runtime diagnostic emitted by environment, interpreter, or native functions. |
| InvalidInputUsageError | TongaRuntimeError | Defined but not currently raised; intended for future statement-style bala usage. |
| LoopLimitExceededError | TongaRuntimeError | Runtime diagnostic emitted by environment, interpreter, or native functions. |
| MainFunctionMissingError | TongaRuntimeError | Runtime diagnostic emitted by environment, interpreter, or native functions. |
| ReturnOutsideFunctionError | TongaRuntimeError | Runtime diagnostic emitted by environment, interpreter, or native functions. |
| TongaLangError | Exception | Base class; stores Tonga message, English message, hints, line, column; supports format_message(mode). |
| TongaLexicalError | TongaLangError | Raised by lexer for illegal characters, semicolons, unterminated strings, invalid escapes. |
| TongaRuntimeError | TongaLangError | Base runtime failure used by interpreter/native functions. |
| TongaSyntaxError | TongaLangError | Raised by parser when grammar validation fails or EOF is unexpected. |
| TypeMismatchError | TongaRuntimeError | Runtime diagnostic emitted by environment, interpreter, or native functions. |
| UndefinedVariableError | TongaRuntimeError | Runtime diagnostic emitted by environment, interpreter, or native functions. |
| VariableAlreadyDeclaredError | TongaRuntimeError | Runtime diagnostic emitted by environment, interpreter, or native functions. |
| WrongArgumentCountError | TongaRuntimeError | Runtime diagnostic emitted by environment, interpreter, or native functions. |

Lexical errors are generated in `tongalang/lexer.py` by `t_SEMICOLON_ERROR`, `t_UNTERMINATED_STRING`, invalid escape handling in `t_STRING`, and `t_error`. Syntax errors are generated in `tongalang/parser.py` by `_syntax_error_from_token`. Runtime errors are generated by `Interpreter`, `Environment`, and native functions. CLI safe-run functions print bilingual diagnostics. GUI diagnostic display now supports `bilingual` and `tonga` modes.

## 6. Recommended Future Error Messages

- Duplicate parameter names inside `mulimo name(a, a)`.
- Clear invalid `matalikilo` placement or wrong signature guidance.
- Unsupported top-level statement guidance during parse, before runtime.
- More specific `bala` usage guidance if statement-style input is added.
- Type-specific native function errors for `mpati`/`inini` when arguments cannot be compared.
- Column-level GUI highlight, not only full-line highlight.
- Multiple syntax error recovery in a single parse pass.
- Version mismatch warning if package version and GUI About version diverge.

## 7. Validation Notes

The GUI navigation has been updated so AST, Console, and Grammar are opened from Settings only. The topbar no longer exposes AST, the sidebar no longer exposes Console, and the editor toolbar no longer includes AST refresh. CLI error formatting remains bilingual through `str(error)`; GUI display calls `format_message(mode=...)`.

## 8. Files Inspected

- `.gitignore`
- `examples/01_mazyina.tg`
- `examples/02_makani_aakuti.tg`
- `examples/03_kuinduluka_kufumbwa.tg`
- `examples/04_kuinduluka_kuzwa_kusika.tg`
- `examples/05_cita_kusikila.tg`
- `examples/06_milimo.tg`
- `examples/07_kusala_mulimo.tg`
- `examples/08_mubwezezyo_wanamba.tg`
- `examples/09_bupanduluzi_bwacipimo.tg`
- `examples/10_kubandika_kusikila_kuyomwe.tg`
- `examples/11_cibalo_cakubandika.tg`
- `examples/12_kukamantanya_mabala.tg`
- `examples/13_kusandula_misyobo.tg`
- `examples/14_kujana_namba.tg`
- `examples/15_mbaka_amazyina.tg`
- `examples/16_milimo_yakumbele.tg`
- `examples/17_kweelanya_iiyi_pepe.tg`
- `gui/__init__.py`
- `gui/app.py`
- `gui/ast_tree.py`
- `gui/language_profile.py`
- `gui/runtime.py`
- `gui/syntax_highlighter.py`
- `main.py`
- `README.md`
- `requirements.txt`
- `setup_project.bat`
- `test_lexer_manual.py`
- `tests/test_ast_visualizer.py`
- `tests/test_errors.py`
- `tests/test_gui.py`
- `tests/test_gui_language_profile.py`
- `tests/test_gui_runtime.py`
- `tests/test_interpreter.py`
- `tests/test_lexer.py`
- `tests/test_parser.py`
- `tongalang/__init__.py`
- `tongalang/ast_nodes.py`
- `tongalang/ast_visualizer.py`
- `tongalang/environment.py`
- `tongalang/errors.py`
- `tongalang/interpreter.py`
- `tongalang/lexer.py`
- `tongalang/native_functions.py`
- `tongalang/parser.py`
- `tongalang/runner.py`
- `TONGALANG_LANGUAGE_REFERENCE.md`
