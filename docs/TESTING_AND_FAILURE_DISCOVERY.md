# TongaLang Testing and Failure-Discovery Guide

## Purpose

This suite is designed to find weaknesses, not merely to confirm the happy path. It combines regression tests with malformed input, boundary values, hostile source text, cancellation, recursion, resource limits, error-contract checks, AST-layout checks, example integrity, and repeated execution.

## Visual command

From the project folder, run:

```powershell
python -m testlab --autorun
```

On Windows you can also double-click `run_test_lab.bat`.

The Test Lab displays total tests, passes, failures, skips, weakness-probe count, line coverage, duration, per-test timing, categories, full failure diagnostics, and raw pytest output. Results are saved under `test-results/run-<date>-<time>-<scope>/` as JUnit XML, JSON, coverage JSON when Coverage.py is installed, and console text.

## Automated commands

Run everything without a GUI:

```powershell
python -m testlab --headless
```

Run only tests intended to stress or break the system:

```powershell
python -m testlab --headless --weakness
```

Run pytest directly:

```powershell
python -m pytest -q
```

Install development metrics support:

```powershell
python -m pip install -r requirements-dev.txt
```

## Test strategy

- Lexer: valid and invalid characters, unterminated constructs, Unicode strings, escape sequences, comments, line/column accuracy, very large values, and long inputs.
- Parser: truncated programs, misspelled keywords, unbalanced grouping, malformed branches, repeated parsing, deep expressions, and large declaration sets.
- Interpreter: type errors, zero division and modulus, loop limits, user cancellation, recursion limits, invalid configuration, repeated interpreter use, scopes, functions, and native calls.
- Error handling: stable diagnostic codes, bilingual and Tonga-only modes, actionable hints, source excerpts, caret placement, and absence of raw Python exceptions in user-facing paths.
- AST: deterministic layout, parent-child direction, centring, depth, categories, empty input, search data, and source positions.
- Examples: every example parses, every example runs with controlled input, filenames and learner-facing content use Tonga, and no obsolete English example names remain.
- GUI support: importability without a display, input hand-off, output forwarding, execution-state contracts, and test-lab result parsing.

## Reading the metrics

A green run means the encoded expectations passed; it does not prove that no defects exist. Line coverage shows which executable lines ran, while branch coverage shows how many decision outcomes ran. High coverage cannot replace strong assertions. A failure under `tests/adversarial/` should be treated as a discovered weakness and fixed or explicitly documented rather than deleted to recover a green result.

## Adding a regression test

When a defect is found, first create the smallest test that reproduces it. Confirm that the test fails for the intended reason, implement the fix, then rerun the full suite. Keep resource-limit tests deterministic and avoid timing thresholds that can fail merely because another application is busy.
