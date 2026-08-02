from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from tongalang import lexer
from tongalang.native_functions import NATIVE_FUNCTIONS


@dataclass(frozen=True)
class LanguageProfile:
    keywords: tuple[str, ...]
    booleans: tuple[str, ...]
    logical_operators: tuple[str, ...]
    comparison_operators: tuple[str, ...]
    arithmetic_operators: tuple[str, ...]
    assignment_operators: tuple[str, ...]
    grouping_symbols: tuple[str, ...]
    native_functions: tuple[str, ...]
    input_output_words: tuple[str, ...]
    function_words: tuple[str, ...]
    loop_words: tuple[str, ...]
    return_words: tuple[str, ...]

    @property
    def word_operators(self) -> tuple[str, ...]:
        words = [
            item
            for item in (*self.logical_operators, *self.comparison_operators)
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", item)
        ]
        return tuple(dict.fromkeys(words))

    @property
    def symbol_operators(self) -> tuple[str, ...]:
        operators = [
            *self.arithmetic_operators,
            *self.assignment_operators,
            *self.comparison_operators,
            *self.logical_operators,
        ]
        symbols = [item for item in operators if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", item)]
        return tuple(dict.fromkeys(sorted(symbols, key=len, reverse=True)))

    @property
    def all_words(self) -> tuple[str, ...]:
        words = [
            *self.keywords,
            *self.booleans,
            *self.word_operators,
            *self.native_functions,
        ]
        return tuple(dict.fromkeys(words))


TOKEN_SYMBOLS = {
    "PLUS": "+",
    "MINUS": "-",
    "STAR": "*",
    "SLASH": "/",
    "MOD": "%",
    "ASSIGN": "=",
    "GT": ">",
    "LT": "<",
    "GTE": ">=",
    "LTE": "<=",
    "EQ": "==",
    "NEQ": "!=",
    "AND": "&&",
    "OR": "||",
    "NOT": "!",
    "LPAREN": "(",
    "RPAREN": ")",
    "LBRACE": "{",
    "RBRACE": "}",
    "COMMA": ",",
}


def _reserved_words_for(*token_types: str) -> tuple[str, ...]:
    wanted = set(token_types)
    words = [word for word, token_type in lexer.reserved.items() if token_type in wanted]
    return tuple(sorted(words))


def _symbols_for(*token_types: str) -> tuple[str, ...]:
    symbols = [TOKEN_SYMBOLS[token_type] for token_type in token_types if token_type in TOKEN_SYMBOLS]
    return tuple(symbols)


def _merge(*groups: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    for group in groups:
        for item in group:
            if item not in result:
                result.append(item)
    return tuple(result)


def build_language_profile() -> LanguageProfile:
    """
    Build the GUI language model from the implementation modules.

    The lexer reserved table is the source of truth for words, and the native
    function registry is the source of truth for built-ins.
    """

    booleans = _reserved_words_for("BOOL")
    logical_words = _reserved_words_for("AND", "OR", "NOT")
    comparison_words = _reserved_words_for("GT", "LT", "EQ")
    logical_symbols = _symbols_for("AND", "OR", "NOT")
    comparison_symbols = _symbols_for("GT", "LT", "GTE", "LTE", "EQ", "NEQ")
    arithmetic = _symbols_for("PLUS", "MINUS", "STAR", "SLASH", "MOD")
    assignment = _symbols_for("ASSIGN",)
    grouping = _symbols_for("LPAREN", "RPAREN", "LBRACE", "RBRACE", "COMMA")

    non_keyword_token_types = {"BOOL", "AND", "OR", "NOT", "GT", "LT", "EQ"}
    keywords = sorted(
        word
        for word, token_type in lexer.reserved.items()
        if token_type not in non_keyword_token_types
    )

    return LanguageProfile(
        keywords=tuple(keywords),
        booleans=booleans,
        logical_operators=_merge(logical_words, logical_symbols),
        comparison_operators=_merge(comparison_words, comparison_symbols),
        arithmetic_operators=arithmetic,
        assignment_operators=assignment,
        grouping_symbols=grouping,
        native_functions=tuple(sorted(NATIVE_FUNCTIONS.keys())),
        input_output_words=_reserved_words_for("AMBA", "BALA"),
        function_words=_reserved_words_for("MULIMO", "MATALIKILO"),
        loop_words=_reserved_words_for("KUFUMBWA", "INDULUKA", "KUZWA", "KUSIKA", "CITA", "KUSIKILA", "LEKA"),
        return_words=_reserved_words_for("PILULA"),
    )
