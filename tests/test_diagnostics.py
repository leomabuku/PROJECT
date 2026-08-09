from __future__ import annotations

from pathlib import Path

import pytest

from tongalang.diagnostics import analyze_source, apply_fix, diagnostic_from_error
from tongalang.errors import (
    CallDepthExceededError,
    ConversionError,
    DivisionByZeroError,
    ExecutionCancelledError,
    FunctionNotDefinedError,
    MainFunctionMissingError,
    SourceEncodingError,
    SourceNotFoundError,
    SourceWriteError,
    TypeMismatchError,
    UndefinedVariableError,
    WrongArgumentCountError,
)


@pytest.mark.parametrize(
    ("source", "code", "fixed_text"),
    [
        ("mul imo matalikilo() { }", "TL-L106", "mulimo matalikilo() { }"),
        ('mulimo matalikilo() { am ba("x") }', "TL-L106", 'mulimo matalikilo() { amba("x") }'),
        ('mulimo matalikilo() { amba("x"); }', "TL-L102", 'mulimo matalikilo() { amba("x") }'),
        ("mulimo mataliklo() { }", "TL-R110", "mulimo matalikilo() { }"),
    ],
)
def test_safe_typo_fixes_are_guarded_and_apply(source: str, code: str, fixed_text: str):
    diagnostic = analyze_source(source)[0]
    assert diagnostic.code == code
    fix = next(item for item in diagnostic.fixes if item.is_editable)
    assert apply_fix(source, fix) == fixed_text


def test_stale_fix_is_rejected():
    source = 'mulimo matalikilo() { amba("x"); }'
    fix = next(item for item in analyze_source(source)[0].fixes if item.is_editable)
    with pytest.raises(ValueError, match="code changed"):
        apply_fix(source.replace('"x"', '"longer"'), fix)


def test_unclosed_delimiter_gets_end_insertion_fix():
    source = "mulimo matalikilo() {\n    amba(1)\n"
    diagnostic = analyze_source(source)[0]
    assert diagnostic.code == "TL-S104"
    fix = next(item for item in diagnostic.fixes if item.is_editable)
    assert apply_fix(source, fix).endswith("\n}")


def test_undefined_variable_near_match_gets_replacement():
    source = 'mulimo matalikilo() { zina zyina = "Leo" amba(zyinaa) }'
    diagnostic = analyze_source(source)[0]
    assert diagnostic.code == "TL-R101"
    fix = next(item for item in diagnostic.fixes if item.is_editable)
    assert "amba(zyina)" in apply_fix(source, fix)


def test_ambiguous_extra_variable_word_has_guidance_but_no_edit():
    source = "mulimo matalikilo() { zina ms usikwiiya = iiyi }"
    diagnostic = analyze_source(source)[0]
    assert diagnostic.code.startswith("TL-S")
    assert diagnostic.fixes
    assert not any(item.is_editable for item in diagnostic.fixes)


def test_static_analysis_does_not_execute_bala(monkeypatch):
    def fail_input(*_args, **_kwargs):
        raise AssertionError("live diagnostics must not request input")

    monkeypatch.setattr("builtins.input", fail_input)
    assert analyze_source('mulimo matalikilo() { zina x = bala("Number: ") }') == ()


@pytest.mark.parametrize(
    "error",
    [
        UndefinedVariableError("x", 1, 1),
        DivisionByZeroError(1, 1),
        TypeMismatchError("-", "text", "number", 1, 1),
        FunctionNotDefinedError("bula", 1, 1),
        WrongArgumentCountError("mpati", 2, 1, 1, 1),
        MainFunctionMissingError(),
        ConversionError("abc", "number", 1, 1),
        ExecutionCancelledError(1, 1),
        CallDepthExceededError(10, 1, 1),
        SourceNotFoundError(Path("missing.tg")),
        SourceEncodingError(Path("bad.tg")),
        SourceWriteError(Path("locked.tg"), "permission denied"),
    ],
)
def test_every_error_family_has_beginner_guidance(error):
    diagnostic = diagnostic_from_error(error, "x")
    assert diagnostic.code == error.code
    assert diagnostic.summary_tonga
    assert diagnostic.summary_english
    assert diagnostic.fixes
    assert all(item.explanation_tonga and item.explanation_english for item in diagnostic.fixes)


def test_missing_main_is_appended_after_a_trailing_newline():
    source = "zina x = 1\n"
    diagnostic = analyze_source(source)[0]
    fix = next(item for item in diagnostic.fixes if item.is_editable)
    updated = apply_fix(source, fix)
    assert updated.startswith("zina x = 1\n")
    assert "mulimo matalikilo()" in updated


def test_valid_program_has_no_static_diagnostics():
    source = 'mulimo matalikilo() { zina x = 2 amba(x) }'
    assert analyze_source(source) == ()
