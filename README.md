# TongaLang

TongaLang is a minimal interpreted educational programming language using
Tonga-derived keywords. It is built in Python with PLY and is designed for
beginner programming education at The Copperbelt University.

The language intentionally keeps a small surface area:

- C/Java/JavaScript-style braces for blocks: `{ ... }`
- Parentheses for conditions and calls: `kuti (x inda 5) { ... }`
- No semicolons
- A required main entry point: `mulimo matalikilo() { ... }`
- Range-based `induluka` loops instead of C-style `for` loops

## Project Structure

```text
TongaLang/
|-- main.py
|-- requirements.txt
|-- README.md
|-- examples/
|-- gui/
|   |-- __init__.py
|   |-- ast_tree.py
|   |-- app.py
|   |-- language_profile.py
|   |-- runtime.py
|   `-- syntax_highlighter.py
|-- tests/
`-- tongalang/
    |-- __init__.py
    |-- ast_nodes.py
    |-- ast_visualizer.py
    |-- environment.py
    |-- errors.py
    |-- interpreter.py
    |-- lexer.py
    |-- native_functions.py
    |-- parser.py
    `-- runner.py
```

Generated Python caches, PLY parser tables, test caches, and packaging output
are ignored by `.gitignore`.

## Full Setup on a New Machine

TongaLang requires **Python 3.10 or newer** because the source code uses modern
type hints such as `int | None`.

### 1. Install Python

Install Python 3.10+ from:

```text
https://www.python.org/downloads/
```

On Windows, tick **Add python.exe to PATH** during installation.

After installation, open a new terminal and check:

```powershell
python --version
```

If `python` is not recognized on Windows, try:

```powershell
py -3 --version
```

If neither command works, Python is not correctly installed or not available on
PATH.

### 2. Get the Project Files

Copy, unzip, or clone the project folder onto the new machine, then open a
terminal in the project root, the folder containing `main.py` and
`requirements.txt`.

Example:

```powershell
cd "C:\path\to\TongaLang"
```

### 3. Quick Windows Setup

On Windows, the easiest setup is:

```powershell
.\setup_project.bat
```

The script:

- checks that Python is available
- creates `.venv` if it does not exist
- upgrades `pip`
- installs `requirements.txt`
- prints commands for launching the IDE, running examples, and running tests

### 4. Manual Setup

If you prefer to set up manually, run:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If your system uses the Python launcher instead of `python`, use:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Verify the Installation

Run the test suite:

```powershell
python -m pytest -q
```

Run one example from the command line:

```powershell
python main.py examples/01_mazyina.tg
```

Launch the GUI:

```powershell
python -m gui.app
```

### 6. Troubleshooting Setup

- If `python` is not recognized, reinstall Python and enable **Add python.exe to PATH**.
- If the GUI does not open, make sure your Python installation includes Tkinter. The official Windows Python installer normally includes it.
- If dependencies are missing, activate the virtual environment and run `python -m pip install -r requirements.txt` again.
- If tests cannot import project modules, make sure you are running commands from the project root folder.
- If a virtual environment was copied from another computer and fails, delete `.venv` and recreate it on the new machine.

## Running Programs

Run a `.tg` file from the command line:

```powershell
python main.py examples/01_mazyina.tg
```

Show the version:

```powershell
python main.py --version
```

Set a custom loop safety limit:

```powershell
python main.py --max-loop 1000 examples/03_kuinduluka_kufumbwa.tg
```

## Example Programs

The `examples/` folder contains small programs for demonstrations and testing
language features:

| File | Topic demonstrated |
| --- | --- |
| `examples/01_mazyina.tg` | Global and local variables, booleans, output |
| `examples/02_makani_aakuti.tg` | `kuti`, `naaba`, `nakunyina` conditionals |
| `examples/03_kuinduluka_kufumbwa.tg` | `kufumbwa` while loop |
| `examples/04_kuinduluka_kuzwa_kusika.tg` | Ascending and descending `induluka` ranges |
| `examples/05_cita_kusikila.tg` | `cita ... kusikila` do-until loop |
| `examples/06_milimo.tg` | User functions, `pilula`, native functions |
| `examples/07_kusala_mulimo.tg` | Interactive menu with `bala()` input |
| `examples/08_mubwezezyo_wanamba.tg` | Arithmetic, modulo, comparisons |
| `examples/09_bupanduluzi_bwacipimo.tg` | Input-driven grade checker and numeric conversion |
| `examples/10_kubandika_kusikila_kuyomwe.tg` | Factorial using a while loop |
| `examples/11_cibalo_cakubandika.tg` | Nested range loops |
| `examples/12_kukamantanya_mabala.tg` | Comments and `$name` / `${name}` string interpolation |
| `examples/13_kusandula_misyobo.tg` | `mpati`, `inini`, `ngamabala`, `ninamba`, `namba`, `mabala` |
| `examples/14_kujana_namba.tg` | Loop search with `leka` break |
| `examples/15_mbaka_amazyina.tg` | Loop-local variables and assignment to outer scope |
| `examples/16_milimo_yakumbele.tg` | Calling functions before declaration |
| `examples/17_kweelanya_iiyi_pepe.tg` | `iiyi`, `pepe`, `aa`, `naa`, `tee` boolean logic |

Run any example with:

```powershell
python main.py examples/08_mubwezezyo_wanamba.tg
```

Interactive examples such as `07_kusala_mulimo.tg` and
`09_bupanduluzi_bwacipimo.tg` will pause for input when they reach `bala()`.

## GUI

Launch the Tkinter educational IDE:

```powershell
python -m gui.app
```

The GUI is designed for project demonstrations and includes:

- A modern editor with line numbers, current-line highlighting, and syntax highlighting
- Dark and light themes
- A collapsible navigation sidebar
- Dedicated Editor, Output, Input / I/O, AST, Console, Settings, and About views
- Interactive pause/resume input for `bala()`
- A zoomable, pannable AST diagram with visible parent-child connectors, colour-coded node roles, source links, search, and an accessible outline
- Internal console logs for tokenizing, parsing, AST generation, execution, input, and errors
- Syntax color customization from Settings
- Open and save actions for `.tg` files

### GUI Architecture

The IDE layer is split into focused modules:

- `gui/language_profile.py` reads the real lexer reserved-word table and native function registry so the GUI knows the implemented language.
- `gui/syntax_highlighter.py` applies theme-aware, customizable highlighting to the editor.
- `gui/runtime.py` provides the thread-safe input pause/resume bridge used when the interpreter calls `bala()`.
- `gui/ast_tree.py` converts AST nodes into educational rows and detail text.
- `gui/ast_canvas.py` lays out and draws the interactive parent-child tree diagram.
- `gui/app.py` assembles the Tkinter IDE shell, sidebar navigation, views, settings, logs, and execution flow.

### Interactive `bala()` Input

When a running program reaches `bala()`:

1. Execution pauses in the background worker thread.
2. The IDE state changes to `Waiting for input`.
3. The Input / I/O view opens automatically.
4. The user enters a value and presses Submit.
5. The value is passed back to the interpreter.
6. Execution resumes and already-printed output is preserved.

This gives `bala()` a live terminal-like experience without changing the
TongaLang interpreter semantics.

### Syntax Highlighting

Syntax highlighting is generated from the implementation, not a separate
hand-written language list. The GUI detects:

- keywords from `tongalang/lexer.py`
- booleans from the `BOOL` token mapping
- logical and comparison word operators from lexer token categories
- symbolic operators such as `+`, `==`, `&&`, and braces
- native functions from `tongalang/native_functions.py`
- identifiers, function calls, numbers, strings, and comments

Settings allows users to customize colors for keywords, strings, comments,
numbers, native functions, operators, current line, error line, and AST
highlight colors. Reset Defaults restores the built-in theme colors.

### AST and Console Views

The AST view parses the current source and displays a real node-link tree.
Parents are centred above their children, connectors make hierarchy explicit,
and colour distinguishes declarations, control flow, expressions, values, and
structural nodes. The diagram supports zooming, panning, fitting, search, and
direct navigation back to the source line. An accessible outline remains
available as an alternative representation. Selecting either representation
opens the same source-linked node inspector.

The Console view is separate from program output. It logs parsing, AST
generation, execution start/finish, input waits, submitted input, warnings, and
runtime errors. Logs can be filtered by All, Info, Warning, Error, or Debug.

## Language Entry Point

Every executable TongaLang program must define:

```tg
mulimo matalikilo() {
    amba("Program starts here")
}
```

Function declarations may appear before or after use. Variables declared
outside `matalikilo()` are global. Variables declared inside `matalikilo()` are
local to main. Variables declared inside loop bodies are local to that loop
iteration.

## Keywords

| TongaLang | Meaning |
| --- | --- |
| `zina` | variable declaration |
| `iiyi` | true |
| `pepe` | false |
| `amba` | print/output |
| `bala` | input |
| `kuti` | if |
| `naaba` | else-if |
| `nakunyina` | else |
| `aa` | logical AND |
| `naa` | logical OR |
| `tee` | logical NOT |
| `inda` | greater than |
| `ceya` | less than |
| `eelana` | equal to |
| `kufumbwa` | while |
| `induluka` | for/range loop |
| `kuzwa` | from/range start |
| `kusika` | to/range end |
| `cita` | do |
| `kusikila` | until / loop stop condition |
| `leka` | break |
| `mulimo` | function |
| `matalikilo` | main entry point |
| `pilula` | return |

`langa` is no longer part of TongaLang. Use `amba(...)` for output.

## Variables

Declare variables with `zina`:

```tg
zina name = "TongaLang"
zina age = 20
zina active = iiyi
```

Assign existing variables without `zina`:

```tg
age = age + 1
```

Semicolons are invalid:

```tg
zina age = 20;
```

## Output and Input

Print values with `amba`:

```tg
amba("Hello")
amba(age)
amba()
```

Read input with `bala()`:

```tg
zina name = bala("Enter name: ")
amba("Hello " + name)
```

Numeric input is converted automatically when possible. For example, input
`20` becomes the number `20`; other text remains text.

## Conditionals

```tg
mulimo matalikilo() {
    zina age = 18

    kuti (age inda 18) {
        amba("Adult")
    } naaba (age eelana 18) {
        amba("Just turned adult")
    } nakunyina {
        amba("Child")
    }
}
```

## Loops

`kufumbwa` is a while loop:

```tg
mulimo matalikilo() {
    zina x = 0

    kufumbwa (x ceya 3) {
        amba(x)
        x = x + 1
    }
}
```

`induluka` is an inclusive range loop. Ascending and descending ranges both
work automatically:

```tg
mulimo matalikilo() {
    induluka i kuzwa 1 kusika 5 {
        amba(i)
    }

    induluka j kuzwa 5 kusika 1 {
        amba(j)
    }
}
```

There is no step syntax yet.

`cita ... kusikila` executes the body first, then stops when the condition
becomes true:

```tg
mulimo matalikilo() {
    zina x = 0

    cita {
        amba(x)
        x = x + 1
    } kusikila (x eelana 3)
}
```

`leka` exits the nearest loop and is an error outside loops.

## Functions

Declare functions with `mulimo` and return values with `pilula`:

```tg
mulimo add(a, b) {
    pilula a + b
}

mulimo matalikilo() {
    amba(add(10, 20))
}
```

`pilula` outside a function is an error. Returning from `matalikilo()` is
allowed because `matalikilo` is itself a function; the returned value is ignored.

## Native Functions

| Function | Behavior |
| --- | --- |
| `mpati(a, b)` | returns the maximum value |
| `inini(a, b)` | returns the minimum value |
| `ngamabala(x)` | returns `True` if `x` is text |
| `ninamba(x)` | returns `True` if `x` is a number |
| `namba(x)` | converts `x` to a number |
| `mabala(x)` | converts `x` to text |

Boolean output currently uses Python-style `True` and `False`.

## Errors

TongaLang errors are bilingual where possible. They include:

- Stable, searchable codes such as `TL-L103`, `TL-S101`, and `TL-R106`
- A Tonga message prefixed with `Mulubizyo`
- An English message prefixed with `Error`
- Optional beginner hints
- Line and column information when available
- The relevant source line and a caret pointing to the failing column

Example:

```text
Line 2, Column 5
Mulubizyo: TongaLang taisebenzisi semicolon ";".
Error: TongaLang does not use semicolons ";".
Langulukila: Leka kulemba semicolon kumamanino aa statement.
Hint: Remove the semicolon at the end of the statement.
```

## AST Visualization

The text AST visualizer can be used from Python:

```python
from tongalang.ast_visualizer import format_ast
from tongalang.parser import parse_source

program = parse_source('mulimo matalikilo() { amba("Hi") }')
print(format_ast(program))
```

The GUI exposes the parsed structure as both a visual node-link tree and an
accessible outline through its AST panel.

## Testing

Run the full test suite:

```powershell
python -m pytest -q
```

Launch the visual failure-discovery dashboard:

```powershell
python -m testlab --autorun
```

Run the full instrumented suite without a GUI:

```powershell
python -m testlab --headless
```

Run only adversarial weakness probes:

```powershell
python -m testlab --headless --weakness
```

The suite covers lexer, parser, interpreter, error contracts, GUI integration,
AST layout, example integrity, cancellation, hostile input, resource limits,
repeated execution, and result reporting. Each Test Lab run writes JSON, JUnit
XML, console output, and coverage data under `test-results/`. See
`docs/TESTING_AND_FAILURE_DISCOVERY.md` for the testing method and how to
interpret the metrics.

## Windows Packaging

Install dependencies first:

```powershell
pip install -r requirements.txt
```

Build the CLI runner:

```powershell
pyinstaller --onefile --name tongalang main.py
```

Build the GUI:

```powershell
pyinstaller --onefile --windowed --name TongaLangGUI gui/app.py
```

Build output is written to `dist/`. PyInstaller temporary output and `.spec`
files are ignored by default.
