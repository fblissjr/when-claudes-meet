"""
Duo Language — Interpreter
===========================
Tree-walking interpreter that evaluates AST nodes.

Built by agent_67691 as part of the Duo language project.

Features:
    - Lexical scoping with closure support
    - First-class functions
    - Collaborate blocks with channel-based message passing
    - Built-in standard library functions
    - Clean error reporting with line/col info
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from duo_ast import (
    ASTNode, Program,
    NumberLiteral, StringLiteral, BoolLiteral, NoneLiteral, ListLiteral,
    Identifier, BinaryOp, UnaryOp,
    FunctionCall, FunctionExpr, IndexExpr,
    CollaborateExpr, SendExpr, ReceiveExpr,
    Assignment, ReassignStatement, IfStatement, WhileLoop, ForLoop,
    ReturnStatement, PrintStatement, ExpressionStatement, FunctionDef,
)


# --- Exceptions for control flow ---

class DuoError(Exception):
    """Runtime error in Duo."""
    def __init__(self, message: str, node: ASTNode = None):
        loc = f" at L{node.line}:{node.col}" if node and node.line else ""
        super().__init__(f"Runtime error{loc}: {message}")


class ReturnSignal(Exception):
    """Used to unwind the stack on 'return'."""
    def __init__(self, value: Any):
        self.value = value


# --- Environment (lexical scoping) ---

class Environment:
    """Chained scope environment supporting closures."""

    def __init__(self, parent: Optional['Environment'] = None):
        self.bindings: Dict[str, Any] = {}
        self.parent = parent

    def define(self, name: str, value: Any):
        self.bindings[name] = value

    def get(self, name: str, node: ASTNode = None) -> Any:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name, node)
        raise DuoError(f"Undefined variable '{name}'", node)

    def set(self, name: str, value: Any, node: ASTNode = None):
        """Reassign an existing variable (walks up scope chain)."""
        if name in self.bindings:
            self.bindings[name] = value
            return
        if self.parent:
            self.parent.set(name, value, node)
            return
        raise DuoError(f"Cannot reassign undefined variable '{name}'", node)


# --- Function values ---

class DuoFunction:
    """A callable function value (closure)."""

    def __init__(self, params: List[str], body: List[ASTNode],
                 closure_env: Environment, name: str = "<anonymous>"):
        self.params = params
        self.body = body
        self.closure_env = closure_env
        self.name = name

    def __repr__(self):
        return f"<fn {self.name}({', '.join(self.params)})>"


class BuiltinFunction:
    """A built-in function implemented in Python."""

    def __init__(self, name: str, func):
        self.name = name
        self.func = func

    def __repr__(self):
        return f"<builtin {self.name}>"


# --- Channel system for collaborate/send/receive ---

class ChannelStore:
    """Message channels for communicate between collaborate blocks."""

    def __init__(self):
        self.channels: Dict[str, list] = defaultdict(list)

    def send(self, channel: str, value: Any):
        self.channels[channel].append(value)

    def receive(self, channel: str) -> Any:
        if self.channels[channel]:
            return self.channels[channel].pop(0)
        return None

    def clear(self):
        self.channels.clear()


# --- The Interpreter ---

class Interpreter:
    """Tree-walking interpreter for the Duo language."""

    def __init__(self, output_fn=None):
        self.globals = Environment()
        self.channels = ChannelStore()
        self.output_fn = output_fn or print
        self._install_builtins()

    def _install_builtins(self):
        """Register standard library functions."""
        builtins = {
            "len": self._builtin_len,
            "range": self._builtin_range,
            "type": self._builtin_type,
            "str": self._builtin_str,
            "num": self._builtin_num,
            "int": self._builtin_int,
            "append": self._builtin_append,
            "push": self._builtin_push,
            "pop": self._builtin_pop,
            "input": self._builtin_input,
            "abs": self._builtin_abs,
            "min": self._builtin_min,
            "max": self._builtin_max,
            "floor": self._builtin_floor,
            "ceil": self._builtin_ceil,
            "keys": self._builtin_keys,
            "slice": self._builtin_slice,
            "join": self._builtin_join,
            "split": self._builtin_split,
            "contains": self._builtin_contains,
        }
        for name, func in builtins.items():
            self.globals.define(name, BuiltinFunction(name, func))

    # --- Public API ---

    def run(self, program: Program) -> Any:
        """Execute a full program."""
        return self._exec_block(program.statements, self.globals)

    def eval_source(self, source: str) -> Any:
        """Parse and run source code. Convenience for REPL."""
        from lexer import tokenize
        from parser import parse
        tokens = tokenize(source)
        program = parse(tokens)
        return self.run(program)

    # --- Statement execution ---

    def _exec_block(self, statements: List[ASTNode], env: Environment) -> Any:
        result = None
        for stmt in statements:
            result = self._exec(stmt, env)
        return result

    def _exec(self, node: ASTNode, env: Environment) -> Any:
        """Execute a statement or evaluate an expression."""
        # Statements
        if isinstance(node, Assignment):
            return self._exec_assignment(node, env)
        if isinstance(node, ReassignStatement):
            return self._exec_reassign(node, env)
        if isinstance(node, FunctionDef):
            return self._exec_funcdef(node, env)
        if isinstance(node, IfStatement):
            return self._exec_if(node, env)
        if isinstance(node, WhileLoop):
            return self._exec_while(node, env)
        if isinstance(node, ForLoop):
            return self._exec_for(node, env)
        if isinstance(node, ReturnStatement):
            return self._exec_return(node, env)
        if isinstance(node, PrintStatement):
            return self._exec_print(node, env)
        if isinstance(node, ExpressionStatement):
            return self._eval(node.expr, env)

        # Expressions (can also appear at top level)
        return self._eval(node, env)

    # --- Statement handlers ---

    def _exec_assignment(self, node: Assignment, env: Environment):
        value = self._eval(node.value, env)
        env.define(node.name, value)
        return value

    def _exec_reassign(self, node: ReassignStatement, env: Environment):
        value = self._eval(node.value, env)
        target = node.target

        if isinstance(target, Identifier):
            env.set(target.name, value, node)
        elif isinstance(target, IndexExpr):
            obj = self._eval(target.obj, env)
            idx = self._eval(target.index, env)
            if not isinstance(obj, list):
                raise DuoError("Can only index-assign into lists", node)
            idx = int(idx)
            if idx < 0 or idx >= len(obj):
                raise DuoError(f"Index {idx} out of bounds (list length {len(obj)})", node)
            obj[idx] = value
        else:
            raise DuoError("Invalid assignment target", node)
        return value

    def _exec_funcdef(self, node: FunctionDef, env: Environment):
        func = DuoFunction(node.params, node.body, env, name=node.name)
        env.define(node.name, func)
        return func

    def _exec_if(self, node: IfStatement, env: Environment):
        condition = self._eval(node.condition, env)
        if self._truthy(condition):
            return self._exec_block(node.then_body, Environment(env))
        elif node.else_body:
            return self._exec_block(node.else_body, Environment(env))
        return None

    def _exec_while(self, node: WhileLoop, env: Environment):
        result = None
        iterations = 0
        max_iterations = 1_000_000
        while self._truthy(self._eval(node.condition, env)):
            result = self._exec_block(node.body, Environment(env))
            iterations += 1
            if iterations > max_iterations:
                raise DuoError(f"While loop exceeded {max_iterations} iterations (infinite loop?)", node)
        return result

    def _exec_for(self, node: ForLoop, env: Environment):
        iterable = self._eval(node.iterable, env)
        if not isinstance(iterable, list):
            raise DuoError("for-in requires a list", node)
        result = None
        for item in iterable:
            loop_env = Environment(env)
            loop_env.define(node.var_name, item)
            result = self._exec_block(node.body, loop_env)
        return result

    def _exec_return(self, node: ReturnStatement, env: Environment):
        value = self._eval(node.value, env) if node.value else None
        raise ReturnSignal(value)

    def _exec_print(self, node: PrintStatement, env: Environment):
        value = self._eval(node.value, env)
        self.output_fn(self._format_value(value))
        return value

    # --- Expression evaluation ---

    def _eval(self, node: ASTNode, env: Environment) -> Any:
        if isinstance(node, NumberLiteral):
            return node.value
        if isinstance(node, StringLiteral):
            return node.value
        if isinstance(node, BoolLiteral):
            return node.value
        if isinstance(node, NoneLiteral):
            return None
        if isinstance(node, ListLiteral):
            return [self._eval(e, env) for e in node.elements]
        if isinstance(node, Identifier):
            return env.get(node.name, node)
        if isinstance(node, BinaryOp):
            return self._eval_binary(node, env)
        if isinstance(node, UnaryOp):
            return self._eval_unary(node, env)
        if isinstance(node, FunctionCall):
            return self._eval_call(node, env)
        if isinstance(node, FunctionExpr):
            return DuoFunction(node.params, node.body, env)
        if isinstance(node, IndexExpr):
            return self._eval_index(node, env)
        if isinstance(node, CollaborateExpr):
            return self._eval_collaborate(node, env)
        if isinstance(node, SendExpr):
            return self._eval_send(node, env)
        if isinstance(node, ReceiveExpr):
            return self._eval_receive(node, env)

        # Statement nodes that can appear in expression position
        if isinstance(node, (Assignment, ReassignStatement, FunctionDef,
                             IfStatement, WhileLoop, ForLoop,
                             ReturnStatement, PrintStatement, ExpressionStatement)):
            return self._exec(node, env)

        raise DuoError(f"Unknown AST node: {type(node).__name__}", node)

    def _eval_binary(self, node: BinaryOp, env: Environment) -> Any:
        # Short-circuit for logical operators
        if node.op == "and":
            left = self._eval(node.left, env)
            return left if not self._truthy(left) else self._eval(node.right, env)
        if node.op == "or":
            left = self._eval(node.left, env)
            return left if self._truthy(left) else self._eval(node.right, env)

        left = self._eval(node.left, env)
        right = self._eval(node.right, env)

        # String concatenation
        if node.op == "+" and isinstance(left, str):
            return left + self._to_str(right)
        if node.op == "+" and isinstance(right, str):
            return self._to_str(left) + right

        # List concatenation
        if node.op == "+" and isinstance(left, list) and isinstance(right, list):
            return left + right

        # String repetition
        if node.op == "*" and isinstance(left, str) and isinstance(right, (int, float)):
            return left * int(right)
        if node.op == "*" and isinstance(right, str) and isinstance(left, (int, float)):
            return right * int(left)

        # Arithmetic
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            ops = {
                "+": lambda a, b: a + b,
                "-": lambda a, b: a - b,
                "*": lambda a, b: a * b,
                "/": lambda a, b: self._safe_div(a, b, node),
                "%": lambda a, b: a % b if b != 0 else self._div_zero(node),
            }
            if node.op in ops:
                return ops[node.op](left, right)

        # Comparison (works on numbers and strings)
        comp_ops = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
        }
        if node.op in comp_ops:
            try:
                return comp_ops[node.op](left, right)
            except TypeError:
                if node.op == "==":
                    return False
                if node.op == "!=":
                    return True
                raise DuoError(f"Cannot compare {type(left).__name__} and {type(right).__name__} with '{node.op}'", node)

        raise DuoError(f"Unsupported operation: {self._type_name(left)} {node.op} {self._type_name(right)}", node)

    def _eval_unary(self, node: UnaryOp, env: Environment) -> Any:
        operand = self._eval(node.operand, env)
        if node.op == "-":
            if isinstance(operand, (int, float)):
                return -operand
            raise DuoError(f"Cannot negate {self._type_name(operand)}", node)
        if node.op == "not":
            return not self._truthy(operand)
        raise DuoError(f"Unknown unary operator: {node.op}", node)

    def _eval_call(self, node: FunctionCall, env: Environment) -> Any:
        callee = self._eval(node.callee, env)
        args = [self._eval(a, env) for a in node.args]

        if isinstance(callee, BuiltinFunction):
            try:
                return callee.func(args, node)
            except DuoError:
                raise
            except Exception as e:
                raise DuoError(f"Error in builtin '{callee.name}': {e}", node)

        if isinstance(callee, DuoFunction):
            if len(args) != len(callee.params):
                raise DuoError(
                    f"Function '{callee.name}' expects {len(callee.params)} args, got {len(args)}",
                    node
                )
            # Create new scope chained to the closure environment
            call_env = Environment(callee.closure_env)
            for param, arg in zip(callee.params, args):
                call_env.define(param, arg)
            try:
                self._exec_block(callee.body, call_env)
                return None  # No explicit return
            except ReturnSignal as ret:
                return ret.value

        raise DuoError(f"Cannot call {self._type_name(callee)} — not a function", node)

    def _eval_index(self, node: IndexExpr, env: Environment) -> Any:
        obj = self._eval(node.obj, env)
        idx = self._eval(node.index, env)
        if isinstance(obj, list):
            idx = int(idx)
            if idx < 0 or idx >= len(obj):
                raise DuoError(f"Index {idx} out of bounds (list length {len(obj)})", node)
            return obj[idx]
        if isinstance(obj, str):
            idx = int(idx)
            if idx < 0 or idx >= len(obj):
                raise DuoError(f"Index {idx} out of bounds (string length {len(obj)})", node)
            return obj[idx]
        raise DuoError(f"Cannot index into {self._type_name(obj)}", node)

    def _eval_collaborate(self, node: CollaborateExpr, env: Environment) -> Any:
        """Execute two blocks with shared channels.

        In our tree-walking interpreter, we run them sequentially
        (left first, then right) with a shared channel store.
        The left block typically sends; the right block receives.
        """
        self.channels.clear()
        left_env = Environment(env)
        right_env = Environment(env)

        # Run left block (producer)
        left_result = None
        try:
            left_result = self._exec_block(node.left, left_env)
        except ReturnSignal as ret:
            left_result = ret.value

        # Run right block (consumer)
        right_result = None
        try:
            right_result = self._exec_block(node.right, right_env)
        except ReturnSignal as ret:
            right_result = ret.value

        return [left_result, right_result]

    def _eval_send(self, node: SendExpr, env: Environment) -> Any:
        channel = self._eval(node.channel, env)
        value = self._eval(node.value, env)
        if not isinstance(channel, str):
            raise DuoError("Channel name must be a string", node)
        self.channels.send(channel, value)
        return value

    def _eval_receive(self, node: ReceiveExpr, env: Environment) -> Any:
        channel = self._eval(node.channel, env)
        if not isinstance(channel, str):
            raise DuoError("Channel name must be a string", node)
        return self.channels.receive(channel)

    # --- Helpers ---

    def _truthy(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, list):
            return len(value) > 0
        return True

    def _safe_div(self, a, b, node):
        if b == 0:
            raise DuoError("Division by zero", node)
        result = a / b
        if isinstance(a, float) or isinstance(b, float):
            return result
        return result if result != int(result) else int(result)

    def _div_zero(self, node):
        raise DuoError("Division by zero", node)

    def _format_value(self, value: Any) -> str:
        """Format a value for print output."""
        if value is None:
            return "none"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, float):
            return str(int(value)) if value == int(value) else str(value)
        if isinstance(value, list):
            return "[" + ", ".join(self._format_value(v) for v in value) + "]"
        if isinstance(value, (DuoFunction, BuiltinFunction)):
            return repr(value)
        return str(value)

    def _to_str(self, value: Any) -> str:
        return self._format_value(value)

    def _type_name(self, value: Any) -> str:
        if value is None:
            return "none"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, (int, float)):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, (DuoFunction, BuiltinFunction)):
            return "function"
        return type(value).__name__

    # --- Built-in functions ---

    def _builtin_len(self, args, node):
        self._check_arity("len", args, 1, node)
        val = args[0]
        if isinstance(val, (list, str)):
            return float(len(val))
        raise DuoError(f"len() expects list or string, got {self._type_name(val)}", node)

    def _builtin_range(self, args, node):
        if len(args) == 1:
            return [float(i) for i in range(int(args[0]))]
        elif len(args) == 2:
            return [float(i) for i in range(int(args[0]), int(args[1]))]
        elif len(args) == 3:
            return [float(i) for i in range(int(args[0]), int(args[1]), int(args[2]))]
        raise DuoError("range() takes 1-3 arguments", node)

    def _builtin_type(self, args, node):
        self._check_arity("type", args, 1, node)
        return self._type_name(args[0])

    def _builtin_str(self, args, node):
        self._check_arity("str", args, 1, node)
        return self._format_value(args[0])

    def _builtin_num(self, args, node):
        self._check_arity("num", args, 1, node)
        try:
            return float(args[0])
        except (ValueError, TypeError):
            raise DuoError(f"Cannot convert {self._format_value(args[0])} to number", node)

    def _builtin_int(self, args, node):
        self._check_arity("int", args, 1, node)
        try:
            return float(int(float(args[0])))
        except (ValueError, TypeError):
            raise DuoError(f"Cannot convert {self._format_value(args[0])} to integer", node)

    def _builtin_append(self, args, node):
        self._check_arity("append", args, 2, node)
        if not isinstance(args[0], list):
            raise DuoError("append() first arg must be a list", node)
        return args[0] + [args[1]]

    def _builtin_push(self, args, node):
        self._check_arity("push", args, 2, node)
        if not isinstance(args[0], list):
            raise DuoError("push() first arg must be a list", node)
        args[0].append(args[1])
        return args[0]

    def _builtin_pop(self, args, node):
        self._check_arity("pop", args, 1, node)
        if not isinstance(args[0], list):
            raise DuoError("pop() expects a list", node)
        if len(args[0]) == 0:
            raise DuoError("pop() on empty list", node)
        return args[0].pop()

    def _builtin_input(self, args, node):
        prompt = self._format_value(args[0]) if args else ""
        return input(prompt)

    def _builtin_abs(self, args, node):
        self._check_arity("abs", args, 1, node)
        if not isinstance(args[0], (int, float)):
            raise DuoError("abs() expects a number", node)
        return abs(args[0])

    def _builtin_min(self, args, node):
        if len(args) == 1 and isinstance(args[0], list):
            if not args[0]:
                raise DuoError("min() on empty list", node)
            return min(args[0])
        if len(args) >= 2:
            return min(args)
        raise DuoError("min() takes a list or 2+ arguments", node)

    def _builtin_max(self, args, node):
        if len(args) == 1 and isinstance(args[0], list):
            if not args[0]:
                raise DuoError("max() on empty list", node)
            return max(args[0])
        if len(args) >= 2:
            return max(args)
        raise DuoError("max() takes a list or 2+ arguments", node)

    def _builtin_floor(self, args, node):
        self._check_arity("floor", args, 1, node)
        import math
        return float(math.floor(args[0]))

    def _builtin_ceil(self, args, node):
        self._check_arity("ceil", args, 1, node)
        import math
        return float(math.ceil(args[0]))

    def _builtin_keys(self, args, node):
        self._check_arity("keys", args, 1, node)
        raise DuoError("keys() requires a map (not yet implemented)", node)

    def _builtin_slice(self, args, node):
        if len(args) < 2 or len(args) > 3:
            raise DuoError("slice() takes 2-3 arguments (list, start, [end])", node)
        lst = args[0]
        start = int(args[1])
        end = int(args[2]) if len(args) == 3 else len(lst)
        if isinstance(lst, (list, str)):
            return lst[start:end]
        raise DuoError("slice() expects list or string", node)

    def _builtin_join(self, args, node):
        self._check_arity("join", args, 2, node)
        sep = args[0]
        lst = args[1]
        if not isinstance(sep, str) or not isinstance(lst, list):
            raise DuoError("join(separator, list) — separator must be string, second arg must be list", node)
        return sep.join(self._format_value(v) for v in lst)

    def _builtin_split(self, args, node):
        self._check_arity("split", args, 2, node)
        s = args[0]
        sep = args[1]
        if not isinstance(s, str) or not isinstance(sep, str):
            raise DuoError("split(string, separator) — both must be strings", node)
        return s.split(sep)

    def _builtin_contains(self, args, node):
        self._check_arity("contains", args, 2, node)
        collection = args[0]
        item = args[1]
        if isinstance(collection, list):
            return item in collection
        if isinstance(collection, str):
            return str(item) in collection
        raise DuoError("contains() expects list or string as first arg", node)

    def _check_arity(self, name: str, args: list, expected: int, node):
        if len(args) != expected:
            raise DuoError(f"{name}() takes {expected} argument(s), got {len(args)}", node)
