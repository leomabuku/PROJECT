from __future__ import annotations

from pathlib import Path

from testlab.runner import TestCaseResult, TestRunResult, _parse_junit


def test_parse_junit_preserves_status_duration_and_failure_detail(tmp_path: Path):
    report = tmp_path / "junit.xml"
    report.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
        <testsuites><testsuite tests="3">
          <testcase classname="tests.test_lexer" name="test_good" time="0.1" />
          <testcase classname="tests.adversarial.test_parser" name="test_bad" time="0.2"><failure message="boom">trace</failure></testcase>
          <testcase classname="tests.test_gui" name="test_skip" time="0"><skipped message="no display" /></testcase>
        </testsuite></testsuites>""",
        encoding="utf-8",
    )
    tests = _parse_junit(report)
    assert [test.status for test in tests] == ["passed", "failure", "skipped"]
    assert tests[1].category == "Weakness probes"
    assert "boom" in tests[1].detail


def test_test_run_result_computes_dashboard_metrics():
    result = TestRunResult(
        started_at="2026-07-21T00:00:00",
        scope="all",
        duration=1.25,
        return_code=1,
        tests=(
            TestCaseResult("a", "tests.test_lexer", "passed", 0.1),
            TestCaseResult("b", "tests.adversarial.test_parser", "failed", 0.2),
            TestCaseResult("c", "tests.test_gui", "skipped", 0.0),
        ),
        coverage_percent=88.5,
        branch_coverage_percent=75.0,
        output="",
        artifact_dir="x",
        command=("python",),
    )
    assert (result.total, result.passed, result.failed, result.skipped) == (3, 1, 1, 1)
    assert result.weakness_probes == 1
    assert not result.success
