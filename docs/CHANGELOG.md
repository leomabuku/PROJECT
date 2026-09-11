# TongaLang Project Changelog

## 11 September 2026

### Installable desktop distribution

- Added the selected TongaLang logo throughout the IDE, About screen, executable, Windows installer and uninstaller, shortcuts, Installed Apps entry, Linux launcher, and repository documentation.
- Added a per-user Windows setup executable with Start Menu and optional Desktop shortcuts, Installed Apps registration, bundled examples and a dedicated uninstaller.
- Added a reproducible PowerShell build that packages the IDE with PyInstaller, compiles the Windows setup/uninstaller with the built-in .NET Framework tools, and produces a SHA-256 checksum.
- Added Linux source-install and standalone-build scripts plus distribution-specific Tkinter prerequisites and troubleshooting guidance.
- Documented the unsigned-build SmartScreen notice so learners can make an informed installation decision without disabling security software.
- Ran the installer end to end on Windows, launched the installed IDE, and captured a privacy-reviewed gallery covering setup, editing, diagnostics, input and output, settings, AST, console, grammar, About, and both themes.

## 9 August 2026

### Beginner guidance and recovery

- Added side-effect-free live lexical, syntax, and semantic diagnostics with bilingual explanations, exact source ranges, and guarded one-click fixes for deterministic mistakes.
- Added a collapsible Problems pane with Go to Code, Copy Details, keyboard navigation, stale-edit protection, and undoable source repairs.
- Added typed source-file diagnostics and kept unexpected internal details behind an explicit copy action.

### IDE usability

- Added Back and Forward view history while preserving the independently collapsible navigation menu.
- Added one shared, resizable Problems/Program Input dock for Editor and Output. `bala()` requests open Program Input automatically, submitted values are echoed into Output, and execution resumes after a single guarded queue handoff.
- Removed the duplicate Input/I/O page and Output input bar so there is one clear input workflow.
- Rebuilt Settings as grouped, collapsible, scrollable sections with mouse-wheel, touchpad, Linux wheel, and keyboard scrolling plus inline numeric validation.
- Rebuilt About as themed, readable sections covering the author, academic context, project purpose, architecture, quick start, features, language overview, and safety scope.
- Added accessible dark/light semantic colors for declarations, input/output, conditions, loops, functions, the main entry point, booleans, and word operators.

### Verification

- Restored the two runnable examples used during typo testing and moved the mistakes into dedicated automated diagnostic tests.
- Expanded the suite to cover fixes, stale edits, live-analysis safety, color contrast, navigation, scrolling, About content, dock persistence, blank and repeated input, visible transcripts, safe stop, and GUI recovery workflows.

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
