"""
Duo Language — AST Node Definitions
====================================
The shared interface contract between Parser (claude_e64e05) and Interpreter (agent_67691).

Duo is a small programming language designed collaboratively by two AI agents.
It features first-class functions, message passing, and a 'collaborate' keyword
that runs two expressions conceptually in parallel.

Syntax overview:
    let x = 42
    let greet = fn(name) { return "hello " + name }
    print greet("world")
    if x > 10 { print "big" } else { print "small" }
    while x > 0 { let x = x - 1 }
    collaborate { expr1 }, { expr2 }
    send "channel", value
    let val = receive "channel"
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union


# --- Base ---

@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0
    col: int = 0


# --- Literals ---

@dataclass
class NumberLiteral(ASTNode):
    value: float = 0.0

@dataclass
class StringLiteral(ASTNode):
    value: str = ""

@dataclass
class BoolLiteral(ASTNode):
    value: bool = False

@dataclass
class NoneLiteral(ASTNode):
    """Represents the 'none' value."""
    pass

@dataclass
class ListLiteral(ASTNode):
    elements: List[ASTNode] = field(default_factory=list)


# --- Expressions ---

@dataclass
class Identifier(ASTNode):
    name: str = ""

@dataclass
class BinaryOp(ASTNode):
    """Binary operation: left op right

    op is one of: +, -, *, /, %, ==, !=, <, >, <=, >=, and, or
    """
    op: str = ""
    left: ASTNode = field(default_factory=ASTNode)
    right: ASTNode = field(default_factory=ASTNode)

@dataclass
class UnaryOp(ASTNode):
    """Unary operation: op operand

    op is one of: -, not
    """
    op: str = ""
    operand: ASTNode = field(default_factory=ASTNode)

@dataclass
class FunctionCall(ASTNode):
    callee: ASTNode = field(default_factory=ASTNode)
    args: List[ASTNode] = field(default_factory=list)

@dataclass
class IndexExpr(ASTNode):
    """Index into a list: obj[index]"""
    obj: ASTNode = field(default_factory=ASTNode)
    index: ASTNode = field(default_factory=ASTNode)

@dataclass
class FunctionExpr(ASTNode):
    """Anonymous function expression: fn(params) { body }"""
    params: List[str] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)


# --- Duo-specific expressions ---

@dataclass
class CollaborateExpr(ASTNode):
    """collaborate { expr1 }, { expr2 }

    Conceptually runs both branches and returns a pair [result1, result2].
    """
    left: List[ASTNode] = field(default_factory=list)
    right: List[ASTNode] = field(default_factory=list)

@dataclass
class SendExpr(ASTNode):
    """send channel, value — sends a value to a named channel."""
    channel: ASTNode = field(default_factory=ASTNode)
    value: ASTNode = field(default_factory=ASTNode)

@dataclass
class ReceiveExpr(ASTNode):
    """receive channel — receives a value from a named channel."""
    channel: ASTNode = field(default_factory=ASTNode)


# --- Statements ---

@dataclass
class Assignment(ASTNode):
    """let name = value"""
    name: str = ""
    value: ASTNode = field(default_factory=ASTNode)

@dataclass
class ReassignStatement(ASTNode):
    """name = value (reassignment, no let)"""
    target: ASTNode = field(default_factory=ASTNode)
    value: ASTNode = field(default_factory=ASTNode)

@dataclass
class IfStatement(ASTNode):
    """if condition { then_body } else { else_body }"""
    condition: ASTNode = field(default_factory=ASTNode)
    then_body: List[ASTNode] = field(default_factory=list)
    else_body: List[ASTNode] = field(default_factory=list)

@dataclass
class WhileLoop(ASTNode):
    """while condition { body }"""
    condition: ASTNode = field(default_factory=ASTNode)
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class ForLoop(ASTNode):
    """for var in iterable { body }"""
    var_name: str = ""
    iterable: ASTNode = field(default_factory=ASTNode)
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class ReturnStatement(ASTNode):
    value: Optional[ASTNode] = None

@dataclass
class PrintStatement(ASTNode):
    value: ASTNode = field(default_factory=ASTNode)

@dataclass
class ExpressionStatement(ASTNode):
    """A bare expression used as a statement (e.g., a function call)."""
    expr: ASTNode = field(default_factory=ASTNode)


# --- Program ---

@dataclass
class Program(ASTNode):
    """The root node: a list of top-level statements."""
    statements: List[ASTNode] = field(default_factory=list)


# --- Named function sugar ---

@dataclass
class FunctionDef(ASTNode):
    """fn name(params) { body } — sugar for let name = fn(params) { body }"""
    name: str = ""
    params: List[str] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)
