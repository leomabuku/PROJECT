from __future__ import annotations

from pathlib import Path
import re

import pytest

from tongalang.errors import (
    CallDepthExceededError,
    ConversionError,
    DivisionByZeroError,
    ExecutionCancelledError,
    FunctionNotDefinedError,
    MainFunctionMissingError,
    SourceEncodingError,
    TypeMismatchError,
    UndefinedVariableError,
    WrongArgumentCountError,
)
from tongalang.runner import run_file


ERRORS = [
    UndefinedVariableError("x", 2, 4),
    DivisionByZeroError(2, 4),
    TypeMismatchError("-", "text", "number", 2, 4),
    FunctionNotDefinedError("bula", 2, 4),
    WrongArgumentCountError("mulimo", 2, 1, 2, 4),
    MainFunctionMissingError(),
    ConversionError("x", "number", 2, 4),
    ExecutionCancelledError(2, 4),
    CallDepthExceededError(20, 2, 4),
]


@pytest.mark.parametrize("error", ERRORS)
def test_diagnostics_have_machine_searchable_codes_and_actionable_text(error):
    assert re.fullmatch(r"TL-[A-Z]\d{3}", error.code)
    assert error.tonga_message
    assert error.english_message
    assert error.category_tonga
    assert error.category_english
    assert str(error).startswith(f"[{error.code}]")


def test_tonga_only_mode_removes_english_display_labels():
    message = UndefinedVariableError("x", 2, 4).format_message(mode="tonga")
    for english_label in ("Error:", "Hint:", "Line ", "Column "):
        assert english_label not in message


def test_source_excerpt_marks_the_exact_column():
    source = "mulimo matalikilo() {\n    amba(x)\n}"
    message = UndefinedVariableError("x", 2, 10).format_message(source=source)
    lines = message.splitlines()
    excerpt_index = next(index for index, line in enumerate(lines) if "amba(x)" in line)
    assert lines[excerpt_index + 1].endswith("         ^")


def test_non_utf8_source_file_has_repair_instruction(tmp_path: Path):
    source = tmp_path / "yasweka.tg"
    source.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(SourceEncodingError) as captured:
        run_file(source)
    assert captured.value.code == "TL-F102"
    assert "UTF-8" in captured.value.english_message
