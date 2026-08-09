from __future__ import annotations

import ply.lex as lex

from .errors import TongaLexicalError


# ============================================================
# Token List
# ============================================================

tokens = (
    # Literals / identifiers
    "IDENT",
    "NUMBER",
    "STRING",

    # Arithmetic operators
    "PLUS",
    "MINUS",
    "STAR",
    "SLASH",
    "MOD",

    # Assignment
    "ASSIGN",

    # Grouping / blocks
    "LPAREN",
    "RPAREN",
    "LBRACE",
    "RBRACE",

    # Separators
    "COMMA",

    # Comparison operators
    "GT",
    "LT",
    "GTE",
    "LTE",
    "EQ",
    "NEQ",

    # Logical operators
    "AND",
    "OR",
    "NOT",

    # Keywords
    "ZINA",
    "AMBA",
    "BALA",

    "KUTI",
    "NAABA",
    "NAKUNYINA",

    "KUFUMBWA",
    "INDULUKA",
    "KUZWA",
    "KUSIKA",
    "CITA",
    "KUSIKILA",
    "LEKA",

    "MULIMO",
    "MATALIKILO",
    "PILULA",

    "BOOL",
)


# ============================================================
# Reserved Keywords
# ============================================================

reserved = {
    # Variables and data
    "zina": "ZINA",
    "iiyi": "BOOL",
    "pepe": "BOOL",

    # Input / output
    "amba": "AMBA",
    "bala": "BALA",

    # Conditionals
    "kuti": "KUTI",
    "naaba": "NAABA",
    "nakunyina": "NAKUNYINA",

    # Logical words
    "aa": "AND",
    "naa": "OR",
    "tee": "NOT",

    # Comparison words
    "inda": "GT",
    "ceya": "LT",
    "eelana": "EQ",

    # Loops
    "kufumbwa": "KUFUMBWA",
    "induluka": "INDULUKA",
    "kuzwa": "KUZWA",
    "kusika": "KUSIKA",
    "cita": "CITA",
    "kusikila": "KUSIKILA",
    "leka": "LEKA",

    # Functions
    "mulimo": "MULIMO",
    "matalikilo": "MATALIKILO",
    "pilula": "PILULA",
}


# ============================================================
# Helper: Column Tracking
# ============================================================

def find_column(source: str, lexpos: int) -> int:
    """
    Find the column number of a token from its lex position.

    PLY gives us:
        - token.lineno
        - token.lexpos

    It does not directly give us column numbers, so we calculate them.
    """
    last_newline = source.rfind("\n", 0, lexpos)

    if last_newline < 0:
        return lexpos + 1

    return lexpos - last_newline


def _error_at_token(
    t,
    tonga_message: str,
    english_message: str,
    hint_tonga: str | None = None,
    hint_english: str | None = None,
    code: str = "TL-L001",
    details: dict | None = None,
):
    source = getattr(t.lexer, "lexdata", "")
    column = find_column(source, t.lexpos)

    raise TongaLexicalError(
        tonga_message=tonga_message,
        english_message=english_message,
        hint_tonga=hint_tonga,
        hint_english=hint_english,
        line=t.lexer.lineno,
        column=column,
        code=code,
        details={"raw_text": str(t.value), **(details or {})},
    )


# ============================================================
# Simple Tokens
# ============================================================

t_PLUS = r"\+"
t_MINUS = r"-"
t_STAR = r"\*"
t_SLASH = r"/"
t_MOD = r"%"

t_ASSIGN = r"="

t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACE = r"\{"
t_RBRACE = r"\}"

t_COMMA = r","


# ============================================================
# Multi-character Operators
# These must be defined before single-character comparisons.
# ============================================================

t_GTE = r">="
t_LTE = r"<="
t_EQ = r"=="
t_NEQ = r"!="


# ============================================================
# Single-character Comparisons
# ============================================================

t_GT = r">"
t_LT = r"<"


# ============================================================
# Symbolic Logic Operators
# ============================================================

t_AND = r"&&"
t_OR = r"\|\|"
t_NOT = r"!"


# ============================================================
# Ignored Characters
# ============================================================

t_ignore = " \t\r"


# ============================================================
# Comments
# ============================================================

def t_line_comment(t):
    r"//[^\n]*"
    # Ignore line comments
    pass


def t_block_comment(t):
    r"/\*[\s\S]*?\*/"
    # Ignore block comments, but keep line numbers correct.
    t.lexer.lineno += t.value.count("\n")
    pass


def t_UNTERMINATED_BLOCK_COMMENT(t):
    r"/\*[\s\S]*$"
    _error_at_token(
        t,
        tonga_message="Kambonyi kamabala takamana. Kwabula */.",
        english_message="Unterminated block comment. Missing */.",
        hint_tonga="Bikka */ aamamanino aakambonyi.",
        hint_english="Add */ at the end of the block comment.",
        code="TL-L105",
        details={"missing": "*/"},
    )


# ============================================================
# Newlines
# ============================================================

def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


# ============================================================
# Numbers
# ============================================================

def t_NUMBER(t):
    r"\d+(\.\d+)?"
    if "." in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)

    return t


# ============================================================
# Strings
# ============================================================

def t_STRING(t):
    r"\"([^\\\n]|(\\.))*?\""
    raw = t.value[1:-1]

    escapes = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"'}
    decoded: list[str] = []
    index = 0
    while index < len(raw):
        character = raw[index]
        if character != "\\":
            decoded.append(character)
            index += 1
            continue
        escaped = raw[index + 1]
        if escaped not in escapes:
            source = getattr(t.lexer, "lexdata", "")
            column = find_column(source, t.lexpos) + index + 1
            raise TongaLexicalError(
                tonga_message=f'Kusandula mabala "\\{escaped}" takuzibidwe.',
                english_message=f'Unknown string escape sequence "\\{escaped}".',
                hint_tonga='Sebenzya buyo \\n, \\t, \\r, \\\\, naa \\".',
                hint_english='Use only \\n, \\t, \\r, \\\\, or \\".',
                line=t.lexer.lineno,
                column=column,
                code="TL-L104",
                details={"escape": f"\\{escaped}", "raw_text": f"\\{escaped}"},
            )
        decoded.append(escapes[escaped])
        index += 2
    t.value = "".join(decoded)

    return t


# ============================================================
# Identifiers and Keywords
# ============================================================

def t_IDENT(t):
    r"[A-Za-z_][A-Za-z0-9_]*"

    text = t.value.lower()

    if text in reserved:
        t.type = reserved[text]

        if t.type == "BOOL":
            t.value = True if text == "iiyi" else False

        elif t.type == "AND":
            t.value = "aa"

        elif t.type == "OR":
            t.value = "naa"

        elif t.type == "NOT":
            t.value = "tee"

        elif t.type == "GT":
            t.value = "inda"

        elif t.type == "LT":
            t.value = "ceya"

        elif t.type == "EQ":
            t.value = "eelana"

        else:
            t.value = text

    else:
        # TongaLang identifiers are case-insensitive.
        # Example: Age, AGE, and age all become "age".
        t.value = text

    return t


# ============================================================
# Special Invalid Characters
# ============================================================

def t_SEMICOLON_ERROR(t):
    r";"
    _error_at_token(
        t,
        tonga_message='TongaLang taisebenzisi semicolon ";".',
        english_message='TongaLang does not use semicolons ";".',
        hint_tonga="Leka kulemba semicolon kumamanino aa statement.",
        hint_english="Remove the semicolon at the end of the statement.",
        code="TL-L102",
        details={"replacement": ""},
    )


def t_UNTERMINATED_STRING(t):
    r"\"([^\\\n]|(\\.))*$"
    _error_at_token(
        t,
        tonga_message="String taitolelwanga. Kwabula quote yakumamanino.",
        english_message="Unterminated string. Missing closing quote.",
        hint_tonga='Bikka quote yakumamanino: ".',
        hint_english='Add a closing quotation mark: ".',
        code="TL-L103",
        details={"missing": '"'},
    )


# ============================================================
# General Error Handler
# ============================================================

def t_error(t):
    bad_char = t.value[0]

    _error_at_token(
        t,
        tonga_message=f'Chilembo "{bad_char}" tachizibidwe mu TongaLang.',
        english_message=f'Illegal character "{bad_char}" in TongaLang source code.',
        hint_tonga="Bona kuti walemba chizindikilo chizumizidwe.",
        hint_english="Check that you used a valid TongaLang symbol or character.",
        details={"bad_character": bad_char},
    )


# ============================================================
# Lexer Builder
# ============================================================

def build_lexer():
    """
    Build and return a new lexer instance.
    """
    lexer = lex.lex()
    lexer.lineno = 1
    return lexer


def tokenize_source(source: str):
    """
    Utility function useful for tests, debugging, and GUI token display.

    Returns a list of tokens from source code.
    """
    lexer = build_lexer()
    lexer.input(source)

    result = []

    while True:
        tok = lexer.token()
        if not tok:
            break
        result.append(tok)

    return result
