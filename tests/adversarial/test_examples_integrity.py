from __future__ import annotations

import builtins
from pathlib import Path
import re

import pytest

from tongalang.interpreter import Interpreter
from tongalang.parser import parse_source


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = PROJECT_ROOT / "examples"
EXAMPLES = tuple(sorted(EXAMPLE_DIR.glob("*.tg")))
EXPECTED_NAMES = {
    "01_mazyina.tg",
    "02_makani_aakuti.tg",
    "03_kuinduluka_kufumbwa.tg",
    "04_kuinduluka_kuzwa_kusika.tg",
    "05_cita_kusikila.tg",
    "06_milimo.tg",
    "07_kusala_mulimo.tg",
    "08_mubwezezyo_wanamba.tg",
    "09_bupanduluzi_bwacipimo.tg",
    "10_kubandika_kusikila_kuyomwe.tg",
    "11_cibalo_cakubandika.tg",
    "12_kukamantanya_mabala.tg",
    "13_kusandula_misyobo.tg",
    "14_kujana_namba.tg",
    "15_mbaka_amazyina.tg",
    "16_milimo_yakumbele.tg",
    "17_kweelanya_iiyi_pepe.tg",
}


def test_example_catalogue_uses_tonga_filenames_only():
    assert {path.name for path in EXAMPLES} == EXPECTED_NAMES


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda path: path.name)
def test_every_example_parses_and_runs(path: Path, monkeypatch, capsys):
    value = "75" if path.name.startswith("09_") else "1"
    monkeypatch.setattr(builtins, "input", lambda _prompt="": value)
    source = path.read_text(encoding="utf-8")
    Interpreter(max_loop_iterations=1000).interpret(parse_source(source))
    capsys.readouterr()


def test_example_content_has_no_known_english_learner_copy():
    blocked = {
        "adult", "age", "app", "area", "arithmetic", "ascending", "biggest",
        "card", "checking", "child", "choice", "comment", "condition", "converted",
        "demo", "descending", "distinction", "doubled", "factorial", "found", "grade",
        "height", "invalid", "maximum", "menu", "merit", "minimum", "missing", "name",
        "number", "paid", "pass", "perimeter", "program", "repeat", "report", "result",
        "search", "student", "subtract", "table", "target", "text", "total", "true",
        "valid", "version", "welcome", "width",
    }
    for path in EXAMPLES:
        words = set(re.findall(r"[A-Za-z]+", path.read_text(encoding="utf-8").lower()))
        assert not words.intersection(blocked), f"English learner copy found in {path.name}: {words.intersection(blocked)}"
