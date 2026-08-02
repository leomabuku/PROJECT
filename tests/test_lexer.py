import pytest

from tongalang.lexer import tokenize_source
from tongalang.errors import TongaLexicalError


def token_types(source):
    return [tok.type for tok in tokenize_source(source)]


def test_keywords_are_recognized():
    source = """
    zina x = 10
    amba(x)
    bala()
    kuti (x inda 5) {}
    naaba (x eelana 5) {}
    nakunyina {}
    kufumbwa (x ceya 10) {}
    induluka i kuzwa 1 kusika 5 {}
    cita {} kusikila (x eelana 5)
    leka
    mulimo matalikilo() {}
    pilula x
    """

    types = token_types(source)

    assert "ZINA" in types
    assert "AMBA" in types
    assert "BALA" in types
    assert "KUTI" in types
    assert "NAABA" in types
    assert "NAKUNYINA" in types
    assert "KUFUMBWA" in types
    assert "INDULUKA" in types
    assert "KUZWA" in types
    assert "KUSIKA" in types
    assert "CITA" in types
    assert "KUSIKILA" in types
    assert "LEKA" in types
    assert "MULIMO" in types
    assert "MATALIKILO" in types
    assert "PILULA" in types


def test_boolean_literals():
    tokens = tokenize_source("iiyi pepe")

    assert tokens[0].type == "BOOL"
    assert tokens[0].value is True

    assert tokens[1].type == "BOOL"
    assert tokens[1].value is False


def test_identifiers_are_case_insensitive():
    tokens = tokenize_source("zina Age = 20")

    assert tokens[1].type == "IDENT"
    assert tokens[1].value == "age"


def test_numbers():
    tokens = tokenize_source("10 20.5")

    assert tokens[0].value == 10
    assert tokens[1].value == 20.5


def test_strings():
    tokens = tokenize_source('"Hello\\nWorld"')

    assert tokens[0].type == "STRING"
    assert tokens[0].value == "Hello\nWorld"


def test_semicolon_is_rejected():
    with pytest.raises(TongaLexicalError):
        tokenize_source("zina x = 10;")


def test_illegal_character_is_rejected():
    with pytest.raises(TongaLexicalError):
        tokenize_source("zina x = @")