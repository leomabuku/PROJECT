from __future__ import annotations

from typing import Iterable

from .ast_nodes import (
    Assign,
    Binary,
    Block,
    BreakStmt,
    Call,
    DoUntilStmt,
    ExpressionStmt,
    ForRangeStmt,
    FunctionDecl,
    IfStmt,
    Literal,
    OutputStmt,
    Program,
    ReturnStmt,
    Unary,
    VarDecl,
    Variable,
    WhileStmt,
)


class ASTVisualizer:
    """
    Render TongaLang AST nodes as a simple text tree.

    The visualizer is intentionally text-first so it can be used from tests,
    the CLI, and the Tkinter GUI without requiring graph libraries.
    """

    def format(self, node: object) -> str:
        lines = list(self._format_node(node, depth=0))
        return "\n".join(lines)

    def _format_node(self, node: object, depth: int) -> Iterable[str]:
        indent = "  " * depth

        if isinstance(node, Program):
            yield f"{indent}Program"
            for statement in node.statements:
                yield from self._format_node(statement, depth + 1)
            return

        if isinstance(node, FunctionDecl):
            params = ", ".join(node.params)
            yield f"{indent}FunctionDecl name={node.name} params=({params})"
            yield from self._format_node(node.body, depth + 1)
            return

        if isinstance(node, Block):
            yield f"{indent}Block"
            for statement in node.statements:
                yield from self._format_node(statement, depth + 1)
            return

        if isinstance(node, VarDecl):
            yield f"{indent}VarDecl name={node.name}"
            yield from self._label_child("initializer", node.initializer, depth + 1)
            return

        if isinstance(node, Assign):
            yield f"{indent}Assign name={node.name}"
            yield from self._label_child("value", node.value, depth + 1)
            return

        if isinstance(node, OutputStmt):
            yield f"{indent}OutputStmt"
            if node.expression is not None:
                yield from self._label_child("expression", node.expression, depth + 1)
            return

        if isinstance(node, IfStmt):
            yield f"{indent}IfStmt"
            for index, (condition, block) in enumerate(node.branches):
                label = "if" if index == 0 else "elseif"
                yield f"{indent}  Branch type={label}"
                yield from self._label_child("condition", condition, depth + 2)
                yield from self._label_child("body", block, depth + 2)
            if node.else_branch is not None:
                yield f"{indent}  Else"
                yield from self._format_node(node.else_branch, depth + 2)
            return

        if isinstance(node, WhileStmt):
            yield f"{indent}WhileStmt"
            yield from self._label_child("condition", node.condition, depth + 1)
            yield from self._label_child("body", node.body, depth + 1)
            return

        if isinstance(node, ForRangeStmt):
            yield f"{indent}ForRangeStmt iterator={node.iterator}"
            yield from self._label_child("start", node.start, depth + 1)
            yield from self._label_child("end", node.end, depth + 1)
            yield from self._label_child("body", node.body, depth + 1)
            return

        if isinstance(node, DoUntilStmt):
            yield f"{indent}DoUntilStmt"
            yield from self._label_child("body", node.body, depth + 1)
            yield from self._label_child("condition", node.condition, depth + 1)
            return

        if isinstance(node, BreakStmt):
            yield f"{indent}BreakStmt"
            return

        if isinstance(node, ReturnStmt):
            yield f"{indent}ReturnStmt"
            if node.value is not None:
                yield from self._label_child("value", node.value, depth + 1)
            return

        if isinstance(node, ExpressionStmt):
            yield f"{indent}ExpressionStmt"
            yield from self._label_child("expression", node.expression, depth + 1)
            return

        if isinstance(node, Literal):
            yield f"{indent}Literal value={node.value!r}"
            return

        if isinstance(node, Variable):
            yield f"{indent}Variable name={node.name}"
            return

        if isinstance(node, Unary):
            yield f"{indent}Unary op={node.op}"
            yield from self._label_child("right", node.right, depth + 1)
            return

        if isinstance(node, Binary):
            yield f"{indent}Binary op={node.op}"
            yield from self._label_child("left", node.left, depth + 1)
            yield from self._label_child("right", node.right, depth + 1)
            return

        if isinstance(node, Call):
            yield f"{indent}Call callee={node.callee}"
            for index, argument in enumerate(node.arguments, start=1):
                yield from self._label_child(f"argument {index}", argument, depth + 1)
            return

        yield f"{indent}{type(node).__name__}"

    def _label_child(self, label: str, node: object, depth: int) -> Iterable[str]:
        indent = "  " * depth
        yield f"{indent}{label}:"
        yield from self._format_node(node, depth + 1)


def format_ast(node: object) -> str:
    """
    Convenience wrapper used by tests, the GUI, and future CLI tooling.
    """
    return ASTVisualizer().format(node)
