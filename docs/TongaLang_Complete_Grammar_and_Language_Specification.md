# TongaLang Complete Grammar and Language Specification

**The Copperbelt University**  
**School of Information and Communication Technology**  
**Department of Computer Science**  
**CS400 Project**

**Project Title:** Native Language Programming Environment in Tonga  
**Student Name:** Leo Mabuku  
**Supervisor:** Dr. Maybin Lengwe  
**Date Generated:** May 14, 2026

## Table of Contents

This Markdown file uses headings that match the Word document headings. In Microsoft Word, use References -> Update Table to refresh the generated table of contents.

## 1. Introduction

TongaLang is an interpreted educational programming language that uses Tonga-derived keywords for core programming constructs. This document describes the language as implemented in the current source code. The implementation, especially `tongalang/lexer.py`, `tongalang/parser.py`, `tongalang/ast_nodes.py`, `tongalang/interpreter.py`, `tongalang/environment.py`, `tongalang/native_functions.py`, and `tongalang/errors.py`, is treated as the source of truth.

The language is designed for beginner programming education while still demonstrating formal language implementation: lexical analysis, grammar parsing, abstract syntax trees, runtime environments, function calls, scope handling, native functions, GUI integration, and bilingual diagnostics.

## 2. Workspace Analysis Summary

| File Path | Role in the Language System | Key Classes / Functions / Definitions Found | Features Confirmed |
| --- | --- | --- | --- |
| `.gitignore` | Example, test, documentation, or configuration |  | inspected |
| `examples/01_mazyina.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/02_makani_aakuti.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/03_kuinduluka_kufumbwa.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/04_kuinduluka_kuzwa_kusika.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/05_cita_kusikila.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/06_milimo.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/07_kusala_mulimo.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/08_mubwezezyo_wanamba.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/09_bupanduluzi_bwacipimo.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/10_kubandika_kusikila_kuyomwe.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/11_cibalo_cakubandika.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/12_kukamantanya_mabala.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/13_kusandula_misyobo.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/14_kujana_namba.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/15_mbaka_amazyina.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/16_milimo_yakumbele.tg` | Example, test, documentation, or configuration |  | inspected |
| `examples/17_kweelanya_iiyi_pepe.tg` | Example, test, documentation, or configuration |  | inspected |
| `gui/__init__.py` | Example, test, documentation, or configuration |  | inspected |
| `gui/app.py` | Tkinter IDE shell and GUI callbacks | SAMPLE_PROGRAM, ExecutionState, IDEState, THEMES, LOG_LEVELS, AVAILABLE_EDITOR_FONTS, TongaLangGUI, main | inspected |
| `gui/ast_tree.py` | AST Treeview adapter | ASTTreeNode, build_ast_tree_rows, iter_ast_children, describe_ast_node, source_position | inspected |
| `gui/language_profile.py` | GUI language profile from source of truth | LanguageProfile, TOKEN_SYMBOLS, _reserved_words_for, _symbols_for, _merge, build_language_profile | inspected |
| `gui/runtime.py` | GUI stdout/input bridge | RuntimeInputProvider, QueueTextWriter, BlockingInputQueue | inspected |
| `gui/syntax_highlighter.py` | Tkinter Text syntax highlighting | SyntaxTheme, TongaSyntaxHighlighter | inspected |
| `main.py` | CLI entry point | build_arg_parser, main | inspected |
| `README.md` | Setup and user documentation |  | inspected |
| `requirements.txt` | Python dependencies |  | inspected |
| `setup_project.bat` | Example, test, documentation, or configuration |  | inspected |
| `test_lexer_manual.py` | Example, test, documentation, or configuration |  | inspected |
| `tests/test_ast_visualizer.py` | Example, test, documentation, or configuration | test_format_ast_renders_program_tree | inspected |
| `tests/test_errors.py` | Example, test, documentation, or configuration | test_undefined_variable_error, test_interpolation_undefined_variable_error, test_old_langa_is_not_available, test_return_outside_function_error, test_error_format_message_default_remains_bilingual, test_error_format_message_tonga_only | inspected |
| `tests/test_gui.py` | Example, test, documentation, or configuration | test_gui_module_exposes_application_class, test_gui_settings_language_tools_are_defined, test_gui_support_modules_import_without_display | inspected |
| `tests/test_gui_language_profile.py` | Example, test, documentation, or configuration | test_language_profile_is_derived_from_runtime_sources, test_language_profile_excludes_old_langa_keyword | inspected |
| `tests/test_gui_runtime.py` | Example, test, documentation, or configuration | test_runtime_input_provider_records_prompt_and_history | inspected |
| `tests/test_interpreter.py` | Example, test, documentation, or configuration | run_source, test_main_function_required, test_print_output, test_global_variable_visible_in_main, test_function_return_expression, test_function_can_be_called_before_declaration, test_while_loop, test_for_range_ascending, test_for_range_descending, test_do_until_loop, test_break_inside_loop, test_loop_declared_variable_is_local_to_loop, test_break_outside_loop_error, test_native_functions, test_conversion_functions, test_bala_reads_input_as_expression, test_undefined_function_error, test_loop_limit_error | inspected |
| `tests/test_lexer.py` | Example, test, documentation, or configuration | token_types, test_keywords_are_recognized, test_boolean_literals, test_identifiers_are_case_insensitive, test_numbers, test_strings, test_semicolon_is_rejected, test_illegal_character_is_rejected | inspected |
| `tests/test_parser.py` | Example, test, documentation, or configuration | test_parse_main_function, test_parse_global_variable_and_main, test_parse_function_with_return_expression, test_parse_while_loop, test_parse_for_range_loop, test_parse_do_until_loop, test_parse_native_function_call, test_semicolon_syntax_rejected, test_invalid_syntax_raises_tonga_syntax_error | inspected |
| `tongalang/__init__.py` | Example, test, documentation, or configuration |  | inspected |
| `tongalang/ast_nodes.py` | AST model | SourceLocation, ASTNode, Stmt, Expr, Program, VarDecl, Assign, OutputStmt, InputStmt, Block, IfStmt, WhileStmt, ForRangeStmt, DoUntilStmt, BreakStmt, FunctionDecl, ReturnStmt, ExpressionStmt | inspected |
| `tongalang/ast_visualizer.py` | Text AST formatter | ASTVisualizer, format_ast | inspected |
| `tongalang/environment.py` | Environment/symbol table | Environment | inspected |
| `tongalang/errors.py` | Error classes and bilingual formatting | TongaLangError, TongaLexicalError, TongaSyntaxError, TongaRuntimeError, UndefinedVariableError, VariableAlreadyDeclaredError, DivisionByZeroError, TypeMismatchError, InvalidInputUsageError, BreakOutsideLoopError, ReturnOutsideFunctionError, FunctionNotDefinedError, WrongArgumentCountError, MainFunctionMissingError, LoopLimitExceededError, ConversionError | inspected |
| `tongalang/interpreter.py` | Interpreter/runtime | BreakSignal, ReturnSignal, Interpreter | inspected |
| `tongalang/lexer.py` | Lexer/tokenizer | find_column, _error_at_token, t_line_comment, t_block_comment, t_newline, t_NUMBER, t_STRING, t_IDENT, t_SEMICOLON_ERROR, t_UNTERMINATED_STRING, t_error, build_lexer, tokenize_source | inspected |
| `tongalang/native_functions.py` | Native function registry | _check_arg_count, native_mpati, native_inini, native_ngamabala, native_ninamba, native_namba, native_mabala | inspected |
| `tongalang/parser.py` | Parser/grammar | _location, _syntax_error_from_token, p_program, p_top_items_many, p_top_items_empty, p_top_item_function, p_top_item_statement, p_function_decl, p_function_name_ident, p_function_name_main, p_param_list_opt_present, p_param_list_opt_empty, p_param_list_many, p_param_list_single, p_statement_var_decl, p_statement_assign, p_statement_output_expr, p_statement_output_blank | inspected |
| `tongalang/runner.py` | CLI/safe runner | run_source, run_file, safe_run_source, safe_run_file | inspected |
| `TONGALANG_LANGUAGE_REFERENCE.md` | Example, test, documentation, or configuration |  | inspected |

## 3. Language Implementation Overview

```text
Source code (.tg or editor text)
  -> tongalang.lexer.build_lexer / tokenize_source
  -> tokens from reserved words, literals, operators, comments, and identifiers
  -> tongalang.parser.parse_source
  -> AST nodes from tongalang.ast_nodes
  -> tongalang.interpreter.Interpreter.interpret
  -> Environment scopes and native function calls
  -> stdout, CLI safe-run output, or Tkinter GUI output/input/error display
```

The GUI follows the same interpreter pipeline. `gui/app.py` reads editor text, redirects stdout through `QueueTextWriter`, replaces `builtins.input` with `RuntimeInputProvider` during execution, and sends errors through `_handle_tongalang_error()` or `_handle_internal_error()`.

## 4. Complete Keyword Reference

| Keyword | Token / Internal Name | English Meaning | Category | Status | Source File |
| --- | --- | --- | --- | --- | --- |
| `aa` | AND | logical and | Logical operator | implemented | `tongalang/lexer.py` |
| `amba` | AMBA | output | Output | implemented | `tongalang/lexer.py` |
| `bala` | BALA | input | Input | implemented | `tongalang/lexer.py` |
| `ceya` | LT | less than | Comparison operator | implemented | `tongalang/lexer.py` |
| `cita` | CITA | do | Loops | implemented | `tongalang/lexer.py` |
| `eelana` | EQ | equal to | Comparison operator | implemented | `tongalang/lexer.py` |
| `iiyi` | BOOL | true | Booleans | implemented | `tongalang/lexer.py` |
| `inda` | GT | greater than | Comparison operator | implemented | `tongalang/lexer.py` |
| `induluka` | INDULUKA | for-range | Loops | implemented | `tongalang/lexer.py` |
| `kufumbwa` | KUFUMBWA | while | Loops | implemented | `tongalang/lexer.py` |
| `kusika` | KUSIKA | to/end | Loops | implemented | `tongalang/lexer.py` |
| `kusikila` | KUSIKILA | until | Loops | implemented | `tongalang/lexer.py` |
| `kuti` | KUTI | if | Conditionals | implemented | `tongalang/lexer.py` |
| `kuzwa` | KUZWA | from | Loops | implemented | `tongalang/lexer.py` |
| `leka` | LEKA | break | Loops | implemented | `tongalang/lexer.py` |
| `matalikilo` | MATALIKILO | main entry point | Functions | implemented | `tongalang/lexer.py` |
| `mulimo` | MULIMO | function | Functions | implemented | `tongalang/lexer.py` |
| `naa` | OR | logical or | Logical operator | implemented | `tongalang/lexer.py` |
| `naaba` | NAABA | else-if | Conditionals | implemented | `tongalang/lexer.py` |
| `nakunyina` | NAKUNYINA | else | Conditionals | implemented | `tongalang/lexer.py` |
| `pepe` | BOOL | false | Booleans | implemented | `tongalang/lexer.py` |
| `pilula` | PILULA | return | Functions | implemented | `tongalang/lexer.py` |
| `tee` | NOT | logical not | Logical operator | implemented | `tongalang/lexer.py` |
| `zina` | ZINA | declare variable | Variables | implemented | `tongalang/lexer.py` |

Planned or old keyword not implemented: `langa` is not recognized. Output is implemented with `amba(...)`.

## 5. Token Specification

| Token Name | Pattern / Literal Symbol | Meaning | Source File |
| --- | --- | --- | --- |
| IDENT | function rule or regex | ident token | `tongalang/lexer.py` |
| NUMBER | function rule or regex | number token | `tongalang/lexer.py` |
| STRING | function rule or regex | string token | `tongalang/lexer.py` |
| PLUS | + | plus token | `tongalang/lexer.py` |
| MINUS | - | minus token | `tongalang/lexer.py` |
| STAR | * | star token | `tongalang/lexer.py` |
| SLASH | / | slash token | `tongalang/lexer.py` |
| MOD | % | mod token | `tongalang/lexer.py` |
| ASSIGN | = | assign token | `tongalang/lexer.py` |
| LPAREN | ( | lparen token | `tongalang/lexer.py` |
| RPAREN | ) | rparen token | `tongalang/lexer.py` |
| LBRACE | { | lbrace token | `tongalang/lexer.py` |
| RBRACE | } | rbrace token | `tongalang/lexer.py` |
| COMMA | , | comma token | `tongalang/lexer.py` |
| GT | > | gt token | `tongalang/lexer.py` |
| LT | < | lt token | `tongalang/lexer.py` |
| GTE | >= | gte token | `tongalang/lexer.py` |
| LTE | <= | lte token | `tongalang/lexer.py` |
| EQ | == | eq token | `tongalang/lexer.py` |
| NEQ | != | neq token | `tongalang/lexer.py` |
| AND | && | and token | `tongalang/lexer.py` |
| OR | || | or token | `tongalang/lexer.py` |
| NOT | ! | not token | `tongalang/lexer.py` |
| ZINA | function rule or regex | zina token | `tongalang/lexer.py` |
| AMBA | function rule or regex | amba token | `tongalang/lexer.py` |
| BALA | function rule or regex | bala token | `tongalang/lexer.py` |
| KUTI | function rule or regex | kuti token | `tongalang/lexer.py` |
| NAABA | function rule or regex | naaba token | `tongalang/lexer.py` |
| NAKUNYINA | function rule or regex | nakunyina token | `tongalang/lexer.py` |
| KUFUMBWA | function rule or regex | kufumbwa token | `tongalang/lexer.py` |
| INDULUKA | function rule or regex | induluka token | `tongalang/lexer.py` |
| KUZWA | function rule or regex | kuzwa token | `tongalang/lexer.py` |
| KUSIKA | function rule or regex | kusika token | `tongalang/lexer.py` |
| CITA | function rule or regex | cita token | `tongalang/lexer.py` |
| KUSIKILA | function rule or regex | kusikila token | `tongalang/lexer.py` |
| LEKA | function rule or regex | leka token | `tongalang/lexer.py` |
| MULIMO | function rule or regex | mulimo token | `tongalang/lexer.py` |
| MATALIKILO | function rule or regex | matalikilo token | `tongalang/lexer.py` |
| PILULA | function rule or regex | pilula token | `tongalang/lexer.py` |
| BOOL | function rule or regex | bool token | `tongalang/lexer.py` |

Additional lexer behavior: identifiers use `[A-Za-z_][A-Za-z0-9_]*` and are normalized to lowercase. Numbers support integers and decimal floats. Strings use double quotes and common escape sequences. `//` line comments and `/* ... */` block comments are ignored. Semicolons are explicitly rejected.

## 6. Formal Grammar Specification

The grammar is implemented as PLY parser functions in `tongalang/parser.py`.

- `p_arg_list_many`: `arg_list : arg_list COMMA expr`
- `p_arg_list_opt_empty`: `arg_list_opt : `
- `p_arg_list_opt_present`: `arg_list_opt : arg_list`
- `p_arg_list_single`: `arg_list : expr`
- `p_block`: `block : LBRACE stmt_list RBRACE`
- `p_call_name_bala`: `call_name : BALA`
- `p_call_name_ident`: `call_name : IDENT`
- `p_else_opt_empty`: `else_opt : `
- `p_else_opt_present`: `else_opt : NAKUNYINA block`
- `p_elseif_list_empty`: `elseif_list : `
- `p_elseif_list_many`: `elseif_list : elseif_list NAABA LPAREN expr RPAREN block`
- `p_expr_binary`: `expr : expr PLUS expr
| expr MINUS expr
| expr STAR expr
| expr SLASH expr
| expr MOD expr
| expr GT expr
| expr GTE expr
| expr LT expr
| expr LTE expr
| expr EQ expr
| expr NEQ expr
| expr AND expr
| expr OR expr`
- `p_expr_bool`: `expr : BOOL`
- `p_expr_call`: `expr : call_name LPAREN arg_list_opt RPAREN`
- `p_expr_group`: `expr : LPAREN expr RPAREN`
- `p_expr_number`: `expr : NUMBER`
- `p_expr_string`: `expr : STRING`
- `p_expr_unary_minus`: `expr : MINUS expr %prec UMINUS`
- `p_expr_unary_not`: `expr : NOT expr`
- `p_expr_variable`: `expr : IDENT`
- `p_function_decl`: `function_decl : MULIMO function_name LPAREN param_list_opt RPAREN block`
- `p_function_name_ident`: `function_name : IDENT`
- `p_function_name_main`: `function_name : MATALIKILO`
- `p_param_list_many`: `param_list : param_list COMMA IDENT`
- `p_param_list_opt_empty`: `param_list_opt : `
- `p_param_list_opt_present`: `param_list_opt : param_list`
- `p_param_list_single`: `param_list : IDENT`
- `p_program`: `program : top_items`
- `p_statement_assign`: `statement : IDENT ASSIGN expr`
- `p_statement_break`: `statement : LEKA`
- `p_statement_do_until`: `statement : CITA block KUSIKILA LPAREN expr RPAREN`
- `p_statement_expression`: `statement : expr`
- `p_statement_for_range`: `statement : INDULUKA IDENT KUZWA expr KUSIKA expr block`
- `p_statement_if`: `statement : KUTI LPAREN expr RPAREN block elseif_list else_opt`
- `p_statement_output_blank`: `statement : AMBA LPAREN RPAREN`
- `p_statement_output_expr`: `statement : AMBA LPAREN expr RPAREN`
- `p_statement_return_empty`: `statement : PILULA`
- `p_statement_return_expr`: `statement : PILULA expr`
- `p_statement_var_decl`: `statement : ZINA IDENT ASSIGN expr`
- `p_statement_while`: `statement : KUFUMBWA LPAREN expr RPAREN block`
- `p_stmt_list_empty`: `stmt_list : `
- `p_stmt_list_many`: `stmt_list : stmt_list statement`
- `p_top_item_function`: `top_item : function_decl`
- `p_top_item_statement`: `top_item : statement`
- `p_top_items_empty`: `top_items : `
- `p_top_items_many`: `top_items : top_items top_item`

## 7. Statement Grammar

### 7.1 Variable Declaration

Syntax: `zina name = expression`. The parser creates `VarDecl`; the interpreter evaluates the initializer and stores it using `Environment.declare`. Re-declaring the same name in the same scope raises `VariableAlreadyDeclaredError`.

```tg
mulimo matalikilo() {
    zina age = 20
    amba(age)
}
```

### 7.2 Assignment

Syntax: `name = expression`. Assignment searches the current scope then parent scopes through `Environment.assign`. Assigning an undeclared name raises `UndefinedVariableError`.

### 7.3 Output Statement

Syntax: `amba(expression)` or `amba()`. `OutputStmt` prints the evaluated value with Python `print`; blank `amba()` prints a blank line.

### 7.4 Input Expression

Syntax: `bala()` or `bala("Prompt")`. Input is implemented as a call expression, not as the unused `InputStmt` node. The interpreter prints the prompt without a newline, reads from `input()`, then auto-converts numeric strings to `int` or `float`.

### 7.5 Conditionals

Syntax: `kuti (condition) block`, optional `naaba (condition) block`, optional `nakunyina block`. `IfStmt.branches` stores ordered conditions and blocks.

### 7.6 Loops

`kufumbwa (condition) block` is a while loop. `induluka i kuzwa start kusika end block` is an inclusive range loop with automatic ascending or descending direction. `cita block kusikila (condition)` is a do-until loop that executes once before testing the condition. `leka` exits the nearest loop.

### 7.7 Functions and Return

`mulimo name(params) block` declares a function. `mulimo matalikilo() block` is required as the entry point. `pilula expression` returns a value through `ReturnSignal`; `pilula` without an expression returns `None`. Functions are collected before main runs, so declaration order does not matter.

## 8. Expression Grammar

Supported expressions include number literals, string literals, boolean literals (`iiyi`, `pepe`), variable references, grouped expressions, unary `tee`/`!`, unary minus, binary arithmetic, comparisons, equality, logical operators, function calls, native function calls, and `bala()` input calls. String interpolation is applied to string literal values at runtime by `Interpreter._interpolate`, supporting `$name` and `${name}`.

## 9. Operator Reference and Precedence

| Level | Operators | Associativity | Meaning |
| --- | --- | --- | --- |
| 1 | `naa`, `||` | left | logical OR |
| 2 | `aa`, `&&` | left | logical AND |
| 3 | `eelana`, `==`, `!=` | left | equality / inequality |
| 4 | `inda`, `>`, `>=`, `ceya`, `<`, `<=` | left | numeric comparison |
| 5 | `+`, `-` | left | addition, string concatenation, subtraction |
| 6 | `*`, `/`, `%` | left | multiplication, division, modulo |
| 7 | `tee`, `!` | right | logical NOT |
| 8 | unary `-` | right | numeric negation |

## 10. Data Types and Runtime Values

Runtime values are Python values: `int`, `float`, `str`, `bool`, and `None` for functions without a return value. There are no arrays/lists, dictionaries, classes, modules, or user-defined types in the implemented grammar.

## 11. Variables, Scope, and Environment

Variables are stored in `Environment.values`, a dictionary keyed by lowercase names, making identifiers case-insensitive. Each environment may have a parent. Global `zina` declarations outside functions are executed before `matalikilo`. Main runs in a child scope named `main`. Blocks create child scopes. Loop bodies use loop-local child scopes per iteration. Function calls run in a child scope of the global environment with parameters declared in that function scope.

## 12. Control Flow

Control flow is implemented with AST nodes and internal Python exceptions. `BreakSignal` exits loops. `ReturnSignal` carries return values from functions. `loop_depth` detects invalid `leka`; `function_depth` detects invalid `pilula`.

## 13. Functions and Built-in Native Functions

| Function Name | Purpose | Source File |
| --- | --- | --- |
| `inini` | inini(a, b) | `tongalang/native_functions.py` |
| `mabala` | mabala(x) | `tongalang/native_functions.py` |
| `mpati` | mpati(a, b) | `tongalang/native_functions.py` |
| `namba` | namba(x) | `tongalang/native_functions.py` |
| `ngamabala` | ngamabala(x) | `tongalang/native_functions.py` |
| `ninamba` | ninamba(x) | `tongalang/native_functions.py` |

`matalikilo` must not have parameters. User functions are stored in `Interpreter.functions` using lowercase names. Wrong argument counts raise `WrongArgumentCountError`.

## 14. Input and Output System

CLI execution uses Python stdout and `input()`. GUI execution redirects stdout with `QueueTextWriter` and replaces `builtins.input` with `RuntimeInputProvider`. When `bala()` is reached in the GUI, execution waits on `BlockingInputQueue` until the user submits input. Program output from `amba(...)` is never translated by GUI error language mode.

## 15. Comments and Whitespace

Whitespace, tabs, carriage returns, line comments, and block comments are ignored by the lexer except for line counting. Statements are separated structurally by the parser; semicolons are invalid.

## 16. Error Handling and Diagnostics

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

`TongaLangError.format_message(mode="bilingual")` preserves existing bilingual behavior. `format_message(mode="tonga")` returns Tonga diagnostic fields only: location, `Mulubizyo`, and `Langulukila` when available. The GUI uses this selected mode; CLI `str(error)` remains bilingual.

Recommended future diagnostics: duplicate parameter names, clearer invalid `matalikilo` placement, parser guidance for unsupported top-level statements, direct guidance for invalid `bala` use, type-specific native function errors for `mpati` and `inini`, column-level GUI highlights, and recovery that reports multiple syntax errors in one parse.

## 17. AST Documentation

| AST Node/Class | Category | Fields |
| --- | --- | --- |
| ASTNode | Support | base class |
| Assign | Statement | name, value, location |
| Binary | Expression | left, op, right, location |
| Block | Statement | statements, location |
| BreakStmt | Statement | location |
| Call | Expression | callee, arguments, location |
| DoUntilStmt | Statement | body, condition, location |
| Expr | Support | base class |
| ExpressionStmt | Statement | expression, location |
| ForRangeStmt | Statement | iterator, start, end, body, location |
| FunctionDecl | Statement | name, params, body, location |
| IfStmt | Statement | branches, else_branch, location |
| InputStmt | Statement | name, prompt, declare, location |
| Literal | Expression | value, location |
| OutputStmt | Statement | expression, location |
| Program | Statement | statements, location |
| ReturnStmt | Statement | value, location |
| SourceLocation | Support | line, column |
| Stmt | Statement | base class |
| Unary | Expression | op, right, location |
| VarDecl | Statement | name, initializer, location |
| Variable | Expression | name, location |
| WhileStmt | Statement | condition, body, location |

AST nodes are produced by parser actions and executed by `Interpreter._exec` or `Interpreter._eval`. `gui/ast_tree.py` adapts AST nodes into `ttk.Treeview` rows. `tongalang/ast_visualizer.py` produces text-form AST output.

## 18. Example Programs

### 01_mazyina.tg

```tg
zina appName = "TongaLang"

mulimo matalikilo() {
    zina name = "Leo"
    zina age = 20
    zina isStudent = iiyi

    amba("App: " + appName)
    amba("Name: " + name)
    amba("Age: " + age)
    amba("Student: " + isStudent)
}
```

### 02_makani_aakuti.tg

```tg
mulimo matalikilo() {
    zina age = 18

    kuti (age inda 18) {
        amba("Adult")
    } naaba (age eelana 18) {
        amba("Just turned adult")
    } nakunyina {
        amba("Child")
    }
}
```

### 03_kuinduluka_kufumbwa.tg

```tg
mulimo matalikilo() {
    zina x = 0

    kufumbwa (x ceya 5) {
        amba(x)
        x = x + 1
    }
}
```

### 04_kuinduluka_kuzwa_kusika.tg

```tg
mulimo matalikilo() {
    amba("Ascending range:")

    induluka i kuzwa 1 kusika 5 {
        amba(i)
    }

    amba("Descending range:")

    induluka j kuzwa 5 kusika 1 {
        amba(j)
    }
}
```

### 05_cita_kusikila.tg

```tg
mulimo matalikilo() {
    zina y = 0

    cita {
        amba(y)
        y = y + 1
    } kusikila (y eelana 5)
}
```

### 06_milimo.tg

```tg
mulimo calculateSum(a, b) {
    pilula a + b
}

mulimo getBiggest(x, y) {
    zina result = mpati(x, y)
    pilula result
}

mulimo matalikilo() {
    zina total = calculateSum(10, 20)
    amba("Total is: " + total)

    zina biggest = getBiggest(45, 99)
    amba("Biggest is: " + biggest)

    zina verify = ninamba(total)

    kuti (verify eelana iiyi) {
        amba("It is a valid number")
    } nakunyina {
        amba("It is not a valid number")
    }
}
```

### 07_kusala_mulimo.tg

```tg
mulimo add(a, b) {
    pilula a + b
}

mulimo subtract(a, b) {
    pilula a - b
}


mulimo matalikilo() {
    amba("=== TongaLang Menu Demo ===")
    amba("1. Add")
    amba("2. Subtract")

    zina choice = bala("Enter your choice: ")
    zina a = 10
    zina b = 5
    kuti (choice eelana 1) {
        zina result = add(a, b)
        amba("Addition result: " + result)
    } naaba (choice eelana 2) {
        zina result = subtract(a, b)
        amba("Subtraction result: " + result)
    } nakunyina {
        amba("Invalid choice")
    }
}
```

### 08_mubwezezyo_wanamba.tg

```tg
// Arithmetic and comparison report

mulimo matalikilo() {
    zina a = 18
    zina b = 5

    amba("=== Arithmetic Report ===")
    amba("a = " + a)
    amba("b = " + b)
    amba("a + b = " + (a + b))
    amba("a - b = " + (a - b))
    amba("a * b = " + (a * b))
    amba("a / b = " + (a / b))
    amba("a % b = " + (a % b))

    kuti (a inda b) {
        amba("a is greater than b")
    } nakunyina {
        amba("a is not greater than b")
    }
}
```

### 09_bupanduluzi_bwacipimo.tg

```tg
// Interactive grade checker using bala(), conditionals, and numeric input conversion

mulimo matalikilo() {
    zina mark = bala("Enter mark from 0 to 100: ")

    kuti (mark >= 70) {
        amba("Grade: Distinction")
    } naaba (mark >= 60) {
        amba("Grade: Merit")
    } naaba (mark >= 50) {
        amba("Grade: Pass")
    } nakunyina {
        amba("Grade: Repeat")
    }
}
```

### 10_kubandika_kusikila_kuyomwe.tg

```tg
// Factorial using a while loop

mulimo matalikilo() {
    zina n = 5
    zina answer = 1

    kufumbwa (n inda 1) {
        answer = answer * n
        n = n - 1
    }

    amba("Factorial is: " + answer)
}
```

### 11_cibalo_cakubandika.tg

```tg
// Nested range loops for a small multiplication table

mulimo matalikilo() {
    amba("=== Multiplication Table ===")

    induluka row kuzwa 1 kusika 3 {
        induluka col kuzwa 1 kusika 4 {
            amba(row + " x " + col + " = " + (row * col))
        }
        amba()
    }
}
```

### 12_kukamantanya_mabala.tg

```tg
// String interpolation supports $name and ${name}
/*
   This program demonstrates comments, interpolation,
   and ordinary string concatenation.
*/

mulimo matalikilo() {
    zina name = "TongaLang"
    zina version = 1

    amba("Welcome to $name")
    amba("Version ${version}")
    amba("Concatenation also works: " + name + " " + version)
}
```

### 13_kusandula_misyobo.tg

```tg
// Native functions for maximum, minimum, type checks, and conversion

mulimo matalikilo() {
    zina textNumber = "42"
    zina converted = namba(textNumber)

    amba("Converted value plus 8: " + (converted + 8))
    amba("Maximum of 12 and 30: " + mpati(12, 30))
    amba("Minimum of 12 and 30: " + inini(12, 30))
    amba("Is converted a number? " + ninamba(converted))
    amba("Is textNumber text? " + ngamabala(textNumber))
    amba("Number converted to text: " + mabala(100))
}
```

### 14_kujana_namba.tg

```tg
// Searching with a loop and leka

mulimo matalikilo() {
    zina target = 4

    induluka number kuzwa 1 kusika 10 {
        amba("Checking " + number)

        kuti (number eelana target) {
            amba("Found target: " + number)
            leka
        }
    }
}
```

### 15_mbaka_amazyina.tg

```tg
// Scope demo: loop-local declarations and assignment to outer variables

mulimo matalikilo() {
    zina total = 0

    induluka i kuzwa 1 kusika 4 {
        zina doubled = i * 2
        total = total + doubled
        amba("Doubled " + i + " is " + doubled)
    }

    amba("Total after loop: " + total)
}
```

### 16_milimo_yakumbele.tg

```tg
// Functions can be called before they appear in the file

mulimo matalikilo() {
    amba("Area: " + rectangleArea(6, 4))
    amba("Perimeter: " + rectanglePerimeter(6, 4))
}

mulimo rectangleArea(width, height) {
    pilula width * height
}

mulimo rectanglePerimeter(width, height) {
    pilula (width + height) * 2
}
```

### 17_kweelanya_iiyi_pepe.tg

```tg
// Boolean logic using iiyi, pepe, aa, naa, and tee

mulimo matalikilo() {
    zina hasPaid = iiyi
    zina hasCard = pepe

    kuti (hasPaid aa tee hasCard) {
        amba("Paid, but card is missing")
    }

    kuti (hasPaid naa hasCard) {
        amba("At least one access condition is true")
    }
}
```


## 19. Complete Feature Matrix

| Feature | Implemented? | Syntax | Source / Runtime Support |
| --- | --- | --- | --- |
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

## 20. Differences Between Original Plan and Current Implementation

Implemented planned core: Tonga keywords, lexer/parser/interpreter, `matalikilo`, variables, output, conditionals, loops, and bilingual errors. Added beyond the early minimal scope: user functions, return values, native functions, string interpolation, automatic numeric input conversion, GUI input pause/resume, syntax color customization, AST tree view, console logs, grammar reference view, and GUI error language mode. Not implemented: arrays/lists, static type checking, modules/imports, continue statement, file I/O inside TongaLang, graphical AST rendering beyond the tree/text view, and installer packaging output checked into the repository.

## 21. Current Limitations

Confirmed limitations from code: no arrays/lists; no `continue`; no module/import system; no static type checking; no formal semantic analyzer separate from runtime checks; no step value for range loops; boolean output displays Python `True`/`False`; parser reports one syntax error at a time; GUI highlights full error lines, not exact columns; `InputStmt` and `InvalidInputUsageError` exist but are not wired into the current grammar/runtime.

## 22. Recommendations for Future Grammar Expansion

Add duplicate parameter validation, a `continue` keyword if needed, optional type declarations, arrays/lists, clearer parser recovery, exact column highlighting in GUI, richer native function errors, published formal EBNF, an environment inspector, and more tests for invalid programs and GUI settings.

## 23. Conclusion

The current TongaLang implementation demonstrates a complete interpreted language pipeline using a Tonga-based surface syntax. It supports lexical analysis, parsing, AST generation, runtime environments, functions, native functions, input/output, GUI integration, and bilingual/Tonga diagnostics. This document can support the CS400 report appendix, final defense, demo preparation, and future maintenance.

## Appendix A: Raw Extracted Grammar

- `p_arg_list_many`: `arg_list : arg_list COMMA expr`
- `p_arg_list_opt_empty`: `arg_list_opt : `
- `p_arg_list_opt_present`: `arg_list_opt : arg_list`
- `p_arg_list_single`: `arg_list : expr`
- `p_block`: `block : LBRACE stmt_list RBRACE`
- `p_call_name_bala`: `call_name : BALA`
- `p_call_name_ident`: `call_name : IDENT`
- `p_else_opt_empty`: `else_opt : `
- `p_else_opt_present`: `else_opt : NAKUNYINA block`
- `p_elseif_list_empty`: `elseif_list : `
- `p_elseif_list_many`: `elseif_list : elseif_list NAABA LPAREN expr RPAREN block`
- `p_expr_binary`: `expr : expr PLUS expr
| expr MINUS expr
| expr STAR expr
| expr SLASH expr
| expr MOD expr
| expr GT expr
| expr GTE expr
| expr LT expr
| expr LTE expr
| expr EQ expr
| expr NEQ expr
| expr AND expr
| expr OR expr`
- `p_expr_bool`: `expr : BOOL`
- `p_expr_call`: `expr : call_name LPAREN arg_list_opt RPAREN`
- `p_expr_group`: `expr : LPAREN expr RPAREN`
- `p_expr_number`: `expr : NUMBER`
- `p_expr_string`: `expr : STRING`
- `p_expr_unary_minus`: `expr : MINUS expr %prec UMINUS`
- `p_expr_unary_not`: `expr : NOT expr`
- `p_expr_variable`: `expr : IDENT`
- `p_function_decl`: `function_decl : MULIMO function_name LPAREN param_list_opt RPAREN block`
- `p_function_name_ident`: `function_name : IDENT`
- `p_function_name_main`: `function_name : MATALIKILO`
- `p_param_list_many`: `param_list : param_list COMMA IDENT`
- `p_param_list_opt_empty`: `param_list_opt : `
- `p_param_list_opt_present`: `param_list_opt : param_list`
- `p_param_list_single`: `param_list : IDENT`
- `p_program`: `program : top_items`
- `p_statement_assign`: `statement : IDENT ASSIGN expr`
- `p_statement_break`: `statement : LEKA`
- `p_statement_do_until`: `statement : CITA block KUSIKILA LPAREN expr RPAREN`
- `p_statement_expression`: `statement : expr`
- `p_statement_for_range`: `statement : INDULUKA IDENT KUZWA expr KUSIKA expr block`
- `p_statement_if`: `statement : KUTI LPAREN expr RPAREN block elseif_list else_opt`
- `p_statement_output_blank`: `statement : AMBA LPAREN RPAREN`
- `p_statement_output_expr`: `statement : AMBA LPAREN expr RPAREN`
- `p_statement_return_empty`: `statement : PILULA`
- `p_statement_return_expr`: `statement : PILULA expr`
- `p_statement_var_decl`: `statement : ZINA IDENT ASSIGN expr`
- `p_statement_while`: `statement : KUFUMBWA LPAREN expr RPAREN block`
- `p_stmt_list_empty`: `stmt_list : `
- `p_stmt_list_many`: `stmt_list : stmt_list statement`
- `p_top_item_function`: `top_item : function_decl`
- `p_top_item_statement`: `top_item : statement`
- `p_top_items_empty`: `top_items : `
- `p_top_items_many`: `top_items : top_items top_item`

## Appendix B: Complete Keyword Mapping

| Keyword | Token | Meaning |
| --- | --- | --- |
| `aa` | AND | logical and |
| `amba` | AMBA | output |
| `bala` | BALA | input |
| `ceya` | LT | less than |
| `cita` | CITA | do |
| `eelana` | EQ | equal to |
| `iiyi` | BOOL | true |
| `inda` | GT | greater than |
| `induluka` | INDULUKA | for-range |
| `kufumbwa` | KUFUMBWA | while |
| `kusika` | KUSIKA | to/end |
| `kusikila` | KUSIKILA | until |
| `kuti` | KUTI | if |
| `kuzwa` | KUZWA | from |
| `leka` | LEKA | break |
| `matalikilo` | MATALIKILO | main entry point |
| `mulimo` | MULIMO | function |
| `naa` | OR | logical or |
| `naaba` | NAABA | else-if |
| `nakunyina` | NAKUNYINA | else |
| `pepe` | BOOL | false |
| `pilula` | PILULA | return |
| `tee` | NOT | logical not |
| `zina` | ZINA | declare variable |

## Appendix C: Complete Example Program Library

### 01_mazyina.tg

```tg
zina appName = "TongaLang"

mulimo matalikilo() {
    zina name = "Leo"
    zina age = 20
    zina isStudent = iiyi

    amba("App: " + appName)
    amba("Name: " + name)
    amba("Age: " + age)
    amba("Student: " + isStudent)
}
```

### 02_makani_aakuti.tg

```tg
mulimo matalikilo() {
    zina age = 18

    kuti (age inda 18) {
        amba("Adult")
    } naaba (age eelana 18) {
        amba("Just turned adult")
    } nakunyina {
        amba("Child")
    }
}
```

### 03_kuinduluka_kufumbwa.tg

```tg
mulimo matalikilo() {
    zina x = 0

    kufumbwa (x ceya 5) {
        amba(x)
        x = x + 1
    }
}
```

### 04_kuinduluka_kuzwa_kusika.tg

```tg
mulimo matalikilo() {
    amba("Ascending range:")

    induluka i kuzwa 1 kusika 5 {
        amba(i)
    }

    amba("Descending range:")

    induluka j kuzwa 5 kusika 1 {
        amba(j)
    }
}
```

### 05_cita_kusikila.tg

```tg
mulimo matalikilo() {
    zina y = 0

    cita {
        amba(y)
        y = y + 1
    } kusikila (y eelana 5)
}
```

### 06_milimo.tg

```tg
mulimo calculateSum(a, b) {
    pilula a + b
}

mulimo getBiggest(x, y) {
    zina result = mpati(x, y)
    pilula result
}

mulimo matalikilo() {
    zina total = calculateSum(10, 20)
    amba("Total is: " + total)

    zina biggest = getBiggest(45, 99)
    amba("Biggest is: " + biggest)

    zina verify = ninamba(total)

    kuti (verify eelana iiyi) {
        amba("It is a valid number")
    } nakunyina {
        amba("It is not a valid number")
    }
}
```

### 07_kusala_mulimo.tg

```tg
mulimo add(a, b) {
    pilula a + b
}

mulimo subtract(a, b) {
    pilula a - b
}


mulimo matalikilo() {
    amba("=== TongaLang Menu Demo ===")
    amba("1. Add")
    amba("2. Subtract")

    zina choice = bala("Enter your choice: ")
    zina a = 10
    zina b = 5
    kuti (choice eelana 1) {
        zina result = add(a, b)
        amba("Addition result: " + result)
    } naaba (choice eelana 2) {
        zina result = subtract(a, b)
        amba("Subtraction result: " + result)
    } nakunyina {
        amba("Invalid choice")
    }
}
```

### 08_mubwezezyo_wanamba.tg

```tg
// Arithmetic and comparison report

mulimo matalikilo() {
    zina a = 18
    zina b = 5

    amba("=== Arithmetic Report ===")
    amba("a = " + a)
    amba("b = " + b)
    amba("a + b = " + (a + b))
    amba("a - b = " + (a - b))
    amba("a * b = " + (a * b))
    amba("a / b = " + (a / b))
    amba("a % b = " + (a % b))

    kuti (a inda b) {
        amba("a is greater than b")
    } nakunyina {
        amba("a is not greater than b")
    }
}
```

### 09_bupanduluzi_bwacipimo.tg

```tg
// Interactive grade checker using bala(), conditionals, and numeric input conversion

mulimo matalikilo() {
    zina mark = bala("Enter mark from 0 to 100: ")

    kuti (mark >= 70) {
        amba("Grade: Distinction")
    } naaba (mark >= 60) {
        amba("Grade: Merit")
    } naaba (mark >= 50) {
        amba("Grade: Pass")
    } nakunyina {
        amba("Grade: Repeat")
    }
}
```

### 10_kubandika_kusikila_kuyomwe.tg

```tg
// Factorial using a while loop

mulimo matalikilo() {
    zina n = 5
    zina answer = 1

    kufumbwa (n inda 1) {
        answer = answer * n
        n = n - 1
    }

    amba("Factorial is: " + answer)
}
```

### 11_cibalo_cakubandika.tg

```tg
// Nested range loops for a small multiplication table

mulimo matalikilo() {
    amba("=== Multiplication Table ===")

    induluka row kuzwa 1 kusika 3 {
        induluka col kuzwa 1 kusika 4 {
            amba(row + " x " + col + " = " + (row * col))
        }
        amba()
    }
}
```

### 12_kukamantanya_mabala.tg

```tg
// String interpolation supports $name and ${name}
/*
   This program demonstrates comments, interpolation,
   and ordinary string concatenation.
*/

mulimo matalikilo() {
    zina name = "TongaLang"
    zina version = 1

    amba("Welcome to $name")
    amba("Version ${version}")
    amba("Concatenation also works: " + name + " " + version)
}
```

### 13_kusandula_misyobo.tg

```tg
// Native functions for maximum, minimum, type checks, and conversion

mulimo matalikilo() {
    zina textNumber = "42"
    zina converted = namba(textNumber)

    amba("Converted value plus 8: " + (converted + 8))
    amba("Maximum of 12 and 30: " + mpati(12, 30))
    amba("Minimum of 12 and 30: " + inini(12, 30))
    amba("Is converted a number? " + ninamba(converted))
    amba("Is textNumber text? " + ngamabala(textNumber))
    amba("Number converted to text: " + mabala(100))
}
```

### 14_kujana_namba.tg

```tg
// Searching with a loop and leka

mulimo matalikilo() {
    zina target = 4

    induluka number kuzwa 1 kusika 10 {
        amba("Checking " + number)

        kuti (number eelana target) {
            amba("Found target: " + number)
            leka
        }
    }
}
```

### 15_mbaka_amazyina.tg

```tg
// Scope demo: loop-local declarations and assignment to outer variables

mulimo matalikilo() {
    zina total = 0

    induluka i kuzwa 1 kusika 4 {
        zina doubled = i * 2
        total = total + doubled
        amba("Doubled " + i + " is " + doubled)
    }

    amba("Total after loop: " + total)
}
```

### 16_milimo_yakumbele.tg

```tg
// Functions can be called before they appear in the file

mulimo matalikilo() {
    amba("Area: " + rectangleArea(6, 4))
    amba("Perimeter: " + rectanglePerimeter(6, 4))
}

mulimo rectangleArea(width, height) {
    pilula width * height
}

mulimo rectanglePerimeter(width, height) {
    pilula (width + height) * 2
}
```

### 17_kweelanya_iiyi_pepe.tg

```tg
// Boolean logic using iiyi, pepe, aa, naa, and tee

mulimo matalikilo() {
    zina hasPaid = iiyi
    zina hasCard = pepe

    kuti (hasPaid aa tee hasCard) {
        amba("Paid, but card is missing")
    }

    kuti (hasPaid naa hasCard) {
        amba("At least one access condition is true")
    }
}
```


## Appendix D: Source Files Inspected

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
