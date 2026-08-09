from __future__ import annotations

from pathlib import Path
from typing import Optional

from .parser import parse_source
from .interpreter import Interpreter
from .errors import SourceEncodingError, SourceNotFoundError, SourceReadError, TongaLangError


def run_source(
    source: str,
    *,
    max_loop_iterations: int = 10000,
    max_call_depth: int = 250,
) -> None:
    """
    Run TongaLang source code from a string.

    Pipeline:
        source text
        -> parser
        -> AST
        -> interpreter
        -> output
    """
    program = parse_source(source)
    interpreter = Interpreter(
        max_loop_iterations=max_loop_iterations,
        max_call_depth=max_call_depth,
    )
    interpreter.interpret(program)


def run_file(
    file_path: str | Path,
    *,
    max_loop_iterations: int = 10000,
    max_call_depth: int = 250,
) -> None:
    """
    Run a TongaLang source file.

    Example:
        python main.py examples/01_mazyina.tg
    """
    path = Path(file_path)

    if not path.exists():
        raise SourceNotFoundError(path)

    if not path.is_file():
        raise SourceNotFoundError(path)

    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise SourceEncodingError(path) from error
    except OSError as error:
        raise SourceReadError(path, str(error)) from error
    run_source(
        source,
        max_loop_iterations=max_loop_iterations,
        max_call_depth=max_call_depth,
    )


def safe_run_source(
    source: str,
    *,
    max_loop_iterations: int = 10000,
    max_call_depth: int = 250,
) -> bool:
    """
    Run source code safely.

    Returns:
        True  -> program ran successfully
        False -> program failed with an error

    This is useful for:
    - CLI
    - GUI runner
    - future debug tools
    """
    try:
        run_source(
            source,
            max_loop_iterations=max_loop_iterations,
            max_call_depth=max_call_depth,
        )
        return True

    except TongaLangError as error:
        print(error.format_message(source=source))
        return False

    except Exception as error:
        print("Mulubizyo: Kwaba mulubizyo uutazibidwe.")
        print(f"Error: Unexpected internal error: {error}")
        return False


def safe_run_file(
    file_path: str | Path,
    *,
    max_loop_iterations: int = 10000,
    max_call_depth: int = 250,
) -> bool:
    """
    Run a TongaLang file safely.

    Returns:
        True  -> file ran successfully
        False -> file failed with an error
    """
    try:
        run_file(
            file_path,
            max_loop_iterations=max_loop_iterations,
            max_call_depth=max_call_depth,
        )
        return True

    except TongaLangError as error:
        print(error.format_message())
        return False

    except Exception as error:
        print("Mulubizyo: Kwaba mulubizyo uutazibidwe.")
        print(f"Error: Unexpected internal error: {error}")
        return False
