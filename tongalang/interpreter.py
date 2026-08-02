from __future__ import annotations

from difflib import get_close_matches
import re
from typing import Any, Callable

from .ast_nodes import (
    Program,
    Stmt,
    Expr,
    VarDecl,
    Assign,
    OutputStmt,
    Block,
    IfStmt,
    WhileStmt,
    ForRangeStmt,
    DoUntilStmt,
    BreakStmt,
    FunctionDecl,
    ReturnStmt,
    ExpressionStmt,
    Literal,
    Variable,
    Unary,
    Binary,
    Call,
)
from .environment import Environment
from .native_functions import NATIVE_FUNCTIONS
from .errors import (
    TongaRuntimeError,
    UndefinedVariableError,
    DivisionByZeroError,
    TypeMismatchError,
    BreakOutsideLoopError,
    ReturnOutsideFunctionError,
    FunctionNotDefinedError,
    WrongArgumentCountError,
    MainFunctionMissingError,
    LoopLimitExceededError,
    ExecutionCancelledError,
    CallDepthExceededError,
    InvalidConfigurationError,
)


# ============================================================
# Internal Control Flow Signals
# ============================================================

class BreakSignal(Exception):
    """
    Internal signal used to exit loops.

    This is not shown directly to the user.
    It is how `leka` jumps out of a loop.
    """
    pass


class ReturnSignal(Exception):
    """
    Internal signal used to return from functions.

    This is not shown directly to the user.
    It carries the value returned by `pilula`.
    """

    def __init__(self, value: Any):
        self.value = value


# ============================================================
# Interpreter
# ============================================================

class Interpreter:
    """
    TongaLang execution engine.

    Responsibilities:
    - collect function declarations
    - execute global declarations
    - require and call mulimo matalikilo()
    - evaluate expressions
    - execute statements
    - manage scopes
    - execute loops
    - execute functions
    - call native functions
    """

    def __init__(
        self,
        max_loop_iterations: int = 10000,
        max_call_depth: int = 250,
        should_stop: Callable[[], bool] | None = None,
    ):
        if not isinstance(max_loop_iterations, int) or isinstance(max_loop_iterations, bool) or max_loop_iterations < 1:
            raise InvalidConfigurationError("max_loop_iterations", max_loop_iterations)
        if not isinstance(max_call_depth, int) or isinstance(max_call_depth, bool) or max_call_depth < 1:
            raise InvalidConfigurationError("max_call_depth", max_call_depth)
        self.global_env = Environment(name="global")
        self.functions: dict[str, FunctionDecl] = {}
        self.max_loop_iterations = max_loop_iterations
        self.max_call_depth = max_call_depth
        self.should_stop = should_stop or (lambda: False)

        # Runtime state flags.
        self.loop_depth = 0
        self.function_depth = 0

    # ========================================================
    # Public Entry Point
    # ========================================================

    def interpret(self, program: Program) -> None:
        """
        Execute a parsed TongaLang Program.

        Execution process:
        1. Collect all function declarations.
        2. Require mulimo matalikilo().
        3. Execute global variable declarations.
        4. Execute matalikilo() in its own local scope.
        """

        self.global_env = Environment(name="global")
        self.functions.clear()
        self.loop_depth = 0
        self.function_depth = 0
        self._ensure_not_cancelled(program)
        self._collect_functions(program)
        self._require_main_function()
        self._execute_global_declarations(program)
        self._run_main()

    # ========================================================
    # Program Setup
    # ========================================================

    def _collect_functions(self, program: Program) -> None:
        """
        Collect function declarations before execution.

        This allows functions to be called before they appear in the file.
        """

        for stmt in program.statements:
            if isinstance(stmt, FunctionDecl):
                name = stmt.name.lower()

                if name in self.functions:
                    line, column = self._line_col(stmt)
                    raise TongaRuntimeError(
                        tonga_message=f'Mulimo "{stmt.name}" wazibikidwe kale.',
                        english_message=f'Function "{stmt.name}" has already been declared.',
                        hint_tonga="Sebenzya izina limbi lyamulimo.",
                        hint_english="Use a different function name.",
                        line=line,
                        column=column,
                    )

                self.functions[name] = stmt

    def _execute_global_declarations(self, program: Program) -> None:
        """
        Execute only global variable declarations outside main.

        Confirmed project rule:
        - Variables declared outside main are global.
        - Main is required.
        - Other executable statements outside functions should not run.
        """

        for stmt in program.statements:
            if isinstance(stmt, FunctionDecl):
                continue

            if isinstance(stmt, VarDecl):
                value = self._eval(stmt.initializer, self.global_env)
                line, column = self._line_col(stmt)
                self.global_env.declare(stmt.name, value, line=line, column=column)
                continue

            line, column = self._line_col(stmt)

            if isinstance(stmt, ReturnStmt):
                raise ReturnOutsideFunctionError(line=line, column=column)

            if isinstance(stmt, BreakStmt):
                raise BreakOutsideLoopError(line=line, column=column)

            raise TongaRuntimeError(
                tonga_message="Statement iyi ili anze a matalikilo. TongaLang itandika mu mulimo matalikilo().",
                english_message="This statement is outside matalikilo. TongaLang execution starts from mulimo matalikilo().",
                hint_tonga='Bikka code iyi mukati ka "mulimo matalikilo() { ... }", naa izibikidwe njenge global variable.',
                hint_english='Place this code inside "mulimo matalikilo() { ... }", or make it a global variable declaration.',
                line=line,
                column=column,
            )

    def _require_main_function(self) -> None:
        """
        Ensure the required matalikilo entry point exists before runtime setup.
        """

        if "matalikilo" not in self.functions:
            matches = get_close_matches("matalikilo", tuple(self.functions), n=1, cutoff=0.72)
            raise MainFunctionMissingError(matches[0] if matches else None)

    def _run_main(self) -> None:
        """
        Run the required entry point:
            mulimo matalikilo() { ... }
        """

        main_func = self.functions.get("matalikilo")

        if main_func is None:
            raise MainFunctionMissingError()

        if len(main_func.params) != 0:
            line, column = self._line_col(main_func)
            raise TongaRuntimeError(
                tonga_message='"matalikilo" taifwiri kuba a ma parameters.',
                english_message='"matalikilo" must not have parameters.',
                hint_tonga='Lemba: mulimo matalikilo() { ... }',
                hint_english='Write: mulimo matalikilo() { ... }',
                line=line,
                column=column,
            )

        main_env = self.global_env.child("main")
        self.function_depth += 1

        try:
            self._exec_block(main_func.body, main_env, create_scope=False)
        except ReturnSignal:
            # Returning from main is allowed but ignored.
            pass
        finally:
            self.function_depth -= 1

    # ========================================================
    # Statement Execution
    # ========================================================

    def _exec(self, stmt: Stmt, env: Environment) -> None:
        """
        Execute one statement node.
        """

        self._ensure_not_cancelled(stmt)

        if isinstance(stmt, VarDecl):
            value = self._eval(stmt.initializer, env)
            line, column = self._line_col(stmt)
            env.declare(stmt.name, value, line=line, column=column)
            return

        if isinstance(stmt, Assign):
            value = self._eval(stmt.value, env)
            line, column = self._line_col(stmt)
            env.assign(stmt.name, value, line=line, column=column)
            return

        if isinstance(stmt, OutputStmt):
            if stmt.expression is None:
                print()
            else:
                value = self._eval(stmt.expression, env)
                print(self._to_output_string(value))
            return

        if isinstance(stmt, Block):
            self._exec_block(stmt, env, create_scope=True)
            return

        if isinstance(stmt, IfStmt):
            self._exec_if(stmt, env)
            return

        if isinstance(stmt, WhileStmt):
            self._exec_while(stmt, env)
            return

        if isinstance(stmt, ForRangeStmt):
            self._exec_for_range(stmt, env)
            return

        if isinstance(stmt, DoUntilStmt):
            self._exec_do_until(stmt, env)
            return

        if isinstance(stmt, BreakStmt):
            if self.loop_depth <= 0:
                line, column = self._line_col(stmt)
                raise BreakOutsideLoopError(line=line, column=column)

            raise BreakSignal()

        if isinstance(stmt, ReturnStmt):
            if self.function_depth <= 0:
                line, column = self._line_col(stmt)
                raise ReturnOutsideFunctionError(line=line, column=column)

            value = None if stmt.value is None else self._eval(stmt.value, env)
            raise ReturnSignal(value)

        if isinstance(stmt, ExpressionStmt):
            self._eval(stmt.expression, env)
            return

        line, column = self._line_col(stmt)
        raise TongaRuntimeError(
            tonga_message=f"Statement teizibidwe: {type(stmt).__name__}",
            english_message=f"Unknown statement type: {type(stmt).__name__}",
            line=line,
            column=column,
        )

    def _exec_block(self, block: Block, env: Environment, create_scope: bool = True) -> None:
        """
        Execute a block of statements.

        If create_scope=True:
            create a new child scope for variables declared inside the block.

        If create_scope=False:
            execute directly in the given environment.

        Main function body uses create_scope=False because main already has its own scope.
        Loop bodies use controlled custom scopes in their loop methods.
        """

        block_env = env.child("block") if create_scope else env

        for statement in block.statements:
            self._exec(statement, block_env)

    def _exec_if(self, stmt: IfStmt, env: Environment) -> None:
        """
        Execute if / else-if / else.
        """

        for condition, block in stmt.branches:
            if self._truthy(self._eval(condition, env)):
                self._exec_block(block, env, create_scope=True)
                return

        if stmt.else_branch is not None:
            self._exec_block(stmt.else_branch, env, create_scope=True)

    # ========================================================
    # Loop Execution
    # ========================================================

    def _exec_while(self, stmt: WhileStmt, env: Environment) -> None:
        """
        Execute kufumbwa loop.

        TongaLang:
            kufumbwa (x ceya 5) {
                amba(x)
                x = x + 1
            }
        """

        iterations = 0
        self.loop_depth += 1

        try:
            while self._truthy(self._eval(stmt.condition, env)):
                if iterations >= self.max_loop_iterations:
                    line, column = self._line_col(stmt)
                    raise LoopLimitExceededError(self.max_loop_iterations, line=line, column=column)

                try:
                    # Fresh loop-body scope per iteration.
                    # Variables declared inside the loop stay local to that iteration.
                    self._exec_block(stmt.body, env.child("while-loop"), create_scope=False)
                except BreakSignal:
                    break

                iterations += 1

        finally:
            self.loop_depth -= 1

    def _exec_for_range(self, stmt: ForRangeStmt, env: Environment) -> None:
        """
        Execute range-based loop.

        TongaLang:
            induluka i kuzwa 1 kusika 5 {
                amba(i)
            }

        Confirmed behavior:
        - End value is inclusive.
        - Descending ranges are supported.
        - No step syntax yet.
        """

        start_value = self._eval(stmt.start, env)
        end_value = self._eval(stmt.end, env)

        line, column = self._line_col(stmt)

        if not self._is_number(start_value) or not self._is_number(end_value):
            raise TongaRuntimeError(
                tonga_message="Induluka iyanda matalikilo a mamanino aali manamba.",
                english_message="For-range loop requires numeric start and end values.",
                hint_tonga="Bona kuti kuzwa na kusika zili manamba.",
                hint_english="Check that the start and end values are numbers.",
                line=line,
                column=column,
            )

        if not float(start_value).is_integer() or not float(end_value).is_integer():
            raise TongaRuntimeError(
                tonga_message="Induluka ya range iyanda manamba aakazima.",
                english_message="For-range loop requires whole numbers.",
                hint_tonga="Sebenzya manamba mbuli 1, 2, 3.",
                hint_english="Use whole numbers such as 1, 2, 3.",
                line=line,
                column=column,
            )

        start = int(start_value)
        end = int(end_value)

        direction = 1 if start <= end else -1
        current = start
        iterations = 0

        self.loop_depth += 1

        try:
            while True:
                if direction == 1 and current > end:
                    break

                if direction == -1 and current < end:
                    break

                if iterations >= self.max_loop_iterations:
                    raise LoopLimitExceededError(self.max_loop_iterations, line=line, column=column)

                # Each iteration gets a fresh loop-local scope.
                loop_env = env.child("for-range-loop")
                loop_env.declare(stmt.iterator, current, line=line, column=column)

                try:
                    self._exec_block(stmt.body, loop_env, create_scope=False)
                except BreakSignal:
                    break

                current += direction
                iterations += 1

        finally:
            self.loop_depth -= 1

    def _exec_do_until(self, stmt: DoUntilStmt, env: Environment) -> None:
        """
        Execute do-until loop.

        TongaLang:
            cita {
                amba(y)
                y = y + 1
            } kusikila (y eelana 5)

        Meaning:
            Execute body first.
            Then stop when condition becomes true.
        """

        iterations = 0
        self.loop_depth += 1

        try:
            while True:
                if iterations >= self.max_loop_iterations:
                    line, column = self._line_col(stmt)
                    raise LoopLimitExceededError(self.max_loop_iterations, line=line, column=column)

                try:
                    self._exec_block(stmt.body, env.child("do-until-loop"), create_scope=False)
                except BreakSignal:
                    break

                iterations += 1

                if self._truthy(self._eval(stmt.condition, env)):
                    break

        finally:
            self.loop_depth -= 1

    # ========================================================
    # Expression Evaluation
    # ========================================================

    def _eval(self, expr: Expr, env: Environment) -> Any:
        """
        Evaluate an expression and return its value.
        """

        self._ensure_not_cancelled(expr)

        if isinstance(expr, Literal):
            if isinstance(expr.value, str):
                return self._interpolate(expr.value, env)
            return expr.value

        if isinstance(expr, Variable):
            line, column = self._line_col(expr)
            return env.get(expr.name, line=line, column=column)

        if isinstance(expr, Unary):
            return self._eval_unary(expr, env)

        if isinstance(expr, Binary):
            return self._eval_binary(expr, env)

        if isinstance(expr, Call):
            return self._eval_call(expr, env)

        line, column = self._line_col(expr)
        raise TongaRuntimeError(
            tonga_message=f"Expression teizibidwe: {type(expr).__name__}",
            english_message=f"Unknown expression type: {type(expr).__name__}",
            line=line,
            column=column,
        )

    def _eval_unary(self, expr: Unary, env: Environment) -> Any:
        right = self._eval(expr.right, env)

        if expr.op in ("tee", "!"):
            return not self._truthy(right)

        if expr.op == "-":
            if self._is_number(right):
                return -right

            line, column = self._line_col(expr)
            raise TongaRuntimeError(
                tonga_message='Minus ya kumbali imwi isebenza buyo kuma namba.',
                english_message='Unary minus only works on numbers.',
                hint_tonga="Bona kuti mutengo uli namba.",
                hint_english="Check that the value is a number.",
                line=line,
                column=column,
            )

        line, column = self._line_col(expr)
        raise TongaRuntimeError(
            tonga_message=f'Unary operator "{expr.op}" teizibidwe.',
            english_message=f'Unknown unary operator "{expr.op}".',
            line=line,
            column=column,
        )

    def _eval_binary(self, expr: Binary, env: Environment) -> Any:
        left = self._eval(expr.left, env)
        right = self._eval(expr.right, env)

        op = expr.op
        line, column = self._line_col(expr)

        # ---------------- Arithmetic ----------------

        if op == "+":
            if self._is_number(left) and self._is_number(right):
                return left + right

            # Beginner-friendly string concatenation.
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)

            raise TypeMismatchError("+", self._type_name(left), self._type_name(right), line=line, column=column)

        if op == "-":
            self._require_numbers(op, left, right, line, column)
            return left - right

        if op == "*":
            self._require_numbers(op, left, right, line, column)
            return left * right

        if op == "/":
            self._require_numbers(op, left, right, line, column)

            if right == 0:
                raise DivisionByZeroError(line=line, column=column)

            return left / right

        if op == "%":
            self._require_numbers(op, left, right, line, column)

            if right == 0:
                raise DivisionByZeroError(line=line, column=column)

            return left % right

        # ---------------- Comparisons ----------------

        if op in (">", "inda"):
            self._require_numbers(op, left, right, line, column)
            return left > right

        if op in ("<", "ceya"):
            self._require_numbers(op, left, right, line, column)
            return left < right

        if op == ">=":
            self._require_numbers(op, left, right, line, column)
            return left >= right

        if op == "<=":
            self._require_numbers(op, left, right, line, column)
            return left <= right

        if op in ("==", "eelana"):
            return left == right

        if op == "!=":
            return left != right

        # ---------------- Logic ----------------

        if op in ("aa", "&&"):
            return self._truthy(left) and self._truthy(right)

        if op in ("naa", "||"):
            return self._truthy(left) or self._truthy(right)

        raise TongaRuntimeError(
            tonga_message=f'Binary operator "{op}" teizibidwe.',
            english_message=f'Unknown binary operator "{op}".',
            line=line,
            column=column,
        )

    def _eval_call(self, expr: Call, env: Environment) -> Any:
        """
        Evaluate function calls.

        Supports:
        - bala()
        - bala("Prompt")
        - native functions
        - user-defined functions
        """

        name = expr.callee.lower()
        args = [self._eval(arg, env) for arg in expr.arguments]

        # Built-in input function.
        if name == "bala":
            return self._call_bala(args, expr)

        # Native standard library functions.
        if name in NATIVE_FUNCTIONS:
            try:
                return NATIVE_FUNCTIONS[name](args)
            except TongaRuntimeError:
                raise
            except TypeError:
                line, column = self._line_col(expr)
                raise TongaRuntimeError(
                    tonga_message=f'Mulimo wa "{name}" wafilwa kusebenzya ma arguments aya.',
                    english_message=f'Native function "{name}" could not process these arguments.',
                    hint_tonga="Bona kuti watuma ma values aalingene.",
                    hint_english="Check that you passed compatible values.",
                    line=line,
                    column=column,
                )

        # User-defined function.
        if name in self.functions:
            return self._call_user_function(name, args, expr)

        line, column = self._line_col(expr)
        raise FunctionNotDefinedError(name, line=line, column=column)

    # ========================================================
    # Function Calls
    # ========================================================

    def _call_user_function(self, name: str, args: list[Any], call_expr: Call) -> Any:
        func = self.functions[name]
        line, column = self._line_col(call_expr)

        if len(args) != len(func.params):
            raise WrongArgumentCountError(
                name=name,
                expected=len(func.params),
                received=len(args),
                line=line,
                column=column,
            )

        if self.function_depth >= self.max_call_depth:
            raise CallDepthExceededError(self.max_call_depth, line=line, column=column)

        call_env = self.global_env.child(f"function:{name}")

        for param_name, value in zip(func.params, args):
            call_env.declare(param_name, value, line=line, column=column)

        self.function_depth += 1

        try:
            self._exec_block(func.body, call_env, create_scope=False)
        except ReturnSignal as signal:
            return signal.value
        finally:
            self.function_depth -= 1

        # If no pilula is used, function returns nothing.
        return None

    def _call_bala(self, args: list[Any], expr: Call) -> Any:
        """
        bala()
        bala("Prompt")

        Confirmed behavior:
        - Auto-convert numeric input where possible.
        - Text stays as text.
        """

        line, column = self._line_col(expr)

        if len(args) > 1:
            raise WrongArgumentCountError(
                name="bala",
                expected=1,
                received=len(args),
                line=line,
                column=column,
            )

        if len(args) == 1:
            print(self._to_output_string(args[0]), end="", flush=True)

        user_input = input()

        return self._auto_convert_input(user_input)

    # ========================================================
    # Helpers
    # ========================================================

    def _auto_convert_input(self, text: str) -> Any:
        """
        Convert input automatically:
        - "20" becomes int 20
        - "20.5" becomes float 20.5
        - anything else remains string
        """

        stripped = text.strip()

        if stripped == "":
            return ""

        try:
            if "." in stripped:
                return float(stripped)
            return int(stripped)
        except ValueError:
            return text

    def _truthy(self, value: Any) -> bool:
        """
        TongaLang truthiness.

        For now, use Python-like truthiness:
        - false / pepe -> False
        - 0 -> False
        - "" -> False
        - everything else -> True
        """
        return bool(value)

    def _to_output_string(self, value: Any) -> str:
        """
        Convert a value to output text.

        Confirmed option:
        - Boolean output uses Python style: True / False.
        """
        return str(value)

    def _interpolate(self, text: str, env: Environment) -> str:
        """
        String interpolation.

        Supports:
            "Hello $name"
            "Hello ${name}"
        """

        pattern = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")

        def replace(match):
            name = match.group(1) or match.group(2)
            value = env.get(name)
            return self._to_output_string(value)

        return pattern.sub(replace, text)

    def _is_number(self, value: Any) -> bool:
        """
        True for int/float, false for bool.

        Python treats bool as a subclass of int, so we exclude it.
        """
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _require_numbers(
        self,
        op: str,
        left: Any,
        right: Any,
        line: int | None,
        column: int | None,
    ) -> None:
        """
        Ensure both operands are numbers.
        """
        if not self._is_number(left) or not self._is_number(right):
            raise TypeMismatchError(
                operation=op,
                left_type=self._type_name(left),
                right_type=self._type_name(right),
                line=line,
                column=column,
            )

    def _type_name(self, value: Any) -> str:
        if isinstance(value, bool):
            return "boolean"

        if isinstance(value, int):
            return "number"

        if isinstance(value, float):
            return "number"

        if isinstance(value, str):
            return "text"

        if value is None:
            return "nothing"

        return type(value).__name__

    def _line_col(self, node: Any) -> tuple[int | None, int | None]:
        """
        Extract line and column from an AST node.
        """
        location = getattr(node, "location", None)

        if location is None:
            return None, None

        line = getattr(location, "line", None)
        column = getattr(location, "column", None)

        if line == 0:
            line = None

        if column == 0:
            column = None

        return line, column

    def _ensure_not_cancelled(self, node: Any = None) -> None:
        if not self.should_stop():
            return
        line, column = self._line_col(node)
        raise ExecutionCancelledError(line=line, column=column)
