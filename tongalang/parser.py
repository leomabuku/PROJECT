from __future__ import annotations

from contextvars import ContextVar
from difflib import get_close_matches
import ply.yacc as yacc

from .lexer import tokens, build_lexer, find_column, reserved
from .ast_nodes import (
    Program,
    SourceLocation,
    VarDecl,
    Assign,
    OutputStmt,
    Block,
    IfStmt,
    WhileStmt,
    ForRangeStmt,
    DoUntilStmt,
    BreakStmt,
    FunctionDecl,
    ReturnStmt,
    ExpressionStmt,
    Literal,
    Variable,
    Unary,
    Binary,
    Call,
)
from .errors import TongaSyntaxError


_CURRENT_SOURCE: ContextVar[str] = ContextVar("tongalang_parser_source", default="")


# ============================================================
# Parser Helpers
# ============================================================

def _location(p, index: int = 1) -> SourceLocation:
    """
    Build a SourceLocation from a PLY production.

    This gives us:
    - line number
    - column number

    Later, the GUI and AST visualizer can use this to highlight errors.
    """
    try:
        source = getattr(p.lexer, "lexdata", "")
        lexpos = p.lexpos(index)
        line = p.lineno(index)
        column = find_column(source, lexpos)
        return SourceLocation(line=line, column=column)
    except Exception:
        return SourceLocation()


def _syntax_error_from_token(token):
    """
    Convert a PLY syntax error into our bilingual TongaLang syntax error.
    """
    source = _CURRENT_SOURCE.get()
    if token is None:
        lines = source.splitlines() or [""]
        raise TongaSyntaxError(
            tonga_message="Program yapwa mpolyo. Kuli chintu chibula kumamanino.",
            english_message="Unexpected end of file. Something is missing at the end of the program.",
            hint_tonga="Bona kuti ma braces, ma parentheses, naa ma statements apwidwa kabotu.",
            hint_english="Check that braces, parentheses, and statements are properly closed.",
            line=len(lines),
            column=len(lines[-1]) + 1,
            code="TL-S101",
        )

    source = getattr(token.lexer, "lexdata", source)
    column = find_column(source, token.lexpos)

    hint_tonga = "Bona mubambilo wa statement ili afwafwi awa."
    hint_english = "Check the statement grammar near this location."
    if token.type == "IDENT":
        matches = get_close_matches(str(token.value).lower(), tuple(reserved), n=1, cutoff=0.72)
        if matches:
            suggestion = matches[0]
            hint_tonga = f'Hena wayandanga kulemba "{suggestion}"?'
            hint_english = f'Did you mean "{suggestion}"?'
    elif token.type == "RBRACE":
        hint_tonga = "Bona statement ili kumbele a } naa bikka chibalo cibula."
        hint_english = "Check the statement before } or add the missing expression."

    raise TongaSyntaxError(
        tonga_message=f'Token "{token.value}" teyelene apa.',
        english_message=f'Unexpected token "{token.value}" of type {token.type}.',
        hint_tonga=hint_tonga,
        hint_english=hint_english,
        line=token.lineno,
        column=column,
        code="TL-S102",
    )


# ============================================================
# Operator Precedence
# Lowest to highest
# ============================================================

precedence = (
    ("left", "OR"),
    ("left", "AND"),
    ("left", "EQ", "NEQ"),
    ("left", "GT", "GTE", "LT", "LTE"),
    ("left", "PLUS", "MINUS"),
    ("left", "STAR", "SLASH", "MOD"),
    ("right", "NOT"),
    ("right", "UMINUS"),
)


# ============================================================
# Program
# ============================================================

def p_program(p):
    "program : top_items"
    p[0] = Program(statements=p[1], location=SourceLocation(line=1, column=1))


def p_top_items_many(p):
    "top_items : top_items top_item"
    p[0] = p[1] + [p[2]]


def p_top_items_empty(p):
    "top_items : "
    p[0] = []


def p_top_item_function(p):
    "top_item : function_decl"
    p[0] = p[1]


def p_top_item_statement(p):
    "top_item : statement"
    p[0] = p[1]


# ============================================================
# Function Declarations
# ============================================================

def p_function_decl(p):
    "function_decl : MULIMO function_name LPAREN param_list_opt RPAREN block"
    p[0] = FunctionDecl(
        name=p[2],
        params=p[4],
        body=p[6],
        location=_location(p, 1),
    )


def p_function_name_ident(p):
    "function_name : IDENT"
    p[0] = p[1]


def p_function_name_main(p):
    "function_name : MATALIKILO"
    p[0] = "matalikilo"


def p_param_list_opt_present(p):
    "param_list_opt : param_list"
    p[0] = p[1]


def p_param_list_opt_empty(p):
    "param_list_opt : "
    p[0] = []


def p_param_list_many(p):
    "param_list : param_list COMMA IDENT"
    p[0] = p[1] + [p[3]]


def p_param_list_single(p):
    "param_list : IDENT"
    p[0] = [p[1]]


# ============================================================
# Statements
# ============================================================

def p_statement_var_decl(p):
    "statement : ZINA IDENT ASSIGN expr"
    p[0] = VarDecl(name=p[2], initializer=p[4], location=_location(p, 1))


def p_statement_assign(p):
    "statement : IDENT ASSIGN expr"
    p[0] = Assign(name=p[1], value=p[3], location=_location(p, 1))


def p_statement_output_expr(p):
    "statement : AMBA LPAREN expr RPAREN"
    p[0] = OutputStmt(expression=p[3], location=_location(p, 1))


def p_statement_output_blank(p):
    "statement : AMBA LPAREN RPAREN"
    p[0] = OutputStmt(expression=None, location=_location(p, 1))


def p_statement_if(p):
    "statement : KUTI LPAREN expr RPAREN block elseif_list else_opt"
    branches = [(p[3], p[5])] + p[6]

    p[0] = IfStmt(
        branches=branches,
        else_branch=p[7],
        location=_location(p, 1),
    )


def p_elseif_list_many(p):
    "elseif_list : elseif_list NAABA LPAREN expr RPAREN block"
    p[0] = p[1] + [(p[4], p[6])]


def p_elseif_list_empty(p):
    "elseif_list : "
    p[0] = []


def p_else_opt_present(p):
    "else_opt : NAKUNYINA block"
    p[0] = p[2]


def p_else_opt_empty(p):
    "else_opt : "
    p[0] = None


def p_statement_while(p):
    "statement : KUFUMBWA LPAREN expr RPAREN block"
    p[0] = WhileStmt(
        condition=p[3],
        body=p[5],
        location=_location(p, 1),
    )


def p_statement_for_range(p):
    "statement : INDULUKA IDENT KUZWA expr KUSIKA expr block"
    p[0] = ForRangeStmt(
        iterator=p[2],
        start=p[4],
        end=p[6],
        body=p[7],
        location=_location(p, 1),
    )


def p_statement_do_until(p):
    "statement : CITA block KUSIKILA LPAREN expr RPAREN"
    p[0] = DoUntilStmt(
        body=p[2],
        condition=p[5],
        location=_location(p, 1),
    )


def p_statement_break(p):
    "statement : LEKA"
    p[0] = BreakStmt(location=_location(p, 1))


def p_statement_return_expr(p):
    "statement : PILULA expr"
    p[0] = ReturnStmt(value=p[2], location=_location(p, 1))


def p_statement_return_empty(p):
    "statement : PILULA"
    p[0] = ReturnStmt(value=None, location=_location(p, 1))


def p_statement_expression(p):
    "statement : expr"
    p[0] = ExpressionStmt(expression=p[1], location=_location(p, 1))


# ============================================================
# Blocks
# ============================================================

def p_block(p):
    "block : LBRACE stmt_list RBRACE"
    p[0] = Block(statements=p[2], location=_location(p, 1))


def p_stmt_list_many(p):
    "stmt_list : stmt_list statement"
    p[0] = p[1] + [p[2]]


def p_stmt_list_empty(p):
    "stmt_list : "
    p[0] = []


# ============================================================
# Expressions
# ============================================================

def p_expr_binary(p):
    """expr : expr PLUS expr
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
            | expr OR expr
    """
    p[0] = Binary(left=p[1], op=p[2], right=p[3], location=_location(p, 2))


def p_expr_unary_not(p):
    "expr : NOT expr"
    p[0] = Unary(op=p[1], right=p[2], location=_location(p, 1))


def p_expr_unary_minus(p):
    "expr : MINUS expr %prec UMINUS"
    p[0] = Unary(op="-", right=p[2], location=_location(p, 1))


def p_expr_group(p):
    "expr : LPAREN expr RPAREN"
    p[0] = p[2]


def p_expr_call(p):
    "expr : call_name LPAREN arg_list_opt RPAREN"
    p[0] = Call(callee=p[1], arguments=p[3], location=_location(p, 1))


def p_call_name_ident(p):
    "call_name : IDENT"
    p[0] = p[1]


def p_call_name_bala(p):
    "call_name : BALA"
    p[0] = "bala"


def p_arg_list_opt_present(p):
    "arg_list_opt : arg_list"
    p[0] = p[1]


def p_arg_list_opt_empty(p):
    "arg_list_opt : "
    p[0] = []


def p_arg_list_many(p):
    "arg_list : arg_list COMMA expr"
    p[0] = p[1] + [p[3]]


def p_arg_list_single(p):
    "arg_list : expr"
    p[0] = [p[1]]


def p_expr_number(p):
    "expr : NUMBER"
    p[0] = Literal(value=p[1], location=_location(p, 1))


def p_expr_string(p):
    "expr : STRING"
    p[0] = Literal(value=p[1], location=_location(p, 1))


def p_expr_bool(p):
    "expr : BOOL"
    p[0] = Literal(value=p[1], location=_location(p, 1))


def p_expr_variable(p):
    "expr : IDENT"
    p[0] = Variable(name=p[1], location=_location(p, 1))


# ============================================================
# Error Handler
# ============================================================

def p_error(p):
    _syntax_error_from_token(p)


# ============================================================
# Parser Builder
# ============================================================

def build_parser(debug: bool = False):
    """
    Build and return a PLY parser.
    """
    return yacc.yacc(start="program", debug=debug, write_tables=False)


def parse_source(source: str) -> Program:
    """
    Parse TongaLang source code and return a Program AST.
    """
    if not isinstance(source, str):
        raise TypeError("TongaLang source must be text.")
    token = _CURRENT_SOURCE.set(source)
    try:
        lexer = build_lexer()
        parser = build_parser(debug=False)
        return parser.parse(source, lexer=lexer)
    finally:
        _CURRENT_SOURCE.reset(token)
