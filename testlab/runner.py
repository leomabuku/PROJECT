from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class TestCaseResult:
    __test__ = False
    name: str
    classname: str
    status: str
    duration: float
    detail: str = ""

    @property
    def category(self) -> str:
        text = f"{self.classname}.{self.name}".lower()
        if "adversarial" in text:
            return "Weakness probes"
        if "lexer" in text:
            return "Lexer"
        if "parser" in text:
            return "Parser"
        if "interpreter" in text or "runtime" in text:
            return "Interpreter"
        if "error" in text:
            return "Error handling"
        if "ast" in text:
            return "AST"
        if "gui" in text:
            return "GUI"
        if "example" in text:
            return "Examples"
        return "Other"


@dataclass(frozen=True)
class TestRunResult:
    __test__ = False
    started_at: str
    scope: str
    duration: float
    return_code: int
    tests: tuple[TestCaseResult, ...]
    coverage_percent: float | None
    branch_coverage_percent: float | None
    output: str
    artifact_dir: str
    command: tuple[str, ...]

    @property
    def total(self) -> int:
        return len(self.tests)

    def count(self, status: str) -> int:
        return sum(1 for test in self.tests if test.status == status)

    @property
    def passed(self) -> int:
        return self.count("passed")

    @property
    def failed(self) -> int:
        return self.count("failed") + self.count("error")

    @property
    def skipped(self) -> int:
        return self.count("skipped")

    @property
    def weakness_probes(self) -> int:
        return sum(1 for test in self.tests if test.category == "Weakness probes")

    @property
    def success(self) -> bool:
        return self.return_code == 0 and self.failed == 0

    def category_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for test in self.tests:
            counts[test.category] = counts.get(test.category, 0) + 1
        return dict(sorted(counts.items()))


def _parse_junit(path: Path) -> tuple[TestCaseResult, ...]:
    if not path.exists():
        return ()
    root = ET.parse(path).getroot()
    results: list[TestCaseResult] = []
    for item in root.iter("testcase"):
        status = "passed"
        detail = ""
        for child_status in ("failure", "error", "skipped"):
            child = item.find(child_status)
            if child is not None:
                status = child_status
                detail = (child.get("message") or "") + ("\n" + (child.text or "") if child.text else "")
                detail = detail.strip()
                break
        results.append(
            TestCaseResult(
                name=item.get("name", "unnamed"),
                classname=item.get("classname", ""),
                status=status,
                duration=float(item.get("time", "0") or 0),
                detail=detail,
            )
        )
    return tuple(results)


def _parse_coverage(path: Path) -> tuple[float | None, float | None]:
    if not path.exists():
        return None, None
    data = json.loads(path.read_text(encoding="utf-8"))
    totals = data.get("totals", {})
    line_percent = totals.get("percent_covered")
    covered_branches = totals.get("covered_branches")
    num_branches = totals.get("num_branches")
    branch_percent = None
    if isinstance(covered_branches, int) and isinstance(num_branches, int) and num_branches:
        branch_percent = covered_branches / num_branches * 100
    return (float(line_percent) if line_percent is not None else None, branch_percent)


def run_test_suite(
    project_root: str | Path,
    *,
    scope: str = "all",
    timeout_seconds: int = 300,
) -> TestRunResult:
    root = Path(project_root).resolve()
    if scope not in {"all", "weakness"}:
        raise ValueError('scope must be "all" or "weakness"')

    started = datetime.now()
    stamp = started.strftime("%Y%m%d-%H%M%S")
    artifact_dir = root / "test-results" / f"run-{stamp}-{scope}"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    junit_path = artifact_dir / "junit.xml"
    coverage_path = artifact_dir / "coverage.json"
    output_path = artifact_dir / "console.txt"
    summary_path = artifact_dir / "summary.json"
    target = "tests" if scope == "all" else "tests/adversarial"

    coverage_available = importlib.util.find_spec("coverage") is not None
    if coverage_available:
        command = [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--branch",
            "--source=tongalang,gui",
            "-m",
            "pytest",
            target,
            "-q",
            f"--junitxml={junit_path}",
        ]
    else:
        command = [sys.executable, "-m", "pytest", target, "-q", f"--junitxml={junit_path}"]

    started_timer = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        return_code = completed.returncode
        output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    except subprocess.TimeoutExpired as error:
        return_code = 124
        output = (
            f"Test run exceeded the {timeout_seconds}-second safety timeout.\n"
            f"Partial stdout:\n{error.stdout or ''}\nPartial stderr:\n{error.stderr or ''}"
        )

    if coverage_available and junit_path.exists():
        coverage_command = [sys.executable, "-m", "coverage", "json", "-o", str(coverage_path)]
        coverage_run = subprocess.run(
            coverage_command,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        if coverage_run.returncode != 0:
            output += "\nCoverage report warning:\n" + (coverage_run.stderr or coverage_run.stdout)

    duration = time.perf_counter() - started_timer
    tests = _parse_junit(junit_path)
    coverage_percent, branch_percent = _parse_coverage(coverage_path)
    result = TestRunResult(
        started_at=started.isoformat(timespec="seconds"),
        scope=scope,
        duration=duration,
        return_code=return_code,
        tests=tests,
        coverage_percent=coverage_percent,
        branch_coverage_percent=branch_percent,
        output=output.strip(),
        artifact_dir=str(artifact_dir),
        command=tuple(command),
    )
    output_path.write_text(result.output, encoding="utf-8")
    summary = {
        "started_at": result.started_at,
        "scope": result.scope,
        "duration_seconds": result.duration,
        "return_code": result.return_code,
        "success": result.success,
        "metrics": {
            "total": result.total,
            "passed": result.passed,
            "failed_or_error": result.failed,
            "skipped": result.skipped,
            "weakness_probes": result.weakness_probes,
            "line_coverage_percent": result.coverage_percent,
            "branch_coverage_percent": result.branch_coverage_percent,
        },
        "categories": result.category_counts(),
        "tests": [asdict(test) | {"category": test.category} for test in result.tests],
        "command": list(result.command),
        "artifact_dir": result.artifact_dir,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (root / "test-results" / "latest-summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return result
