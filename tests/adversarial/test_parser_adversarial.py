from __future__ import annotations

import pytest

from tongalang.ast_nodes import Program
from tongalang.errors import TongaLangError, TongaSyntaxError
from tongalang.parser import parse_source


INVALID_PROGRAMS = [
    "mulimo matalikilo( { }",
    "mulimo matalikilo() { zina = 1 }",
    "mulimo matalikilo() { zina x 1 }",
    "mulimo matalikilo() { kuti { } }",
    "mulimo matalikilo() { kuti (iiyi) }",
    "mulimo matalikilo() { naaba (iiyi) { } }",
    "mulimo matalikilo() { nakunyina { } }",
    "mulimo matalikilo() { induluka i 1 kusika 2 { } }",
    "mulimo matalikilo() { induluka i kuzwa 1 2 { } }",
    "mulimo matalikilo() { cita { } kusikila }",
    "mulimo matalikilo() { amba(,) }",
    "mulimo matalikilo() { amba(1 2) }",
    "mulimo matalikilo() { zina x = (1 + ) }",
    "mulimo matalikilo() { pilula, 1 }",
    "mulimo matalikilo() { leka, 1 }",
]


@pytest.mark.parametrize("source", INVALID_PROGRAMS)
def test_malformed_programs_raise_only_domain_errors(source):
    with pytest.raises(TongaLangError):
        parse_source(source)


def test_misspelled_main_name_gets_runtime_repair_suggestion():
    source = "mulimo mataliklo() { }"
    from tongalang.errors import MainFunctionMissingError
    from tongalang.interpreter import Interpreter

    with pytest.raises(MainFunctionMissingError) as captured:
        Interpreter().interpret(parse_source(source))
    assert captured.value.code == "TL-R110"
    assert "matalikilo" in (captured.value.hint_english or "")


def test_unexpected_eof_has_last_source_position_and_caret():
    source = "mulimo matalikilo() {\n    amba(1)"
    with pytest.raises(TongaSyntaxError) as captured:
        parse_source(source)
    error = captured.value
    assert (error.code, error.line, error.column) == ("TL-S101", 2, 12)
    assert "^" in error.format_message(source=source)


def test_deep_but_reasonable_grouping_parses_without_python_recursion_error():
    expression = "(" * 80 + "1" + ")" * 80
    program = parse_source(f"mulimo matalikilo() {{ amba({expression}) }}")
    assert isinstance(program, Program)


def test_large_declaration_set_parses_completely():
    declarations = "\n".join(f"zina n{i} = {i}" for i in range(250))
    program = parse_source(f"mulimo matalikilo() {{\n{declarations}\n}}")
    main = program.statements[0]
    assert len(main.body.statements) == 250


def test_repeated_parse_does_not_leak_previous_source_location():
    with pytest.raises(TongaSyntaxError):
        parse_source("\n\nmulimo matalikilo() {")
    with pytest.raises(TongaSyntaxError) as captured:
        parse_source("mulimo matalikilo() {")
    assert captured.value.line == 1


def test_non_text_source_has_explicit_api_failure():
    with pytest.raises(TypeError, match="source must be text"):
        parse_source(None)  # type: ignore[arg-type]
