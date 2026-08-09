from __future__ import annotations

from typing import Any, Optional


class TongaLangError(Exception):
    """
    Base class for TongaLang errors.

    Every user-facing error should ideally include:
    - Tonga message
    - English message
    - optional beginner hint
    - optional line and column
    """

    def __init__(
        self,
        tonga_message: str,
        english_message: str,
        hint_tonga: Optional[str] = None,
        hint_english: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        code: str = "TL000",
        category_tonga: str = "Mulubizyo wa TongaLang",
        category_english: str = "TongaLang error",
        details: Optional[dict[str, Any]] = None,
    ):
        self.tonga_message = tonga_message
        self.english_message = english_message
        self.hint_tonga = hint_tonga
        self.hint_english = hint_english
        self.line = line
        self.column = column
        self.code = code
        self.category_tonga = category_tonga
        self.category_english = category_english
        self.details = dict(details or {})

        super().__init__(self.format_message())

    def to_diagnostic(self, source: str = ""):
        """Return the structured diagnostic used by the IDE.

        The import stays local so the legacy error module remains usable by
        the lexer and parser without creating an import cycle.
        """
        from .diagnostics import diagnostic_from_error

        return diagnostic_from_error(self, source)

    def format_message(self, mode: str = "bilingual", source: str | None = None) -> str:
        """
        Format this error for display.

        The default remains bilingual so existing CLI output and tests keep
        their original behavior. GUI code can request Tonga-only diagnostics
        with mode="tonga".
        """
        parts = []

        if mode == "tonga":
            parts.append(f"[{self.code}] {self.category_tonga}")
        else:
            parts.append(f"[{self.code}] {self.category_english}")

        if self.line is not None:
            if self.column is not None:
                location = f"Line {self.line}, Column {self.column}"
            else:
                location = f"Line {self.line}"

            if mode == "tonga":
                location = f"{self.line}:{self.column}" if self.column is not None else f"{self.line}"
            parts.append(location)

        excerpt = self._source_excerpt(source)
        if excerpt:
            parts.append(excerpt)

        parts.append(f"Mulubizyo: {self.tonga_message}")

        if mode != "tonga":
            parts.append(f"Error: {self.english_message}")

        if self.hint_tonga:
            parts.append(f"Langulukila: {self.hint_tonga}")

        if mode != "tonga" and self.hint_english:
            parts.append(f"Hint: {self.hint_english}")

        return "\n".join(parts)

    def _source_excerpt(self, source: str | None) -> str:
        if source is None or self.line is None:
            return ""
        source_lines = source.splitlines()
        if not 1 <= self.line <= len(source_lines):
            return ""
        text = source_lines[self.line - 1]
        caret = " " * max(0, (self.column or 1) - 1) + "^"
        return f"{self.line:>4} | {text}\n     | {caret}"


# ============================================================
# Lexical / Syntax Errors
# ============================================================

class TongaLexicalError(TongaLangError):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("code", "TL-L001")
        kwargs.setdefault("category_tonga", "Mulubizyo wazilembo")
        kwargs.setdefault("category_english", "Lexical error")
        super().__init__(*args, **kwargs)


class TongaSyntaxError(TongaLangError):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("code", "TL-S001")
        kwargs.setdefault("category_tonga", "Mulubizyo wamubambilo")
        kwargs.setdefault("category_english", "Syntax error")
        super().__init__(*args, **kwargs)


# ============================================================
# Runtime Errors
# ============================================================

class TongaRuntimeError(TongaLangError):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("code", "TL-R001")
        kwargs.setdefault("category_tonga", "Mulubizyo wakucita")
        kwargs.setdefault("category_english", "Runtime error")
        super().__init__(*args, **kwargs)


class UndefinedVariableError(TongaRuntimeError):
    def __init__(
        self,
        name: str,
        line: int | None = None,
        column: int | None = None,
        candidates: tuple[str, ...] = (),
    ):
        super().__init__(
            tonga_message=f'Kunyina izina lya "{name}".',
            english_message=f'There is no variable named "{name}".',
            hint_tonga="Bona kuti izina lyalembwa kabotu naa kuti lyazibikidwe kusanguna.",
            hint_english="Check that the variable name is spelled correctly or declared first.",
            line=line,
            column=column,
            code="TL-R101",
            details={"name": name, "candidates": tuple(candidates)},
        )


class VariableAlreadyDeclaredError(TongaRuntimeError):
    def __init__(self, name: str, line: int | None = None, column: int | None = None):
        super().__init__(
            tonga_message=f'Izina "{name}" lyazibikidwe kale muno.',
            english_message=f'Variable "{name}" has already been declared in this scope.',
            hint_tonga="Sebenzya izina limbi naa chinja mutengo wa izina liripo.",
            hint_english="Use a different variable name or assign a new value to the existing variable.",
            line=line,
            column=column,
            code="TL-R102",
            details={"name": name},
        )


class DivisionByZeroError(TongaRuntimeError):
    def __init__(self, line: int | None = None, column: int | None = None):
        super().__init__(
            tonga_message="Tokonzya kwaabanya nchintu na zilo.",
            english_message="Cannot divide by zero.",
            hint_tonga="Bona kuti namba ili mumugabo tee zilo.",
            hint_english="Check that the divisor is not zero.",
            line=line,
            column=column,
            code="TL-R103",
        )


class TypeMismatchError(TongaRuntimeError):
    def __init__(
        self,
        operation: str,
        left_type: str,
        right_type: str,
        line: int | None = None,
        column: int | None = None,
    ):
        super().__init__(
            tonga_message=f'Tokonzya kusebenzya "{operation}" pakati ka {left_type} a {right_type}.',
            english_message=f'Cannot use "{operation}" between {left_type} and {right_type}.',
            hint_tonga="Bona kuti milimo ya namba naa mabala ilikuyelana.",
            hint_english="Check that the values are compatible for this operation.",
            line=line,
            column=column,
            code="TL-R104",
            details={"operation": operation, "left_type": left_type, "right_type": right_type},
        )


class InvalidInputUsageError(TongaRuntimeError):
    def __init__(self, line: int | None = None, column: int | None = None):
        super().__init__(
            tonga_message='Bala ifwila kubikwa mu izina, mbuli "zina x = bala()" naa "bala(x)".',
            english_message='Input from "bala" must be stored in a variable, such as "zina x = bala()" or "bala(x)".',
            hint_tonga="Bala ibala muntu, pele mutengo ufunika kubikwa aantu amwi izina.",
            hint_english="Input reads a value from the user, but that value must be stored somewhere.",
            line=line,
            column=column,
            code="TL-R105",
        )


class BreakOutsideLoopError(TongaRuntimeError):
    def __init__(self, line: int | None = None, column: int | None = None):
        super().__init__(
            tonga_message='"leka" ilakonzya kusebenzya buyo mukati kamulungu.',
            english_message='"leka" can only be used inside a loop.',
            hint_tonga='Bikka "leka" mukati ka kufumbwa, induluka, naa cita/kusikila.',
            hint_english='Place "leka" inside a while loop, for-range loop, or do-until loop.',
            line=line,
            column=column,
            code="TL-R106",
        )


class ReturnOutsideFunctionError(TongaRuntimeError):
    def __init__(self, line: int | None = None, column: int | None = None):
        super().__init__(
            tonga_message='"pilula" ilasebenzya buyo mukati kamulimo.',
            english_message='"pilula" can only be used inside a function.',
            hint_tonga='Bikka "pilula" mukati ka mulimo.',
            hint_english='Place "pilula" inside a function body.',
            line=line,
            column=column,
            code="TL-R107",
        )


class FunctionNotDefinedError(TongaRuntimeError):
    def __init__(
        self,
        name: str,
        line: int | None = None,
        column: int | None = None,
        candidates: tuple[str, ...] = (),
    ):
        super().__init__(
            tonga_message=f'Mulimo "{name}" tauzibikidwe.',
            english_message=f'Function "{name}" is not defined.',
            hint_tonga="Bona kuti mulimo walembwa kabotu naa kuti wazibikidwe.",
            hint_english="Check that the function name is spelled correctly or declared.",
            line=line,
            column=column,
            code="TL-R108",
            details={"name": name, "candidates": tuple(candidates)},
        )


class WrongArgumentCountError(TongaRuntimeError):
    def __init__(
        self,
        name: str,
        expected: int,
        received: int,
        line: int | None = None,
        column: int | None = None,
    ):
        super().__init__(
            tonga_message=f'Mulimo "{name}" ulayanda ma arguments {expected}, pele wapegwa {received}.',
            english_message=f'Function "{name}" expects {expected} argument(s), but received {received}.',
            hint_tonga="Bona bungi bwama values uutuma kumulimo.",
            hint_english="Check the number of values passed to the function.",
            line=line,
            column=column,
            code="TL-R109",
            details={"name": name, "expected": expected, "received": received},
        )


class MainFunctionMissingError(TongaRuntimeError):
    def __init__(self, suggestion: str | None = None):
        hint_tonga = 'Program ifwila kutandika mu "mulimo matalikilo() { ... }".'
        hint_english = 'Every TongaLang program must start execution from "mulimo matalikilo() { ... }".'
        if suggestion:
            hint_tonga += f' Hena "{suggestion}" wayandanga kuba "matalikilo"?'
            hint_english += f' Did you mean to name "{suggestion}" as "matalikilo"?'
        super().__init__(
            tonga_message='Kunyina mulimo wa matalikilo: "mulimo matalikilo()".',
            english_message='Missing main entry point: "mulimo matalikilo()".',
            hint_tonga=hint_tonga,
            hint_english=hint_english,
            code="TL-R110",
            details={"suggestion": suggestion},
        )


class LoopLimitExceededError(TongaRuntimeError):
    def __init__(self, limit: int, line: int | None = None, column: int | None = None):
        super().__init__(
            tonga_message=f'Mulungu waima akaambo wakupita mpimo wa {limit}.',
            english_message=f'Loop stopped after reaching the maximum iteration limit of {limit}.',
            hint_tonga="Bona kuti mulungu uli a condition iikonzya kusanduka.",
            hint_english="Check that the loop condition eventually becomes false.",
            line=line,
            column=column,
            code="TL-R111",
            details={"limit": limit},
        )


class ConversionError(TongaRuntimeError):
    def __init__(self, value: object, target: str, line: int | None = None, column: int | None = None):
        super().__init__(
            tonga_message=f'Tokonzya kusandula "{value}" kuya ku {target}.',
            english_message=f'Cannot convert "{value}" to {target}.',
            hint_tonga="Bona kuti mutengo ulingene kusandulwa.",
            hint_english="Check that the value can be converted to the requested type.",
            line=line,
            column=column,
            code="TL-R112",
            details={"value": value, "target": target},
        )


class ExecutionCancelledError(TongaRuntimeError):
    def __init__(self, line: int | None = None, column: int | None = None):
        super().__init__(
            tonga_message="Kucita kwaimikwa amuntu.",
            english_message="Program execution was stopped by the user.",
            hint_tonga="Kobweza kucita program naa wamana kubambulula code.",
            hint_english="Run the program again when you are ready.",
            line=line,
            column=column,
            code="TL-R113",
        )


class CallDepthExceededError(TongaRuntimeError):
    def __init__(self, limit: int, line: int | None = None, column: int | None = None):
        super().__init__(
            tonga_message=f"Milimo yayitana buyo kusika ampimo wa {limit}.",
            english_message=f"Function-call depth reached the safety limit of {limit}.",
            hint_tonga="Bona mulimo uliyitana lwakwe; ufwila kuba anzila yakuleka.",
            hint_english="Check recursive functions and make sure they have a reachable stopping case.",
            line=line,
            column=column,
            code="TL-R114",
            details={"limit": limit},
        )


class InvalidConfigurationError(TongaRuntimeError):
    def __init__(self, setting: str, value: object):
        super().__init__(
            tonga_message=f'Mpango ya "{setting}" ajisi mutengo utazumizidwe: {value!r}.',
            english_message=f'Configuration setting "{setting}" has an invalid value: {value!r}.',
            hint_tonga="Bikka namba mpati a zilo.",
            hint_english="Use a positive whole number.",
            code="TL-C101",
            category_tonga="Mulubizyo wampango",
            category_english="Configuration error",
            details={"setting": setting, "value": value},
        )


class SourceNotFoundError(TongaLangError):
    def __init__(self, path: object):
        super().__init__(
            tonga_message=f'Fayilo "{path}" taiyajanika.',
            english_message=f'Source file "{path}" was not found.',
            hint_tonga="Bona kuti nzila aizina lyafayilo zyalembwa kabotu.",
            hint_english="Check that the file path and file name are correct.",
            code="TL-F101",
            category_tonga="Mulubizyo wafayilo",
            category_english="Source-file error",
            details={"path": str(path)},
        )


class SourceEncodingError(TongaLangError):
    def __init__(self, path: object):
        super().__init__(
            tonga_message=f'Fayilo "{path}" taili mumubambilo wa UTF-8.',
            english_message=f'Source file "{path}" is not valid UTF-8 text.',
            hint_tonga="Sungula fayilo kuba UTF-8 kakunyina BOM, elyo kobweza.",
            hint_english="Save the file as UTF-8 text and try again.",
            code="TL-F102",
            category_tonga="Mulubizyo wafayilo",
            category_english="Source-file error",
            details={"path": str(path)},
        )


class SourceReadError(TongaLangError):
    def __init__(self, path: object, reason: str):
        super().__init__(
            tonga_message=f'Fayilo "{path}" tayibaliki.',
            english_message=f'Source file "{path}" could not be read: {reason}',
            hint_tonga="Bona nzila yafayilo, luzumizyo, akuti fayilo tiikazikkidwe.",
            hint_english="Check the path, file permissions, and whether another program has locked the file.",
            code="TL-F103",
            category_tonga="Mulubizyo wafayilo",
            category_english="Source-file error",
            details={"path": str(path), "reason": reason},
        )


class SourceWriteError(TongaLangError):
    def __init__(self, path: object, reason: str):
        super().__init__(
            tonga_message=f'Fayilo "{path}" taisungiki.',
            english_message=f'Source file "{path}" could not be saved: {reason}',
            hint_tonga="Bona nzila yafayilo, luzumizyo, akuti fayilo tiikazikkidwe.",
            hint_english="Check the folder, file permissions, and whether another program has locked the file.",
            code="TL-F104",
            category_tonga="Mulubizyo wafayilo",
            category_english="Source-file error",
            details={"path": str(path), "reason": reason},
        )
