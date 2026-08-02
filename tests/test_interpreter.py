import pytest

from tongalang.parser import parse_source
from tongalang.interpreter import Interpreter
from tongalang.errors import (
    MainFunctionMissingError,
    BreakOutsideLoopError,
    FunctionNotDefinedError,
    UndefinedVariableError,
    LoopLimitExceededError,
)


def run_source(source):
    program = parse_source(source)
    interpreter = Interpreter()
    interpreter.interpret(program)


def test_main_function_required():
    program = parse_source("""
    amba("Hello")
    """)

    interpreter = Interpreter()

    with pytest.raises(MainFunctionMissingError):
        interpreter.interpret(program)


def test_print_output(capsys):
    run_source("""
    mulimo matalikilo() {
        amba("Hello")
    }
    """)

    captured = capsys.readouterr()
    assert captured.out.strip() == "Hello"


def test_global_variable_visible_in_main(capsys):
    run_source("""
    zina appName = "TongaLang"

    mulimo matalikilo() {
        amba(appName)
    }
    """)

    captured = capsys.readouterr()
    assert captured.out.strip() == "TongaLang"


def test_function_return_expression(capsys):
    run_source("""
    mulimo add(a, b) {
        pilula a + b
    }

    mulimo matalikilo() {
        zina total = add(10, 20)
        amba(total)
    }
    """)

    captured = capsys.readouterr()
    assert captured.out.strip() == "30"


def test_function_can_be_called_before_declaration(capsys):
    run_source("""
    mulimo matalikilo() {
        amba(add(7, 8))
    }

    mulimo add(a, b) {
        pilula a + b
    }
    """)

    captured = capsys.readouterr()
    assert captured.out.strip() == "15"


def test_while_loop(capsys):
    run_source("""
    mulimo matalikilo() {
        zina x = 0

        kufumbwa (x ceya 3) {
            amba(x)
            x = x + 1
        }
    }
    """)

    captured = capsys.readouterr()
    assert captured.out.strip().splitlines() == ["0", "1", "2"]


def test_for_range_ascending(capsys):
    run_source("""
    mulimo matalikilo() {
        induluka i kuzwa 1 kusika 5 {
            amba(i)
        }
    }
    """)

    captured = capsys.readouterr()
    assert captured.out.strip().splitlines() == ["1", "2", "3", "4", "5"]


def test_for_range_descending(capsys):
    run_source("""
    mulimo matalikilo() {
        induluka i kuzwa 3 kusika 1 {
            amba(i)
        }
    }
    """)

    captured = capsys.readouterr()
    assert captured.out.strip().splitlines() == ["3", "2", "1"]


def test_do_until_loop(capsys):
    run_source("""
    mulimo matalikilo() {
        zina x = 0

        cita {
            amba(x)
            x = x + 1
        } kusikila (x eelana 3)
    }
    """)

    captured = capsys.readouterr()
    assert captured.out.strip().splitlines() == ["0", "1", "2"]


def test_break_inside_loop(capsys):
    run_source("""
    mulimo matalikilo() {
        zina x = 0

        kufumbwa (x ceya 10) {
            amba(x)

            kuti (x eelana 2) {
                leka
            }

            x = x + 1
        }
    }
    """)

    captured = capsys.readouterr()
    assert captured.out.strip().splitlines() == ["0", "1", "2"]


def test_loop_declared_variable_is_local_to_loop():
    program = parse_source("""
    mulimo matalikilo() {
        induluka i kuzwa 1 kusika 1 {
            zina hidden = 99
        }

        amba(hidden)
    }
    """)

    interpreter = Interpreter()

    with pytest.raises(UndefinedVariableError):
        interpreter.interpret(program)


def test_break_outside_loop_error():
    program = parse_source("""
    mulimo matalikilo() {
        leka
    }
    """)

    interpreter = Interpreter()

    with pytest.raises(BreakOutsideLoopError):
        interpreter.interpret(program)


def test_native_functions(capsys):
    run_source("""
    mulimo matalikilo() {
        amba(mpati(10, 20))
        amba(inini(10, 20))
        amba(ninamba(20))
        amba(ngamabala("Leo"))
    }
    """)

    captured = capsys.readouterr()
    assert captured.out.strip().splitlines() == ["20", "10", "True", "True"]


def test_conversion_functions(capsys):
    run_source("""
    mulimo matalikilo() {
        zina x = namba("20")
        amba(x + 5)
        amba(mabala(100) + " years")
    }
    """)

    captured = capsys.readouterr()
    assert captured.out.strip().splitlines() == ["25", "100 years"]


def test_bala_reads_input_as_expression(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda: "42")

    run_source("""
    mulimo matalikilo() {
        zina answer = bala("Enter: ")
        amba(answer + 8)
    }
    """)

    captured = capsys.readouterr()
    assert captured.out == "Enter: 50\n"


def test_undefined_function_error():
    program = parse_source("""
    mulimo matalikilo() {
        unknown()
    }
    """)

    interpreter = Interpreter()

    with pytest.raises(FunctionNotDefinedError):
        interpreter.interpret(program)


def test_loop_limit_error():
    program = parse_source("""
    mulimo matalikilo() {
        kufumbwa (iiyi) {
            amba("looping")
        }
    }
    """)

    interpreter = Interpreter(max_loop_iterations=3)

    with pytest.raises(LoopLimitExceededError):
        interpreter.interpret(program)
