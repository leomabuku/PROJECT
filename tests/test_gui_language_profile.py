from gui.language_profile import build_language_profile
from gui.syntax_highlighter import DEFAULT_SYNTAX_THEMES


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


def test_language_profile_exposes_semantic_reserved_word_groups():
    profile = build_language_profile()
    assert profile.declaration_words == ("zina",)
    assert set(profile.input_output_words) == {"amba", "bala"}
    assert set(profile.conditional_words) == {"kuti", "naaba", "nakunyina"}
    assert "induluka" in profile.loop_words
    assert set(profile.function_words) == {"mulimo", "pilula"}
    assert profile.entry_point_words == ("matalikilo",)


def test_semantic_keyword_palette_meets_normal_text_contrast():
    def luminance(color: str) -> float:
        values = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in values]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    keys = (
        "declarations",
        "input_output",
        "conditionals",
        "loops",
        "functions",
        "entry_point",
        "booleans",
        "word_operators",
    )
    for theme in DEFAULT_SYNTAX_THEMES.values():
        background = luminance(theme.editor_bg)
        for key in keys:
            foreground = luminance(getattr(theme, key))
            ratio = (max(foreground, background) + 0.05) / (min(foreground, background) + 0.05)
            assert ratio >= 4.5, (key, ratio)
