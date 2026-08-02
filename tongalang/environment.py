from __future__ import annotations

from typing import Any, Optional

from .errors import UndefinedVariableError, VariableAlreadyDeclaredError


class Environment:
    """
    Runtime environment / symbol table.

    It stores variables and supports nested scopes.

    Example:
        global scope
            main scope
                loop scope
    """

    def __init__(self, parent: Optional["Environment"] = None, name: str = "scope"):
        self.parent = parent
        self.name = name
        self.values: dict[str, Any] = {}

    def declare(self, name: str, value: Any, line: int | None = None, column: int | None = None) -> None:
        """
        Declare a new variable in the current scope only.
        """
        key = name.lower()

        if key in self.values:
            raise VariableAlreadyDeclaredError(name, line=line, column=column)

        self.values[key] = value

    def assign(self, name: str, value: Any, line: int | None = None, column: int | None = None) -> None:
        """
        Assign to an existing variable.

        Search starts from the current scope and moves upward.
        """
        key = name.lower()

        if key in self.values:
            self.values[key] = value
            return

        if self.parent is not None:
            self.parent.assign(name, value, line=line, column=column)
            return

        raise UndefinedVariableError(name, line=line, column=column)

    def get(self, name: str, line: int | None = None, column: int | None = None) -> Any:
        """
        Get a variable value.

        Search starts from the current scope and moves upward.
        """
        key = name.lower()

        if key in self.values:
            return self.values[key]

        if self.parent is not None:
            return self.parent.get(name, line=line, column=column)

        raise UndefinedVariableError(name, line=line, column=column)

    def exists_in_current_scope(self, name: str) -> bool:
        """
        Check whether a variable exists in the current scope only.
        """
        return name.lower() in self.values

    def child(self, name: str = "child") -> "Environment":
        """
        Create a child scope.
        """
        return Environment(parent=self, name=name)

    def snapshot(self) -> dict[str, Any]:
        """
        Return visible variables from parent scopes to current scope.

        Useful for debugging and GUI environment display.
        """
        data = {}

        if self.parent is not None:
            data.update(self.parent.snapshot())

        data.update(self.values)
        return data

    def __repr__(self) -> str:
        return f"Environment(name={self.name!r}, values={self.values!r})"