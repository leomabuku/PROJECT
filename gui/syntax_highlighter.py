from __future__ import annotations

from dataclasses import dataclass
import re
import tkinter as tk

from .language_profile import LanguageProfile, build_language_profile


@dataclass
class SyntaxTheme:
    editor_bg: str
    editor_fg: str
    selection_bg: str
    keywords: str
    declarations: str
    input_output: str
    conditionals: str
    loops: str
    functions: str
    entry_point: str
    booleans: str
    word_operators: str
    strings: str
    comments: str
    numbers: str
    native_functions: str
    operators: str
    function_names: str
    identifiers: str
    braces: str
    current_line: str
    error_line: str
    ast_highlight: str


DEFAULT_SYNTAX_THEMES: dict[str, SyntaxTheme] = {
    "dark": SyntaxTheme(
        editor_bg="#101722",
        editor_fg="#d6deeb",
        selection_bg="#264f78",
        keywords="#7aa2f7",
        declarations="#7aa2f7",
        input_output="#2ac3de",
        conditionals="#f7768e",
        loops="#ff9e64",
        functions="#bb9af7",
        entry_point="#e0af68",
        booleans="#9ece6a",
        word_operators="#89ddff",
        strings="#9ece6a",
        comments="#6b7280",
        numbers="#bb9af7",
        native_functions="#2ac3de",
        operators="#f7768e",
        function_names="#e0af68",
        identifiers="#d6deeb",
        braces="#89ddff",
        current_line="#182233",
        error_line="#4a1f2a",
        ast_highlight="#243b55",
    ),
    "light": SyntaxTheme(
        editor_bg="#ffffff",
        editor_fg="#1f2937",
        selection_bg="#bfdbfe",
        keywords="#1d4ed8",
        declarations="#1d4ed8",
        input_output="#0e7490",
        conditionals="#be123c",
        loops="#c2410c",
        functions="#7e22ce",
        entry_point="#92400e",
        booleans="#15803d",
        word_operators="#6d28d9",
        strings="#15803d",
        comments="#6b7280",
        numbers="#7e22ce",
        native_functions="#0891b2",
        operators="#be123c",
        function_names="#a16207",
        identifiers="#1f2937",
        braces="#0369a1",
        current_line="#eef2ff",
        error_line="#fee2e2",
        ast_highlight="#dbeafe",
    ),
}


class TongaSyntaxHighlighter:
    """
    Configurable TongaLang highlighter for Tkinter Text widgets.

    Language words come from the lexer/native-function registry through
    LanguageProfile, so highlighting stays aligned with the implementation.
    """

    TOKEN_TAGS = (
        "keyword",
        "declaration_keyword",
        "input_output_keyword",
        "conditional_keyword",
        "loop_keyword",
        "function_keyword",
        "entry_point_keyword",
        "boolean",
        "native_function",
        "word_operator",
        "string",
        "number",
        "comment",
        "symbol_operator",
        "function_name",
        "identifier",
        "brace",
    )

    def __init__(
        self,
        text_widget: tk.Text,
        profile: LanguageProfile | None = None,
        theme_name: str = "dark",
        font_family: str = "Consolas",
        font_size: int = 11,
    ):
        self.text = text_widget
        self.profile = profile or build_language_profile()
        self.theme_name = theme_name
        self.font_family = font_family
        self.font_size = font_size
        self.syntax_theme = DEFAULT_SYNTAX_THEMES[theme_name]
        self.custom_colors: dict[str, str] = {}
        self.current_line_enabled = True
        self._error_line: int | None = None
        self._error_span: tuple[str, str] | None = None
        self._after_id: str | None = None

        self._compile_regexes()
        self.apply_theme(theme_name, font_family=font_family, font_size=font_size)
        self.text.bind("<KeyRelease>", lambda _event: self.schedule_highlight())
        self.text.bind("<ButtonRelease-1>", lambda _event: self.highlight_current_line())
        self.text.bind("<FocusIn>", lambda _event: self.highlight_current_line())

    def _compile_regexes(self) -> None:
        def words_pattern(words: tuple[str, ...]) -> re.Pattern[str] | None:
            if not words:
                return None
            return re.compile(r"\b(?:" + "|".join(map(re.escape, words)) + r")\b")

        categorized = {
            *self.profile.declaration_words,
            *self.profile.input_output_words,
            *self.profile.conditional_words,
            *self.profile.loop_words,
            *self.profile.function_words,
            *self.profile.entry_point_words,
        }
        self.re_keyword = words_pattern(tuple(word for word in self.profile.keywords if word not in categorized))
        self.re_declaration = words_pattern(self.profile.declaration_words)
        self.re_input_output = words_pattern(self.profile.input_output_words)
        self.re_conditional = words_pattern(self.profile.conditional_words)
        self.re_loop = words_pattern(self.profile.loop_words)
        self.re_function_keyword = words_pattern(self.profile.function_words)
        self.re_entry_point = words_pattern(self.profile.entry_point_words)
        self.re_boolean = words_pattern(self.profile.booleans)
        self.re_native = words_pattern(self.profile.native_functions)
        self.re_word_op = words_pattern(self.profile.word_operators)
        self.re_identifier = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
        self.re_function_name = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()")
        self.re_string = re.compile(r'"(?:\\.|[^"\\])*"')
        self.re_block_comment = re.compile(r"/\*.*?\*/", re.DOTALL)
        self.re_line_comment = re.compile(r"//.*?$", re.MULTILINE)
        self.re_number = re.compile(r"\b\d+(?:\.\d+)?\b")
        symbol_operators = "|".join(map(re.escape, self.profile.symbol_operators))
        self.re_symbol = re.compile(symbol_operators) if symbol_operators else None
        braces = "|".join(map(re.escape, self.profile.grouping_symbols))
        self.re_brace = re.compile(braces) if braces else None

    def apply_theme(
        self,
        theme_name: str,
        *,
        font_family: str | None = None,
        font_size: int | None = None,
        custom_colors: dict[str, str] | None = None,
    ) -> None:
        # Reconfiguring fonts and spacing can otherwise move the viewport to
        # the insertion cursor, which is especially disorienting when a
        # learner switches themes while reviewing an error.
        y_position = self.text.yview()[0]
        x_position = self.text.xview()[0]
        self.theme_name = theme_name
        self.syntax_theme = DEFAULT_SYNTAX_THEMES[theme_name]
        if font_family is not None:
            self.font_family = font_family
        if font_size is not None:
            self.font_size = font_size
        if custom_colors is not None:
            self.custom_colors = dict(custom_colors)

        base_font = (self.font_family, self.font_size)
        bold_font = (self.font_family, self.font_size, "bold")
        italic_font = (self.font_family, self.font_size, "italic")

        self.text.configure(
            background=self.syntax_theme.editor_bg,
            foreground=self.syntax_theme.editor_fg,
            insertbackground=self.syntax_theme.editor_fg,
            selectbackground=self.syntax_theme.selection_bg,
            font=base_font,
            relief="flat",
            padx=12,
            pady=10,
            spacing1=2,
            spacing3=2,
        )

        color = self._color
        self.text.tag_configure("keyword", foreground=color("keywords"), font=bold_font)
        self.text.tag_configure("declaration_keyword", foreground=color("declarations"), font=bold_font)
        self.text.tag_configure("input_output_keyword", foreground=color("input_output"), font=bold_font)
        self.text.tag_configure("conditional_keyword", foreground=color("conditionals"), font=bold_font)
        self.text.tag_configure("loop_keyword", foreground=color("loops"), font=bold_font)
        self.text.tag_configure("function_keyword", foreground=color("functions"), font=bold_font)
        self.text.tag_configure("entry_point_keyword", foreground=color("entry_point"), font=bold_font)
        self.text.tag_configure("boolean", foreground=color("booleans"), font=bold_font)
        self.text.tag_configure("native_function", foreground=color("native_functions"), font=bold_font)
        self.text.tag_configure("word_operator", foreground=color("word_operators"), font=bold_font)
        self.text.tag_configure("string", foreground=color("strings"))
        self.text.tag_configure("number", foreground=color("numbers"))
        self.text.tag_configure("comment", foreground=color("comments"), font=italic_font)
        self.text.tag_configure("symbol_operator", foreground=color("operators"))
        self.text.tag_configure("function_name", foreground=color("function_names"), font=bold_font)
        self.text.tag_configure("identifier", foreground=color("identifiers"))
        self.text.tag_configure("brace", foreground=color("braces"), font=bold_font)
        self.text.tag_configure("current_line", background=color("current_line"))
        self.text.tag_configure("error_line", background=color("error_line"))
        self.text.tag_configure("error_range", background=color("error_line"), underline=True)
        for tag in (
            "identifier",
            "function_name",
            "keyword",
            "declaration_keyword",
            "input_output_keyword",
            "conditional_keyword",
            "loop_keyword",
            "function_keyword",
            "boolean",
            "word_operator",
            "native_function",
            "entry_point_keyword",
        ):
            self.text.tag_raise(tag)
        self.highlight()
        self.highlight_current_line()
        self.text.yview_moveto(y_position)
        self.text.xview_moveto(x_position)

    def update_color(self, color_key: str, value: str) -> None:
        self.custom_colors[color_key] = value
        self.apply_theme(self.theme_name, custom_colors=self.custom_colors)

    def reset_custom_colors(self) -> None:
        self.custom_colors.clear()
        self.apply_theme(self.theme_name)

    def schedule_highlight(self) -> None:
        if self._after_id is not None:
            self.text.after_cancel(self._after_id)
        self._after_id = self.text.after(60, self._highlight_from_schedule)

    def _highlight_from_schedule(self) -> None:
        self._after_id = None
        self.highlight()
        self.highlight_current_line()

    def highlight(self) -> None:
        content = self.text.get("1.0", "end-1c")
        protected = [False] * (len(content) + 1)

        for tag in self.TOKEN_TAGS:
            self.text.tag_remove(tag, "1.0", "end")

        protected_spans: list[tuple[int, int, str]] = []
        for regex, tag in (
            (self.re_block_comment, "comment"),
            (self.re_line_comment, "comment"),
            (self.re_string, "string"),
        ):
            for match in regex.finditer(content):
                protected_spans.append((match.start(), match.end(), tag))

        protected_spans.sort(key=lambda item: item[0])
        for start, end, tag in protected_spans:
            for index in range(start, min(end, len(content))):
                protected[index] = True
            self._tag_range(tag, start, end)

        def is_open(start: int, end: int) -> bool:
            return not any(protected[start:min(end, len(content))])

        for regex, tag in (
            (self.re_identifier, "identifier"),
            (self.re_number, "number"),
            (self.re_function_name, "function_name"),
            (self.re_keyword, "keyword"),
            (self.re_declaration, "declaration_keyword"),
            (self.re_input_output, "input_output_keyword"),
            (self.re_conditional, "conditional_keyword"),
            (self.re_loop, "loop_keyword"),
            (self.re_function_keyword, "function_keyword"),
            (self.re_entry_point, "entry_point_keyword"),
            (self.re_boolean, "boolean"),
            (self.re_native, "native_function"),
            (self.re_word_op, "word_operator"),
            (self.re_symbol, "symbol_operator"),
            (self.re_brace, "brace"),
        ):
            if regex is None:
                continue
            for match in regex.finditer(content):
                start, end = match.span(1) if regex is self.re_function_name else match.span()
                if is_open(start, end):
                    self._tag_range(tag, start, end)

    def highlight_current_line(self) -> None:
        self.text.tag_remove("current_line", "1.0", "end")
        if not self.current_line_enabled:
            return
        try:
            insert_index = self.text.index("insert")
            self.text.tag_add("current_line", f"{insert_index} linestart", f"{insert_index} lineend +1c")
            self.text.tag_lower("current_line")
        except tk.TclError:
            return

    def set_current_line_enabled(self, enabled: bool) -> None:
        self.current_line_enabled = bool(enabled)
        self.highlight_current_line()

    def highlight_error_line(self, line_number: int) -> None:
        self.clear_error_highlight()
        try:
            self.text.tag_add("error_line", f"{line_number}.0", f"{line_number}.end +1c")
            self.text.see(f"{line_number}.0")
            self._error_line = line_number
        except tk.TclError:
            return

    def highlight_error_span(self, start: str, end: str) -> None:
        self.clear_error_highlight()
        try:
            if self.text.compare(start, "==", end):
                end = f"{start} +1c"
            self.text.tag_add("error_range", start, end)
            self.text.see(start)
            self._error_span = (start, end)
        except tk.TclError:
            return

    def clear_error_highlight(self) -> None:
        self.text.tag_remove("error_line", "1.0", "end")
        self.text.tag_remove("error_range", "1.0", "end")
        self._error_line = None
        self._error_span = None

    def _tag_range(self, tag: str, start: int, end: int) -> None:
        self.text.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")

    def _color(self, key: str) -> str:
        return self.custom_colors.get(key, getattr(self.syntax_theme, key))
