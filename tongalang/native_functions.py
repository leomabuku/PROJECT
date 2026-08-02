from __future__ import annotations

from typing import Any, Callable

from .errors import ConversionError, WrongArgumentCountError


NativeFunction = Callable[..., Any]


def _check_arg_count(name: str, args: list[Any], expected: int) -> None:
    if len(args) != expected:
        raise WrongArgumentCountError(name=name, expected=expected, received=len(args))


def native_mpati(args: list[Any]) -> Any:
    """
    mpati(a, b)
    Returns the bigger value.
    """
    _check_arg_count("mpati", args, 2)
    return max(args[0], args[1])


def native_inini(args: list[Any]) -> Any:
    """
    inini(a, b)
    Returns the smaller value.
    """
    _check_arg_count("inini", args, 2)
    return min(args[0], args[1])


def native_ngamabala(args: list[Any]) -> bool:
    """
    ngamabala(x)
    Returns true if x is text/string.
    """
    _check_arg_count("ngamabala", args, 1)
    return isinstance(args[0], str)


def native_ninamba(args: list[Any]) -> bool:
    """
    ninamba(x)
    Returns true if x is a number.
    """
    _check_arg_count("ninamba", args, 1)

    # bool is technically a subclass of int in Python,
    # so we exclude booleans here.
    return isinstance(args[0], (int, float)) and not isinstance(args[0], bool)


def native_namba(args: list[Any]) -> int | float:
    """
    namba(x)
    Converts x to a number if possible.
    """
    _check_arg_count("namba", args, 1)

    value = args[0]

    if isinstance(value, bool):
        raise ConversionError(value=value, target="number")

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        text = value.strip()

        try:
            if "." in text:
                return float(text)
            return int(text)
        except ValueError:
            raise ConversionError(value=value, target="number")

    raise ConversionError(value=value, target="number")


def native_mabala(args: list[Any]) -> str:
    """
    mabala(x)
    Converts x to text/string.
    """
    _check_arg_count("mabala", args, 1)
    return str(args[0])


NATIVE_FUNCTIONS: dict[str, NativeFunction] = {
    "mpati": native_mpati,
    "inini": native_inini,
    "ngamabala": native_ngamabala,
    "ninamba": native_ninamba,
    "namba": native_namba,
    "mabala": native_mabala,
}