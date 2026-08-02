from __future__ import annotations

import pytest

from tongalang.errors import (
    CallDepthExceededError,
    DivisionByZeroError,
    ExecutionCancelledError,
    InvalidConfigurationError,
    LoopLimitExceededError,
    TongaRuntimeError,
    TypeMismatchError,
)
from tongalang.interpreter import Interpreter
from tongalang.parser import parse_source


@pytest.mark.parametrize(
    ("setting", "kwargs"),
    [
        ("max_loop_iterations", {"max_loop_iterations": 0}),
        ("max_loop_iterations", {"max_loop_iterations": -1}),
        ("max_loop_iterations", {"max_loop_iterations": True}),
        ("max_call_depth", {"max_call_depth": 0}),
        ("max_call_depth", {"max_call_depth": 1.5}),
    ],
)
def test_invalid_safety_configuration_fails_before_execution(setting, kwargs):
    with pytest.raises(InvalidConfigurationError) as captured:
        Interpreter(**kwargs)
    assert setting in captured.value.english_message


def test_infinite_loop_hits_configured_iteration_limit():
    program = parse_source("mulimo matalikilo() { kufumbwa (iiyi) { zina x = 1 } }")
    with pytest.raises(LoopLimitExceededError) as captured:
        Interpreter(max_loop_iterations=3).interpret(program)
    assert "3" in captured.value.english_message


def test_recursive_function_hits_call_depth_before_python_recursion_error():
    program = parse_source(
        """
        mulimo bwela() { pilula bwela() }
        mulimo matalikilo() { amba(bwela()) }
        """
    )
    with pytest.raises(CallDepthExceededError) as captured:
        Interpreter(max_call_depth=8).interpret(program)
    assert captured.value.code == "TL-R114"


def test_external_stop_signal_cancels_busy_program():
    checks = 0

    def should_stop():
        nonlocal checks
        checks += 1
        return checks > 40

    program = parse_source("mulimo matalikilo() { kufumbwa (iiyi) { amba() } }")
    with pytest.raises(ExecutionCancelledError):
        Interpreter(max_loop_iterations=100000, should_stop=should_stop).interpret(program)


@pytest.mark.parametrize("operator", ["/", "%"])
def test_zero_divisor_is_never_exposed_as_python_zero_division(operator):
    program = parse_source(f"mulimo matalikilo() {{ amba(5 {operator} 0) }}")
    with pytest.raises(DivisionByZeroError):
        Interpreter().interpret(program)


def test_boolean_is_not_silently_accepted_as_number():
    program = parse_source("mulimo matalikilo() { amba(iiyi - 1) }")
    with pytest.raises(TypeMismatchError):
        Interpreter().interpret(program)


def test_incompatible_native_maximum_becomes_domain_error():
    program = parse_source('mulimo matalikilo() { amba(mpati(1, "mabala")) }')
    with pytest.raises(TongaRuntimeError):
        Interpreter().interpret(program)


def test_interpreter_instance_can_be_reused_without_state_leak(capsys):
    program = parse_source('mulimo matalikilo() { amba("kabotu") }')
    interpreter = Interpreter()
    interpreter.interpret(program)
    interpreter.interpret(program)
    assert capsys.readouterr().out.splitlines() == ["kabotu", "kabotu"]
