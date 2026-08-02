import pytest
from tongalang.parser import parse_source
from tongalang.interpreter import Interpreter
from tongalang.errors import (
    UndefinedVariableError,
    FunctionNotDefinedError,
    ReturnOutsideFunctionError,
)


def test_undefined_variable_error():
    interpreter = Interpreter()
    stmts = parse_source("""
    mulimo matalikilo() {
        amba(x)
    }
    """)
    with pytest.raises(UndefinedVariableError):
        interpreter.interpret(stmts)


def test_interpolation_undefined_variable_error():
    interpreter = Interpreter()
    stmts = parse_source("""
    mulimo matalikilo() {
        amba("Hello $name")
    }
    """)
    with pytest.raises(UndefinedVariableError):
        interpreter.interpret(stmts)


def test_old_langa_is_not_available():
    interpreter = Interpreter()
    stmts = parse_source("""
    mulimo matalikilo() {
        langa("Hello")
    }
    """)
    with pytest.raises(FunctionNotDefinedError):
        interpreter.interpret(stmts)


def test_return_outside_function_error():
    interpreter = Interpreter()
    stmts = parse_source("""
    pilula 10

    mulimo matalikilo() {
        amba("start")
    }
    """)
    with pytest.raises(ReturnOutsideFunctionError):
        interpreter.interpret(stmts)


def test_error_format_message_default_remains_bilingual():
    error = UndefinedVariableError("x", line=2, column=5)

    assert str(error) == error.format_message()
    assert "Line 2, Column 5" in error.format_message()
    assert "Mulubizyo:" in error.format_message()
    assert "Error:" in error.format_message()
    assert "Langulukila:" in error.format_message()
    assert "Hint:" in error.format_message()


def test_error_format_message_tonga_only():
    error = UndefinedVariableError("x", line=2, column=5)
    message = error.format_message(mode="tonga")

    assert "2:5" in message
    assert "Mulubizyo:" in message
    assert "Langulukila:" in message
    assert "Error:" not in message
    assert "Hint:" not in message
    assert "There is no variable" not in message
