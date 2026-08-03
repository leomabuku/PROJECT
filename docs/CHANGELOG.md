# TongaLang Project Changelog

## 3 August 2026

This entry documents the current public implementation and the supporting
evidence added during the portfolio update.

### Language and runtime

- Implemented a PLY-based lexer and parser, typed AST nodes, runtime
  environments, native functions, and controlled diagnostics.
- Added variables, arithmetic, Boolean logic, conditions, loops, functions,
  scope, interactive input, output, conversion functions, and `break` support.
- Added stable bilingual lexical, syntax, and runtime error messages with codes
  and learner-oriented hints.

### Educational IDE

- Separated the language engine from the Tkinter interface so command-line and
  graphical execution use the same interpreter.
- Added source editing, syntax highlighting, file controls, interactive input,
  output controls, configurable themes and language preferences.
- Added graphical and accessible-outline AST views with source locations, node
  explanations, search, zoom, navigation, and deterministic layout.

### Testing and documentation

- Added 17 executable `.tg` examples covering the language surface.
- Added unit, integration, GUI, adversarial, safety, and example-integrity test
  suites, plus a graphical Test Lab for regression and weakness-probe results.
- Added a complete language reference, grammar specification, implementation
  audit, testing guide, and UI audit.

### Portfolio evidence

- Added current source-editor, AST-explorer, and Test Lab screenshots.
- Added a compressed one-minute IDE walkthrough while retaining the original
  recording outside the repository.
