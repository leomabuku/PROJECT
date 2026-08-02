from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, List


# ============================================================
# Source Location Support
# ============================================================

@dataclass
class SourceLocation:
    """
    Represents where a piece of code came from.

    This will later help us support:
    - line numbers
    - column numbers
    - error highlighting
    - AST visualization with source location
    """
    line: int = 0
    column: int = 0


# ============================================================
# Base AST Classes
# ============================================================

class ASTNode:
    """
    Base class for all AST nodes.
    """
    location: SourceLocation


class Stmt(ASTNode):
    """
    Base class for all statement nodes.
    Statements perform actions.

    Examples:
    - variable declaration
    - printing
    - loops
    - if statements
    - function declarations
    """
    pass


class Expr(ASTNode):
    """
    Base class for all expression nodes.
    Expressions produce values.

    Examples:
    - 10
    - "Hello"
    - x + y
    - mpati(4, 9)
    """
    pass


# ============================================================
# Program Root
# ============================================================

@dataclass
class Program(ASTNode):
    """
    Represents the whole parsed TongaLang program.

    The program may contain:
    - global variable declarations
    - function declarations

    Execution must start from:
        mulimo matalikilo() { ... }
    """
    statements: List[Stmt]
    location: SourceLocation = field(default_factory=SourceLocation)


# ============================================================
# Statement Nodes
# ============================================================

@dataclass
class VarDecl(Stmt):
    """
    Variable declaration.

    TongaLang:
        zina age = 20
    """
    name: str
    initializer: Expr
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class Assign(Stmt):
    """
    Variable assignment.

    TongaLang:
        age = 21
    """
    name: str
    value: Expr
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class OutputStmt(Stmt):
    """
    Output statement.

    TongaLang:
        amba("Hello")
        amba(age)
        amba()
    """
    expression: Optional[Expr]
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class InputStmt(Stmt):
    """
    Input statement.

    TongaLang:
        zina name = bala()
        zina name = bala("Enter name: ")
        bala(existingVariable)
    """
    name: Optional[str]
    prompt: Optional[Expr]
    declare: bool
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class Block(Stmt):
    """
    A block of statements inside braces.

    TongaLang:
        {
            amba("Inside block")
        }
    """
    statements: List[Stmt]
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class IfStmt(Stmt):
    """
    Conditional statement.

    TongaLang:
        kuti (age inda 18) {
            amba("Adult")
        } naaba (age eelana 18) {
            amba("Just turned adult")
        } nakunyina {
            amba("Child")
        }
    """
    branches: List[tuple[Expr, Block]]
    else_branch: Optional[Block]
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class WhileStmt(Stmt):
    """
    While loop.

    TongaLang:
        kufumbwa (x ceya 5) {
            amba(x)
            x = x + 1
        }
    """
    condition: Expr
    body: Block
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class ForRangeStmt(Stmt):
    """
    Range-based for loop.

    TongaLang:
        induluka i kuzwa 1 kusika 5 {
            amba(i)
        }

    Meaning:
        Repeat i from 1 to 5, inclusive.

    Descending ranges must also work:
        induluka i kuzwa 5 kusika 1 {
            amba(i)
        }
    """
    iterator: str
    start: Expr
    end: Expr
    body: Block
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class DoUntilStmt(Stmt):
    """
    Do-until loop.

    TongaLang:
        cita {
            amba(x)
            x = x + 1
        } kusikila (x eelana 5)

    Meaning:
        Execute body first.
        After each execution, stop if the condition is true.
    """
    body: Block
    condition: Expr
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class BreakStmt(Stmt):
    """
    Break statement.

    TongaLang:
        leka

    Valid only inside:
    - kufumbwa
    - induluka
    - cita/kusikila
    """
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class FunctionDecl(Stmt):
    """
    Function declaration.

    TongaLang:
        mulimo add(a, b) {
            pilula a + b
        }

    Main entry point:
        mulimo matalikilo() {
            amba("Program starts here")
        }
    """
    name: str
    params: List[str]
    body: Block
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class ReturnStmt(Stmt):
    """
    Return statement.

    TongaLang:
        pilula a + b

    Must support full expressions, not only identifiers.
    """
    value: Optional[Expr]
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class ExpressionStmt(Stmt):
    """
    Expression used as a statement.

    Useful for function calls such as:
        greet()
    """
    expression: Expr
    location: SourceLocation = field(default_factory=SourceLocation)


# ============================================================
# Expression Nodes
# ============================================================

@dataclass
class Literal(Expr):
    """
    Literal value.

    Examples:
        10
        20.5
        "Hello"
        iiyi
        pepe
    """
    value: Any
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class Variable(Expr):
    """
    Variable reference.

    TongaLang:
        age
    """
    name: str
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class Unary(Expr):
    """
    Unary expression.

    TongaLang:
        tee isReady
        -number
    """
    op: str
    right: Expr
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class Binary(Expr):
    """
    Binary expression.

    TongaLang:
        a + b
        age inda 18
        x aa y
    """
    left: Expr
    op: str
    right: Expr
    location: SourceLocation = field(default_factory=SourceLocation)


@dataclass
class Call(Expr):
    """
    Function call expression.

    TongaLang:
        mpati(10, 20)
        calculateSum(a, b)
    """
    callee: str
    arguments: List[Expr]
    location: SourceLocation = field(default_factory=SourceLocation)