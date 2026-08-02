from __future__ import annotations

import pytest

from tongalang.errors import TongaLexicalError
from tongalang.lexer import tokenize_source


def test_unicode_string_is_preserved_without_mojibake():
    tokens = tokenize_source('amba("Mwaabonwa - zyina lyangu")')
    string = next(token for token in tokens if token.type == "STRING")
    assert string.value == "Mwaabonwa - zyina lyangu"


def test_supported_escape_sequences_are_decoded_explicitly():
    tokens = tokenize_source(r'amba("mulongo\nciindi\t\"mabala\"")')
    string = next(token for token in tokens if token.type == "STRING")
    assert string.value == 'mulongo\nciindi\t"mabala"'


@pytest.mark.parametrize("escape", [r"\q", r"\a", r"\v", r"\0", r"\u"])
def test_unknown_escape_sequences_fail_with_stable_code(escape):
    with pytest.raises(TongaLexicalError) as captured:
        tokenize_source(f'amba("kabotu{escape}")')
    assert captured.value.code == "TL-L104"
    assert "escape sequence" in captured.value.english_message


def test_unterminated_block_comment_is_reported_as_lexical_error():
    with pytest.raises(TongaLexicalError) as captured:
        tokenize_source("mulimo matalikilo() { /* kambonyi")
    assert captured.value.code == "TL-L105"
    assert captured.value.line == 1


@pytest.mark.parametrize("character", ["@", "#", "?", "`", "[", "]", ":", "&", "|"])
def test_illegal_character_never_leaks_raw_lexer_exception(character):
    with pytest.raises(TongaLexicalError) as captured:
        tokenize_source(f"zina x = 1 {character}")
    assert captured.value.code.startswith("TL-L")
    assert captured.value.line == 1
    assert captured.value.column is not None


def test_semicolon_error_points_to_exact_line_and_column():
    source = "zina x = 1\namba(x);\n"
    with pytest.raises(TongaLexicalError) as captured:
        tokenize_source(source)
    error = captured.value
    assert (error.line, error.column, error.code) == (2, 8, "TL-L102")
    rendered = error.format_message(source=source)
    assert "2 | amba(x);" in rendered
    assert rendered.rstrip().endswith("Remove the semicolon at the end of the statement.")


def test_very_large_integer_remains_exact():
    digits = "9" * 500
    token = tokenize_source(digits)[0]
    assert token.type == "NUMBER"
    assert str(token.value) == digits


def test_new_lexer_instances_do_not_leak_line_numbers():
    assert tokenize_source("\n\n11")[0].lineno == 3
    assert tokenize_source("12")[0].lineno == 1


def test_crlf_and_block_comments_keep_following_location_correct():
    source = "/* a\r\nb\r\n*/\r\nzina x = 1"
    zina = tokenize_source(source)[0]
    assert zina.type == "ZINA"
    assert zina.lineno == 4
