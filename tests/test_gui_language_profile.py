from gui.language_profile import build_language_profile


def test_language_profile_is_derived_from_runtime_sources():
    profile = build_language_profile()

    assert "zina" in profile.keywords
    assert "amba" in profile.keywords
    assert "matalikilo" in profile.keywords
    assert "iiyi" in profile.booleans
    assert "pepe" in profile.booleans
    assert "aa" in profile.logical_operators
    assert "inda" in profile.comparison_operators
    assert "mpati" in profile.native_functions
    assert "mabala" in profile.native_functions
    assert "+" in profile.arithmetic_operators
    assert "==" in profile.comparison_operators


def test_language_profile_excludes_old_langa_keyword():
    profile = build_language_profile()

    assert "langa" not in profile.all_words
