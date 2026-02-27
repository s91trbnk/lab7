from __future__ import annotations

import ast
import math
import operator
import sys
from dataclasses import dataclass
from typing import Any, Callable


class CalculatorError(Exception):
    pass


_BIN_OPS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_FUNCS: dict[str, Callable[..., float]] = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,  # log(x) or log(x, base)
    "log10": math.log10,
    "ln": math.log,  # alias
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
}

_CONSTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def _as_number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    raise CalculatorError(f"Expected a number, got {type(value).__name__}")


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise CalculatorError("Only numbers are allowed")

    if isinstance(node, ast.Name):
        if node.id in _CONSTS:
            return float(_CONSTS[node.id])
        raise CalculatorError(f"Unknown name: {node.id!r}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BIN_OPS:
            raise CalculatorError(f"Operator not allowed: {op_type.__name__}")
        left = _eval(node.left)
        right = _eval(node.right)
        try:
            return float(_BIN_OPS[op_type](left, right))
        except ZeroDivisionError as e:
            raise CalculatorError("Division by zero") from e

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise CalculatorError(f"Unary operator not allowed: {op_type.__name__}")
        return float(_UNARY_OPS[op_type](_eval(node.operand)))

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise CalculatorError("Only simple function calls are allowed, e.g. sqrt(9)")
        name = node.func.id
        if name not in _FUNCS:
            raise CalculatorError(f"Unknown function: {name!r}")
        if node.keywords:
            raise CalculatorError("Keyword arguments are not supported")
        args = [_as_number(_eval(arg)) for arg in node.args]
        try:
            return float(_FUNCS[name](*args))
        except ValueError as e:
            raise CalculatorError(str(e)) from e
        except TypeError as e:
            raise CalculatorError(f"Bad arguments for {name}()") from e

    raise CalculatorError(f"Expression not supported: {type(node).__name__}")


def evaluate(expr: str) -> float:
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise CalculatorError("Invalid expression") from e
    return _eval(tree)


@dataclass
class ReplState:
    last: float | None = None


def repl() -> int:
    state = ReplState()
    print("Python Calculator (safe)")
    print("Examples: 2+3*4, (1+2)**3, sqrt(9), sin(pi/2)")
    print("Constants: pi, e, tau")
    print("Commands: :q (quit), :h (help), :c (clear last)")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not line:
            continue
        if line in {":q", "q", "quit", "exit"}:
            return 0
        if line in {":h", "help", "?"}:
            print("Enter a math expression.")
            print("Allowed: + - * / % ** ( ) and functions like sqrt(x), log(x, base).")
            print("Use '_' to refer to the previous result.")
            continue
        if line in {":c", "clear"}:
            state.last = None
            print("Cleared.")
            continue

        expr = line.replace("_", str(state.last) if state.last is not None else "0")
        try:
            value = evaluate(expr)
        except CalculatorError as e:
            print(f"Error: {e}")
            continue

        state.last = value
        if value.is_integer():
            print(int(value))
        else:
            print(value)


def main(argv: list[str]) -> int:
    if len(argv) <= 1:
        return repl()
    expr = " ".join(argv[1:])
    try:
        value = evaluate(expr)
    except CalculatorError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    if value.is_integer():
        print(int(value))
    else:
        print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
