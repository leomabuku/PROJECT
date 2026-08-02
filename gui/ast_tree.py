from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from tongalang.ast_nodes import (
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
from tongalang.native_functions import NATIVE_FUNCTIONS


@dataclass(frozen=True)
class ASTTreeNode:
    node_id: str
    parent_id: str
    label: str
    node_type: str
    line: int | None
    column: int | None
    detail: str
    depth: int = 0


def build_ast_tree_rows(root: object) -> list[ASTTreeNode]:
    rows: list[ASTTreeNode] = []

    def visit(
        node: object,
        parent: str,
        label_hint: str | None = None,
        depth: int = 0,
    ) -> None:
        node_id = f"node-{len(rows) + 1}"
        label, detail = describe_ast_node(node, label_hint)
        line, column = source_position(node)
        rows.append(
            ASTTreeNode(
                node_id=node_id,
                parent_id=parent,
                label=label,
                node_type=type(node).__name__,
                line=line,
                column=column,
                detail=detail,
                depth=depth,
            )
        )
        for child_label, child in iter_ast_children(node):
            visit(child, node_id, child_label, depth + 1)

    visit(root, "")
    return rows


def ast_node_category(node_type: str) -> str:
    """Return a stable visual category for an AST node type."""
    if node_type == "Program":
        return "root"
    if node_type in {"FunctionDecl", "VarDecl", "Assign"}:
        return "declaration"
    if node_type in {
        "IfStmt",
        "WhileStmt",
        "ForRangeStmt",
        "DoUntilStmt",
        "BreakStmt",
        "ReturnStmt",
    }:
        return "control"
    if node_type in {"Binary", "Unary", "Call", "ExpressionStmt", "OutputStmt"}:
        return "expression"
    if node_type in {"Literal", "Variable"}:
        return "value"
    return "structure"


def iter_ast_children(node: object) -> Iterable[tuple[str, object]]:
    if isinstance(node, Program):
        for statement in node.statements:
            yield "statement", statement
    elif isinstance(node, FunctionDecl):
        yield "body", node.body
    elif isinstance(node, Block):
        for statement in node.statements:
            yield "statement", statement
    elif isinstance(node, VarDecl):
        yield "initializer", node.initializer
    elif isinstance(node, Assign):
        yield "value", node.value
    elif isinstance(node, OutputStmt) and node.expression is not None:
        yield "expression", node.expression
    elif isinstance(node, IfStmt):
        for index, (condition, block) in enumerate(node.branches):
            yield f"branch {index + 1} condition", condition
            yield f"branch {index + 1} body", block
        if node.else_branch is not None:
            yield "else body", node.else_branch
    elif isinstance(node, WhileStmt):
        yield "condition", node.condition
        yield "body", node.body
    elif isinstance(node, ForRangeStmt):
        yield "start", node.start
        yield "end", node.end
        yield "body", node.body
    elif isinstance(node, DoUntilStmt):
        yield "body", node.body
        yield "condition", node.condition
    elif isinstance(node, ReturnStmt) and node.value is not None:
        yield "value", node.value
    elif isinstance(node, ExpressionStmt):
        yield "expression", node.expression
    elif isinstance(node, Unary):
        yield "right", node.right
    elif isinstance(node, Binary):
        yield "left", node.left
        yield "right", node.right
    elif isinstance(node, Call):
        for index, argument in enumerate(node.arguments, start=1):
            yield f"argument {index}", argument


def describe_ast_node(node: object, label_hint: str | None = None) -> tuple[str, str]:
    prefix = f"{label_hint}: " if label_hint else ""

    if isinstance(node, Program):
        return "Program", "Root node for the full TongaLang source file."
    if isinstance(node, FunctionDecl):
        params = ", ".join(node.params) or "no parameters"
        return f"{prefix}FunctionDecl {node.name}", f"Declares function '{node.name}' with {params}."
    if isinstance(node, Block):
        return f"{prefix}Block", "A brace-delimited sequence of statements with its own scope rules."
    if isinstance(node, VarDecl):
        return f"{prefix}VarDecl {node.name}", f"Declares variable '{node.name}' and evaluates its initializer."
    if isinstance(node, Assign):
        return f"{prefix}Assign {node.name}", f"Assigns a new value to existing variable '{node.name}'."
    if isinstance(node, OutputStmt):
        return f"{prefix}OutputStmt amba", "Prints a value to program output."
    if isinstance(node, IfStmt):
        return f"{prefix}IfStmt kuti", "Evaluates branches in order and executes the first true branch."
    if isinstance(node, WhileStmt):
        return f"{prefix}WhileStmt kufumbwa", "Repeats while the condition remains true."
    if isinstance(node, ForRangeStmt):
        return f"{prefix}ForRangeStmt {node.iterator}", "Inclusive range loop; automatically ascends or descends."
    if isinstance(node, DoUntilStmt):
        return f"{prefix}DoUntilStmt cita/kusikila", "Executes body first, then stops when condition becomes true."
    if isinstance(node, BreakStmt):
        return f"{prefix}BreakStmt leka", "Leaves the nearest active loop."
    if isinstance(node, ReturnStmt):
        return f"{prefix}ReturnStmt pilula", "Returns a value from the current function."
    if isinstance(node, ExpressionStmt):
        return f"{prefix}ExpressionStmt", "Evaluates an expression for its side effect."
    if isinstance(node, Literal):
        return f"{prefix}Literal {node.value!r}", f"Literal value of type {type(node.value).__name__}."
    if isinstance(node, Variable):
        return f"{prefix}Variable {node.name}", f"Reads variable '{node.name}' from the environment."
    if isinstance(node, Unary):
        return f"{prefix}Unary {node.op}", f"Applies unary operator '{node.op}'."
    if isinstance(node, Binary):
        return f"{prefix}Binary {node.op}", f"Applies binary operator '{node.op}'."
    if isinstance(node, Call):
        call_kind = "Native function call" if node.callee in NATIVE_FUNCTIONS else "Function call"
        if node.callee == "bala":
            call_kind = "Input call"
        return f"{prefix}Call {node.callee}", f"{call_kind} with {len(node.arguments)} argument(s)."
    return f"{prefix}{type(node).__name__}", "AST node."


def source_position(node: Any) -> tuple[int | None, int | None]:
    location = getattr(node, "location", None)
    if location is None:
        return None, None
    line = getattr(location, "line", None)
    column = getattr(location, "column", None)
    return (line or None, column or None)
