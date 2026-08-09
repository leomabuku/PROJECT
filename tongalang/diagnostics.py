from __future__ import annotations

from dataclasses import dataclass, field
from difflib import get_close_matches
from enum import Enum
import re
import traceback
from typing import Iterable

from .ast_nodes import (
    Assign,
    Binary,
    Block,
    BreakStmt,
    Call,
    DoUntilStmt,
    ExpressionStmt,
    ForRangeStmt,
    FunctionDecl,
    IfStmt,
    Literal,
    OutputStmt,
    Program,
    ReturnStmt,
    Unary,
    VarDecl,
    Variable,
    WhileStmt,
)
from .errors import TongaLangError
from .lexer import reserved
from .native_functions import NATIVE_FUNCTIONS
from .parser import parse_source


class DiagnosticSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class SourceSpan:
    """One-based source range with an end-exclusive boundary."""

    start_line: int
    start_column: int
    end_line: int
    end_column: int


@dataclass(frozen=True)
class TextEdit:
    span: SourceSpan
    expected_text: str
    replacement: str


@dataclass(frozen=True)
class SuggestedFix:
    fix_id: str
    title_tonga: str
    title_english: str
    explanation_tonga: str
    explanation_english: str
    edits: tuple[TextEdit, ...] = ()
    is_preferred: bool = False

    @property
    def is_editable(self) -> bool:
        return bool(self.edits)


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: DiagnosticSeverity
    category_tonga: str
    category_english: str
    summary_tonga: str
    summary_english: str
    detail_tonga: str
    detail_english: str
    span: SourceSpan | None = None
    fixes: tuple[SuggestedFix, ...] = field(default_factory=tuple)
    technical_details: str = ""

    def summary(self, mode: str = "bilingual") -> str:
        if mode == "tonga":
            return self.summary_tonga
        return self.summary_english

    def detail(self, mode: str = "bilingual") -> str:
        if mode == "tonga":
            return self.detail_tonga
        return self.detail_english


def _offset_from_position(source: str, line: int, column: int) -> int:
    if line < 1 or column < 1:
        raise ValueError("Source positions are one-based.")
    lines = source.splitlines(keepends=True)
    has_trailing_line = source.endswith(("\n", "\r"))
    maximum_line = max(1, len(lines) + (1 if has_trailing_line else 0))
    if line > maximum_line:
        raise ValueError("Source position is outside the current text.")
    if line > len(lines):
        return len(source)
    line_text = lines[line - 1]
    content_length = len(line_text.rstrip("\r\n"))
    if column - 1 > content_length:
        raise ValueError("Source column is outside the current line.")
    return sum(len(item) for item in lines[: line - 1]) + column - 1


def _span_from_offsets(source: str, start: int, end: int) -> SourceSpan:
    start = max(0, min(len(source), start))
    end = max(start, min(len(source), end))

    def position(offset: int) -> tuple[int, int]:
        line = source.count("\n", 0, offset) + 1
        last_newline = source.rfind("\n", 0, offset)
        column = offset + 1 if last_newline < 0 else offset - last_newline
        return line, column

    start_line, start_column = position(start)
    end_line, end_column = position(end)
    return SourceSpan(start_line, start_column, end_line, end_column)


def _text_for_span(source: str, span: SourceSpan) -> str:
    start = _offset_from_position(source, span.start_line, span.start_column)
    end = _offset_from_position(source, span.end_line, span.end_column)
    return source[start:end]


def apply_fix(source: str, fix: SuggestedFix) -> str:
    """Apply a guarded source fix and reject stale or overlapping edits."""
    if not fix.edits:
        raise ValueError("This suggestion contains guidance only.")

    resolved: list[tuple[int, int, TextEdit]] = []
    for edit in fix.edits:
        start = _offset_from_position(source, edit.span.start_line, edit.span.start_column)
        end = _offset_from_position(source, edit.span.end_line, edit.span.end_column)
        if source[start:end] != edit.expected_text:
            raise ValueError("The code changed after this fix was calculated. Check the code again.")
        resolved.append((start, end, edit))

    resolved.sort(key=lambda item: item[0])
    for previous, current in zip(resolved, resolved[1:]):
        if previous[1] > current[0]:
            raise ValueError("A suggested fix contains overlapping edits.")

    updated = source
    for start, end, edit in reversed(resolved):
        updated = updated[:start] + edit.replacement + updated[end:]
    return updated


def _guidance_fix(error: TongaLangError) -> SuggestedFix:
    return SuggestedFix(
        fix_id=f"{error.code.lower()}-guidance",
        title_tonga="Nzila yakubambulula",
        title_english="How to fix it",
        explanation_tonga=error.hint_tonga or "Bona code ili afwafwi acilembo casalidwe.",
        explanation_english=error.hint_english or "Review the highlighted code and the Grammar reference.",
    )


def _point_span(source: str, line: int | None, column: int | None, raw_text: str = "") -> SourceSpan | None:
    if line is None:
        return None
    lines = source.splitlines()
    if not 1 <= line <= max(1, len(lines)):
        return None
    column = max(1, column or 1)
    line_text = lines[line - 1] if lines else ""
    column = min(column, len(line_text) + 1)
    if not raw_text and column <= len(line_text):
        word = re.match(r"[A-Za-z_][A-Za-z0-9_]*", line_text[column - 1:])
        if word:
            raw_text = word.group(0)
    length = len(raw_text)
    return SourceSpan(line, column, line, min(len(line_text) + 1, column + length))


def _line_end_span(source: str, line: int) -> SourceSpan:
    lines = source.splitlines()
    text = lines[line - 1] if 1 <= line <= len(lines) else ""
    column = len(text) + 1
    return SourceSpan(line, column, line, column)


def _append_span(source: str) -> SourceSpan:
    return _span_from_offsets(source, len(source), len(source))


def _main_fix(source: str, suggestion: str | None) -> SuggestedFix:
    if suggestion:
        pattern = re.compile(rf"\b{re.escape(suggestion)}\b", re.IGNORECASE)
        match = pattern.search(source)
        if match:
            span = _span_from_offsets(source, match.start(), match.end())
            return SuggestedFix(
                fix_id="rename-main-entry",
                title_tonga='Sandula izina kuba "matalikilo"',
                title_english='Rename it to "matalikilo"',
                explanation_tonga="TongaLang itandika mumulimo uujisi izina lya matalikilo.",
                explanation_english="TongaLang starts in the function named matalikilo.",
                edits=(TextEdit(span, source[match.start():match.end()], "matalikilo"),),
                is_preferred=True,
            )
    separator = "" if not source else ("\n" if source.endswith("\n") else "\n\n")
    skeleton = f'{separator}mulimo matalikilo() {{\n    // Lemba code yako muno.\n}}\n'
    span = _append_span(source)
    return SuggestedFix(
        fix_id="insert-main-entry",
        title_tonga="Bikka mulimo wa matalikilo",
        title_english="Insert a main function",
        explanation_tonga="Bikka nzila yakutandikila program kumamanino aacode.",
        explanation_english="Add the required program entry point at the end of the code.",
        edits=(TextEdit(span, "", skeleton),),
        is_preferred=True,
    )


def diagnostic_from_error(error: TongaLangError, source: str = "") -> Diagnostic:
    details = error.details
    raw_text = str(details.get("raw_text") or details.get("token_value") or "")
    span = _point_span(source, error.line, error.column, raw_text)
    fixes: list[SuggestedFix] = []

    if error.code == "TL-L102" and span is not None:
        expected = _text_for_span(source, span)
        fixes.append(SuggestedFix(
            "remove-semicolon",
            "Kusa semicolon",
            "Remove the semicolon",
            "TongaLang taisebenzisi semicolon kumamanino aa statement.",
            "TongaLang statements do not end with semicolons.",
            (TextEdit(span, expected, ""),),
            True,
        ))
    elif error.code == "TL-L103" and error.line is not None:
        insert_span = _line_end_span(source, error.line)
        fixes.append(SuggestedFix(
            "close-string",
            "Jala string",
            "Close the string",
            'Bikka quote yakumamanino: ".',
            'Add the missing closing quotation mark: ".',
            (TextEdit(insert_span, "", '"'),),
            True,
        ))
    elif error.code == "TL-L105":
        insert_span = _append_span(source)
        fixes.append(SuggestedFix(
            "close-block-comment",
            "Jala kambonyi",
            "Close the block comment",
            "Bikka */ kumamanino aakambonyi.",
            "Add */ at the end of the block comment.",
            (TextEdit(insert_span, "", "*/"),),
            True,
        ))
    elif error.code == "TL-S102" and details.get("suggestion") and span is not None:
        expected = _text_for_span(source, span)
        suggestion = str(details["suggestion"])
        fixes.append(SuggestedFix(
            "replace-keyword-typo",
            f'Lemba "{suggestion}"',
            f'Replace with "{suggestion}"',
            "Ibbala ili lifwambana abbalakani lya TongaLang.",
            "This word closely matches a TongaLang keyword.",
            (TextEdit(span, expected, suggestion),),
            True,
        ))
    elif error.code == "TL-S102" and error.line is not None:
        line_text = source.splitlines()[error.line - 1] if source.splitlines() else ""
        brace_match = re.search(r"\bmulimo\s+[A-Za-z_]\w*\s*(\{)", line_text)
        if brace_match and details.get("token_type") == "LBRACE":
            column = brace_match.start(1) + 1
            insert_span = SourceSpan(error.line, column, error.line, column)
            fixes.append(SuggestedFix(
                "insert-function-parentheses",
                "Bikka () kumulimo",
                "Add function parentheses",
                "Mulimo ulayanda ma parentheses kumbele a brace.",
                "A function declaration needs parentheses before its block.",
                (TextEdit(insert_span, "", "() "),),
                True,
            ))
    elif error.code == "TL-R110":
        fixes.append(_main_fix(source, details.get("suggestion")))

    candidate_values = tuple(str(item) for item in details.get("candidates", ()))
    name = str(details.get("name", ""))
    if error.code in {"TL-R101", "TL-R108"} and name and candidate_values and span is not None:
        matches = get_close_matches(name.lower(), candidate_values, n=1, cutoff=0.75)
        if matches:
            replacement = matches[0]
            expected = _text_for_span(source, span)
            fixes.insert(0, SuggestedFix(
                f"replace-{error.code.lower()}-name",
                f'Lemba "{replacement}"',
                f'Replace with "{replacement}"',
                "Izina ili lili afwafwi aizina lyazibidwe.",
                "This name closely matches one that is already defined.",
                (TextEdit(span, expected, replacement),),
                True,
            ))

    fixes.append(_guidance_fix(error))
    return Diagnostic(
        code=error.code,
        severity=DiagnosticSeverity.ERROR,
        category_tonga=error.category_tonga,
        category_english=error.category_english,
        summary_tonga=error.tonga_message,
        summary_english=error.english_message,
        detail_tonga=error.hint_tonga or "Bona code ili afwafwi acilembo casalidwe.",
        detail_english=error.hint_english or "Review the highlighted code and the Grammar reference.",
        span=span,
        fixes=tuple(fixes),
        technical_details=error.format_message(source=source),
    )


def diagnostic_from_exception(error: Exception) -> Diagnostic:
    return Diagnostic(
        code="TL-I101",
        severity=DiagnosticSeverity.ERROR,
        category_tonga="Mulubizyo uutalangilidwe",
        category_english="Internal IDE error",
        summary_tonga="Kwaba mulubizyo uutazibidwe mu IDE.",
        summary_english="The IDE encountered an unexpected internal problem.",
        detail_tonga="Code yako tiyasandulwa. Kobweza naa kopa technical details kuti ziyanduluzidwe.",
        detail_english="Your code was not changed. Try again or copy the technical details for investigation.",
        fixes=(SuggestedFix(
            "retry-after-internal-error",
            "Kobweza kucita",
            "Try the action again",
            "Sunga code yako akuti kobweza kucita.",
            "Save your code and try the action again.",
        ),),
        technical_details="".join(traceback.format_exception(type(error), error, error.__traceback__)),
    )


def _mask_non_code(source: str) -> str:
    result = list(source)
    index = 0
    state = "code"
    while index < len(source):
        character = source[index]
        next_character = source[index + 1] if index + 1 < len(source) else ""
        if state == "code":
            if character == '"':
                result[index] = " "
                state = "string"
            elif character == "/" and next_character == "/":
                result[index] = result[index + 1] = " "
                index += 1
                state = "line_comment"
            elif character == "/" and next_character == "*":
                result[index] = result[index + 1] = " "
                index += 1
                state = "block_comment"
        elif state == "string":
            if character != "\n":
                result[index] = " "
            if character == "\\" and next_character:
                if next_character != "\n":
                    result[index + 1] = " "
                index += 1
            elif character == '"':
                state = "code"
            elif character == "\n":
                state = "code"
        elif state == "line_comment":
            if character == "\n":
                state = "code"
            else:
                result[index] = " "
        elif state == "block_comment":
            if character != "\n":
                result[index] = " "
            if character == "*" and next_character == "/":
                result[index + 1] = " "
                index += 1
                state = "code"
        index += 1
    return "".join(result)


def _has_unterminated_literal_or_comment(source: str) -> bool:
    index = 0
    state = "code"
    while index < len(source):
        character = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if state == "code":
            if character == '"':
                state = "string"
            elif character == "/" and following == "/":
                state = "line_comment"
                index += 1
            elif character == "/" and following == "*":
                state = "block_comment"
                index += 1
        elif state == "string":
            if character == "\\" and following:
                index += 1
            elif character == '"':
                state = "code"
            elif character == "\n":
                return True
        elif state == "line_comment":
            if character == "\n":
                state = "code"
        elif state == "block_comment" and character == "*" and following == "/":
            state = "code"
            index += 1
        index += 1
    return state in {"string", "block_comment"}


def _preflight_diagnostics(source: str) -> list[Diagnostic]:
    masked = _mask_non_code(source)
    diagnostics: list[Diagnostic] = []

    allowed_symbols = set("+-*/%=><!&|(){},.")
    for index, character in enumerate(masked):
        if character == ";":
            span = _span_from_offsets(source, index, index + 1)
            fix = SuggestedFix(
                "remove-semicolon",
                "Kusa semicolon",
                "Remove the semicolon",
                "TongaLang taisebenzisi semicolon kumamanino aa statement.",
                "TongaLang statements do not end with semicolons.",
                (TextEdit(span, ";", ""),),
                True,
            )
            diagnostics.append(Diagnostic(
                "TL-L102",
                DiagnosticSeverity.ERROR,
                "Mulubizyo wazilembo",
                "Lexical error",
                'TongaLang taisebenzisi semicolon ";".',
                'TongaLang does not use semicolons ";".',
                "Leka kulemba semicolon kumamanino aa statement.",
                "Remove the semicolon at the end of the statement.",
                span,
                (fix,),
            ))
            continue
        if character.isspace() or character.isascii() and (character.isalnum() or character == "_"):
            continue
        if character in {"&", "|"}:
            previous = masked[index - 1] if index else ""
            following = masked[index + 1] if index + 1 < len(masked) else ""
            if previous == character or following == character:
                continue
        elif character in allowed_symbols:
            continue
        span = _span_from_offsets(source, index, index + 1)
        diagnostics.append(Diagnostic(
            "TL-L001",
            DiagnosticSeverity.ERROR,
            "Mulubizyo wazilembo",
            "Lexical error",
            f'Chilembo "{character}" tachizibidwe mu TongaLang.',
            f'Illegal character "{character}" in TongaLang source code.',
            "Bona kuti walemba chizindikilo chizumizidwe.",
            "Check that you used a valid TongaLang symbol or character.",
            span,
            (SuggestedFix(
                "review-illegal-character",
                "Bona cilembo",
                "Review this character",
                "Chilembo cakonzya kuba calembwa akulubizya.",
                "The character may have been typed by mistake; remove or replace it only if that matches your intent.",
            ),),
        ))

    split_pattern = re.compile(r"(?=\b([A-Za-z_][A-Za-z0-9_]*)[ \t]+([A-Za-z_][A-Za-z0-9_]*)\b)")
    seen_spans: set[tuple[int, int]] = set()
    for match in split_pattern.finditer(masked):
        first, second = match.group(1), match.group(2)
        joined = (first + second).lower()
        if joined not in reserved:
            continue
        start = match.start(1)
        end = match.end(2)
        if (start, end) in seen_spans:
            continue
        seen_spans.add((start, end))
        span = _span_from_offsets(source, start, end)
        expected = source[start:end]
        fix = SuggestedFix(
            "join-split-keyword",
            f'Lemba "{joined}"',
            f'Join the word as "{joined}"',
            "Bbalakani lya TongaLang lyabambulwa amwiwiili.",
            "A TongaLang keyword was accidentally split into two words.",
            (TextEdit(span, expected, joined),),
            True,
        )
        diagnostics.append(Diagnostic(
            "TL-L106",
            DiagnosticSeverity.ERROR,
            "Mulubizyo wazilembo",
            "Lexical error",
            f'Bbalakani "{joined}" lyabambulwa amwiwiili.',
            f'The keyword "{joined}" was split into two words.',
            f'Lemba "{joined}" kali bbala limwi.',
            f'Write "{joined}" as one word.',
            span,
            (fix,),
        ))

    if _has_unterminated_literal_or_comment(source):
        return diagnostics

    pairs = {"(": ")", "{": "}"}
    closing = {value: key for key, value in pairs.items()}
    stack: list[tuple[str, int]] = []
    for index, character in enumerate(masked):
        if character in pairs:
            stack.append((character, index))
        elif character in closing:
            if not stack or stack[-1][0] != closing[character]:
                span = _span_from_offsets(source, index, index + 1)
                fix = SuggestedFix(
                    "remove-unmatched-delimiter",
                    f'Kusa "{character}"',
                    f'Remove unmatched "{character}"',
                    "Cilembo ici tacina ncicijalidwe.",
                    "This closing symbol has no matching opening symbol.",
                    (TextEdit(span, character, ""),),
                    True,
                )
                diagnostics.append(Diagnostic(
                    "TL-S103",
                    DiagnosticSeverity.ERROR,
                    "Mulubizyo wamubambilo",
                    "Syntax error",
                    f'Chilembo "{character}" taciyelani aciyandikana.',
                    f'Closing symbol "{character}" has no matching opener.',
                    "Bona ma parentheses ama braces.",
                    "Check the surrounding parentheses and braces.",
                    span,
                    (fix,),
                ))
            else:
                stack.pop()

    if stack:
        missing = "".join(pairs[item[0]] for item in reversed(stack))
        _, start = stack[-1]
        span = _span_from_offsets(source, start, start + 1)
        insertion = _append_span(source)
        fix = SuggestedFix(
            "close-open-delimiters",
            f'Bikka "{missing}"',
            f'Add missing "{missing}"',
            "Jala ma parentheses naa ma braces aatamanina.",
            "Close the unfinished parentheses or braces.",
            (TextEdit(insertion, "", missing),),
            True,
        )
        diagnostics.append(Diagnostic(
            "TL-S104",
            DiagnosticSeverity.ERROR,
            "Mulubizyo wamubambilo",
            "Syntax error",
            "Kuli ma parentheses naa ma braces aatamanina.",
            "One or more parentheses or braces are not closed.",
            f'Bikka "{missing}" kumamanino.',
            f'Add "{missing}" at the end.',
            span,
            (fix,),
        ))

    return diagnostics


def _span_for_name(source: str, line: int, column: int, name: str) -> SourceSpan:
    lines = source.splitlines()
    if not 1 <= line <= len(lines):
        return SourceSpan(max(1, line), max(1, column), max(1, line), max(1, column))
    text = lines[line - 1]
    start = text.lower().find(name.lower(), max(0, column - 1))
    if start < 0:
        start = min(max(0, column - 1), len(text))
        end = start
    else:
        end = start + len(name)
    return SourceSpan(line, start + 1, line, end + 1)


class _SemanticChecker:
    def __init__(self, source: str, program: Program):
        self.source = source
        self.program = program
        self.diagnostics: list[Diagnostic] = []
        self.functions: dict[str, FunctionDecl] = {}
        self.global_names: set[str] = set()

    def run(self) -> tuple[Diagnostic, ...]:
        self._collect_top_level()
        self._check_main()
        seen_globals: set[str] = set()
        for statement in self.program.statements:
            if isinstance(statement, FunctionDecl):
                visible = set(self.global_names)
                parameters: set[str] = set()
                for parameter in statement.params:
                    key = parameter.lower()
                    if key in parameters:
                        self._add(
                            "TL-A108",
                            statement,
                            parameter,
                            f'Parameter "{parameter}" walembwa libili.',
                            f'Parameter "{parameter}" is declared more than once.',
                            "Sebenzya mazina aasiyene kuma parameters.",
                            "Use a unique name for each parameter.",
                        )
                    parameters.add(key)
                visible.update(parameters)
                self._check_block(statement.body, visible, statement.name, 0)
            elif isinstance(statement, VarDecl):
                self._check_expr(statement.initializer, set(seen_globals))
                seen_globals.add(statement.name.lower())
            else:
                self._add(
                    "TL-A106",
                    statement,
                    "",
                    "Statement ili anze amulimo wa matalikilo.",
                    "An executable statement is outside a function.",
                    'Bikka statement mukati ka "mulimo matalikilo() { ... }".',
                    'Move the statement inside "mulimo matalikilo() { ... }".',
                )
        return tuple(self.diagnostics)

    def _collect_top_level(self) -> None:
        for statement in self.program.statements:
            if isinstance(statement, FunctionDecl):
                key = statement.name.lower()
                if key in self.functions:
                    self._add(
                        "TL-A107",
                        statement,
                        statement.name,
                        f'Mulimo "{statement.name}" wazibikidwe kale.',
                        f'Function "{statement.name}" is already declared.',
                        "Sebenzya izina limbi lyamulimo.",
                        "Use a different function name.",
                    )
                else:
                    self.functions[key] = statement
            elif isinstance(statement, VarDecl):
                key = statement.name.lower()
                if key in self.global_names:
                    self._add_duplicate_variable(statement)
                self.global_names.add(key)

    def _check_main(self) -> None:
        main = self.functions.get("matalikilo")
        if main is None:
            matches = get_close_matches("matalikilo", tuple(self.functions), n=1, cutoff=0.72)
            suggestion = matches[0] if matches else None
            fix = _main_fix(self.source, suggestion)
            self.diagnostics.append(Diagnostic(
                "TL-R110",
                DiagnosticSeverity.ERROR,
                "Mulubizyo wakucita",
                "Runtime error",
                'Kunyina mulimo wa matalikilo: "mulimo matalikilo()".',
                'Missing main entry point: "mulimo matalikilo()".',
                'Program ifwila kutandika mu "mulimo matalikilo() { ... }".',
                'Every TongaLang program must start from "mulimo matalikilo() { ... }".',
                None,
                (fix,),
            ))
        elif main.params:
            self._add(
                "TL-A109",
                main,
                "matalikilo",
                '"matalikilo" taifwiri kuba a ma parameters.',
                '"matalikilo" must not have parameters.',
                'Lemba: mulimo matalikilo() { ... }',
                'Write: mulimo matalikilo() { ... }',
            )

    def _check_block(self, block: Block, inherited: set[str], function_name: str | None, loop_depth: int) -> None:
        local: set[str] = set()
        for statement in block.statements:
            visible = inherited | local
            if isinstance(statement, VarDecl):
                self._check_expr(statement.initializer, visible)
                key = statement.name.lower()
                if key in local:
                    self._add_duplicate_variable(statement)
                local.add(key)
            elif isinstance(statement, Assign):
                if statement.name.lower() not in visible:
                    self._add_undefined_variable(statement, statement.name, visible)
                self._check_expr(statement.value, visible)
            elif isinstance(statement, OutputStmt):
                if statement.expression is not None:
                    self._check_expr(statement.expression, visible)
            elif isinstance(statement, ExpressionStmt):
                self._check_expr(statement.expression, visible)
            elif isinstance(statement, ReturnStmt):
                if function_name is None:
                    self._add_context_error(statement, "TL-R107", "pilula", "function")
                if statement.value is not None:
                    self._check_expr(statement.value, visible)
            elif isinstance(statement, BreakStmt):
                if loop_depth <= 0:
                    self._add_context_error(statement, "TL-R106", "leka", "loop")
            elif isinstance(statement, IfStmt):
                for condition, branch in statement.branches:
                    self._check_expr(condition, visible)
                    self._check_block(branch, visible, function_name, loop_depth)
                if statement.else_branch is not None:
                    self._check_block(statement.else_branch, visible, function_name, loop_depth)
            elif isinstance(statement, WhileStmt):
                self._check_expr(statement.condition, visible)
                self._check_block(statement.body, visible, function_name, loop_depth + 1)
            elif isinstance(statement, ForRangeStmt):
                self._check_expr(statement.start, visible)
                self._check_expr(statement.end, visible)
                self._check_block(statement.body, visible | {statement.iterator.lower()}, function_name, loop_depth + 1)
            elif isinstance(statement, DoUntilStmt):
                self._check_block(statement.body, visible, function_name, loop_depth + 1)
                self._check_expr(statement.condition, visible)
            elif isinstance(statement, Block):
                self._check_block(statement, visible, function_name, loop_depth)

    def _check_expr(self, expression, visible: set[str]) -> None:
        if isinstance(expression, Variable):
            if expression.name.lower() not in visible:
                self._add_undefined_variable(expression, expression.name, visible)
            return
        if isinstance(expression, Literal):
            if isinstance(expression.value, str):
                for name in re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", expression.value):
                    if name.lower() not in visible:
                        self._add_undefined_variable(expression, name, visible)
            return
        if isinstance(expression, Unary):
            self._check_expr(expression.right, visible)
            if expression.op == "-" and isinstance(expression.right, Literal) and not self._is_number(expression.right.value):
                self._add_type_guidance(expression, "Unary minus requires a number.")
            return
        if isinstance(expression, Binary):
            self._check_expr(expression.left, visible)
            self._check_expr(expression.right, visible)
            if expression.op in {"/", "%"} and isinstance(expression.right, Literal) and expression.right.value == 0:
                self._add(
                    "TL-R103",
                    expression,
                    expression.op,
                    "Tokonzya kwaabanya nchintu na zilo.",
                    "Cannot divide by zero.",
                    "Chinja divisor naa bikka condition iibona zilo.",
                    "Change the divisor or guard the operation with a zero check.",
                )
            elif expression.op in {"-", "*", "/", "%", ">", "<", ">=", "<=", "inda", "ceya"}:
                if isinstance(expression.left, Literal) and isinstance(expression.right, Literal):
                    if not self._is_number(expression.left.value) or not self._is_number(expression.right.value):
                        self._add_type_guidance(expression, "This operation requires numeric values.")
            return
        if isinstance(expression, Call):
            for argument in expression.arguments:
                self._check_expr(argument, visible)
            name = expression.callee.lower()
            expected: int | None = None
            if name == "bala":
                expected = 1
                valid_counts = {0, 1}
            elif name in NATIVE_FUNCTIONS:
                expected = {"mpati": 2, "inini": 2, "ngamabala": 1, "ninamba": 1, "namba": 1, "mabala": 1}[name]
                valid_counts = {expected}
            elif name in self.functions:
                expected = len(self.functions[name].params)
                valid_counts = {expected}
            else:
                candidates = tuple(self.functions) + tuple(NATIVE_FUNCTIONS) + ("bala",)
                matches = get_close_matches(name, candidates, n=1, cutoff=0.75)
                span = _span_for_name(self.source, expression.location.line, expression.location.column, expression.callee)
                fixes: tuple[SuggestedFix, ...]
                if matches:
                    expected_text = _text_for_span(self.source, span)
                    replacement = matches[0]
                    fixes = (SuggestedFix(
                        "replace-undefined-function",
                        f'Lemba "{replacement}"',
                        f'Replace with "{replacement}"',
                        "Izina lyamulimo lili afwafwi alimwi lizibidwe.",
                        "The function name closely matches a defined function.",
                        (TextEdit(span, expected_text, replacement),),
                        True,
                    ),)
                else:
                    fixes = (SuggestedFix(
                        "define-function",
                        "Zibya mulimo kusanguna",
                        "Define the function first",
                        "Lemba mulimo naa bona izina lyawo.",
                        "Declare the function or check its spelling.",
                    ),)
                self.diagnostics.append(Diagnostic(
                    "TL-R108",
                    DiagnosticSeverity.ERROR,
                    "Mulubizyo wakucita",
                    "Runtime error",
                    f'Mulimo "{expression.callee}" tauzibikidwe.',
                    f'Function "{expression.callee}" is not defined.',
                    "Bona izina naa zibya mulimo kusanguna.",
                    "Check the name or declare the function first.",
                    span,
                    fixes,
                ))
                return
            if len(expression.arguments) not in valid_counts:
                self._add(
                    "TL-R109",
                    expression,
                    expression.callee,
                    f'Mulimo "{expression.callee}" ulayanda ma arguments {expected}, pele wapegwa {len(expression.arguments)}.',
                    f'Function "{expression.callee}" expects {expected} argument(s), but received {len(expression.arguments)}.',
                    "Bona bungi bwama values uutuma kumulimo.",
                    "Check the number of values passed to the function.",
                )

    def _add_undefined_variable(self, node, name: str, visible: Iterable[str]) -> None:
        span = _span_for_name(self.source, node.location.line, node.location.column, name)
        matches = get_close_matches(name.lower(), tuple(visible), n=1, cutoff=0.75)
        fixes: list[SuggestedFix] = []
        if matches:
            replacement = matches[0]
            expected = _text_for_span(self.source, span)
            fixes.append(SuggestedFix(
                "replace-undefined-variable",
                f'Lemba "{replacement}"',
                f'Replace with "{replacement}"',
                "Izina ili lili afwafwi alimwi lyazibidwe.",
                "This name closely matches a variable that is already declared.",
                (TextEdit(span, expected, replacement),),
                True,
            ))
        fixes.append(SuggestedFix(
            "declare-variable",
            "Zibya izina kusanguna",
            "Declare the variable first",
            f'Lemba "zina {name} = ..." kakunyina kusebenzya izina.',
            f'Write "zina {name} = ..." before using this variable.',
        ))
        self.diagnostics.append(Diagnostic(
            "TL-R101",
            DiagnosticSeverity.ERROR,
            "Mulubizyo wakucita",
            "Runtime error",
            f'Kunyina izina lya "{name}".',
            f'There is no variable named "{name}".',
            "Bona izina naa kuti lyazibikidwe kusanguna.",
            "Check the spelling or declare the variable first.",
            span,
            tuple(fixes),
        ))

    def _add_duplicate_variable(self, statement: VarDecl) -> None:
        self._add(
            "TL-R102",
            statement,
            statement.name,
            f'Izina "{statement.name}" lyazibikidwe kale muno.',
            f'Variable "{statement.name}" is already declared in this scope.',
            "Sebenzya assignment kakunyina zina, naa sandula izina.",
            "Use assignment without zina, or choose another variable name.",
        )

    def _add_context_error(self, node, code: str, word: str, context: str) -> None:
        if context == "loop":
            tonga = f'"{word}" ilasebenza buyo mukati kamulungu.'
            english = f'"{word}" can only be used inside a loop.'
        else:
            tonga = f'"{word}" ilasebenza buyo mukati kamulimo.'
            english = f'"{word}" can only be used inside a function.'
        self._add(code, node, word, tonga, english, "Bikka cilembo munzila cilizumizidwe.", f"Move {word} into a {context}.")

    def _add_type_guidance(self, node, english_detail: str) -> None:
        self._add(
            "TL-R104",
            node,
            "",
            "Milimo yamisyobo yabupanduluzi taiyelani.",
            "The value types are not compatible with this operation.",
            "Bona kuti milimo ya namba naa mabala ilikuyelana.",
            english_detail,
        )

    def _add(self, code: str, node, name: str, summary_tonga: str, summary_english: str, detail_tonga: str, detail_english: str) -> None:
        span = _span_for_name(self.source, node.location.line, node.location.column, name) if name else _point_span(
            self.source, node.location.line, node.location.column
        )
        self.diagnostics.append(Diagnostic(
            code,
            DiagnosticSeverity.ERROR,
            "Mulubizyo wa TongaLang",
            "TongaLang error",
            summary_tonga,
            summary_english,
            detail_tonga,
            detail_english,
            span,
            (SuggestedFix(
                f"{code.lower()}-guidance",
                "Nzila yakubambulula",
                "How to fix it",
                detail_tonga,
                detail_english,
            ),),
        ))

    @staticmethod
    def _is_number(value: object) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)


def analyze_source(source: str) -> tuple[Diagnostic, ...]:
    """Analyze source without executing learner code."""
    if not isinstance(source, str):
        raise TypeError("TongaLang source must be text.")

    preflight = _preflight_diagnostics(source)
    if preflight:
        return tuple(preflight)

    try:
        program = parse_source(source)
    except TongaLangError as error:
        return (diagnostic_from_error(error, source),)

    return _SemanticChecker(source, program).run()


__all__ = [
    "Diagnostic",
    "DiagnosticSeverity",
    "SourceSpan",
    "SuggestedFix",
    "TextEdit",
    "analyze_source",
    "apply_fix",
    "diagnostic_from_error",
    "diagnostic_from_exception",
]
