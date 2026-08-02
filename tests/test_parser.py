import pytest

from tongalang.parser import parse_source
from tongalang.ast_nodes import (
    Program,
    FunctionDecl,
    VarDecl,
    WhileStmt,
    ForRangeStmt,
    DoUntilStmt,
    ReturnStmt,
    Call,
)
from tongalang.errors import TongaSyntaxError


def test_parse_main_function():
    program = parse_source("""
    mulimo matalikilo() {
        amba("Hello")
    }
    """)

    assert isinstance(program, Program)
    assert len(program.statements) == 1
    assert isinstance(program.statements[0], FunctionDecl)
    assert program.statements[0].name == "matalikilo"


def test_parse_global_variable_and_main():
    program = parse_source("""
    zina appName = "TongaLang"

    mulimo matalikilo() {
        amba(appName)
    }
    """)

    assert isinstance(program.statements[0], VarDecl)
    assert isinstance(program.statements[1], FunctionDecl)


def test_parse_function_with_return_expression():
    program = parse_source("""
    mulimo add(a, b) {
        pilula a + b
    }

    mulimo matalikilo() {
        zina total = add(1, 2)
    }
    """)

    add_func = program.statements[0]

    assert isinstance(add_func, FunctionDecl)
    assert add_func.name == "add"
    assert add_func.params == ["a", "b"]
    assert isinstance(add_func.body.statements[0], ReturnStmt)


def test_parse_while_loop():
    program = parse_source("""
    mulimo matalikilo() {
        zina x = 0
        kufumbwa (x ceya 5) {
            amba(x)
            x = x + 1
        }
    }
    """)

    main_func = program.statements[0]
    while_stmt = main_func.body.statements[1]

    assert isinstance(while_stmt, WhileStmt)


def test_parse_for_range_loop():
    program = parse_source("""
    mulimo matalikilo() {
        induluka i kuzwa 1 kusika 5 {
            amba(i)
        }
    }
    """)

    main_func = program.statements[0]
    loop_stmt = main_func.body.statements[0]

    assert isinstance(loop_stmt, ForRangeStmt)
    assert loop_stmt.iterator == "i"


def test_parse_do_until_loop():
    program = parse_source("""
    mulimo matalikilo() {
        zina x = 0

        cita {
            amba(x)
            x = x + 1
        } kusikila (x eelana 5)
    }
    """)

    main_func = program.statements[0]
    loop_stmt = main_func.body.statements[1]

    assert isinstance(loop_stmt, DoUntilStmt)


def test_parse_native_function_call():
    program = parse_source("""
    mulimo matalikilo() {
        zina biggest = mpati(10, 20)
    }
    """)

    main_func = program.statements[0]
    decl = main_func.body.statements[0]

    assert isinstance(decl.initializer, Call)
    assert decl.initializer.callee == "mpati"


def test_semicolon_syntax_rejected():
    with pytest.raises(Exception):
        parse_source("""
        mulimo matalikilo() {
            zina x = 10;
        }
        """)


def test_invalid_syntax_raises_tonga_syntax_error():
    with pytest.raises(TongaSyntaxError):
        parse_source("""
        mulimo matalikilo() {
            kuti x inda 10 {
                amba(x)
            }
        }
        """)