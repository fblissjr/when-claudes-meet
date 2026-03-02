"""
Duo Language — Test Suite
==========================
Comprehensive tests for both the parser (claude_e64e05) and interpreter (agent_67691).

Run with: python3 test_duo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import tokenize, TokenType
from parser import parse
from duo_ast import *


def test_lexer():
    """Test the lexer produces correct tokens."""
    print("=== LEXER TESTS ===")

    # Test basic tokens
    tokens = tokenize("let x = 42")
    types = [t.type for t in tokens]
    assert types == [TokenType.LET, TokenType.IDENTIFIER, TokenType.ASSIGN,
                     TokenType.NUMBER, TokenType.EOF], f"Basic: {types}"
    print("  [PASS] Basic tokens")

    # Test operators
    tokens = tokenize("a + b - c * d / e % f")
    ops = [t.type for t in tokens if t.type in
           (TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT)]
    assert len(ops) == 5
    print("  [PASS] Arithmetic operators")

    # Test comparison operators
    tokens = tokenize("a == b != c < d > e <= f >= g")
    ops = [t.type for t in tokens if t.type in
           (TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE)]
    assert len(ops) == 6
    print("  [PASS] Comparison operators")

    # Test string literals
    tokens = tokenize('"hello world"')
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "hello world"
    print("  [PASS] String literals")

    # Test escape sequences
    tokens = tokenize(r'"hello\nworld"')
    assert tokens[0].value == "hello\nworld"
    print("  [PASS] Escape sequences")

    # Test keywords
    tokens = tokenize("let fn if else while for in return print and or not true false none collaborate send receive")
    keyword_types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert TokenType.COLLABORATE in keyword_types
    assert TokenType.SEND in keyword_types
    assert TokenType.RECEIVE in keyword_types
    print("  [PASS] All keywords recognized")

    # Test comments
    tokens = tokenize("x // comment\ny")
    idents = [t for t in tokens if t.type == TokenType.IDENTIFIER]
    assert len(idents) == 2 and idents[0].value == "x" and idents[1].value == "y"
    print("  [PASS] Line comments")

    tokens = tokenize("x /* block */ y")
    idents = [t for t in tokens if t.type == TokenType.IDENTIFIER]
    assert len(idents) == 2
    print("  [PASS] Block comments")

    # Test float numbers
    tokens = tokenize("3.14")
    assert tokens[0].type == TokenType.NUMBER
    assert tokens[0].value == "3.14"
    print("  [PASS] Float numbers")

    print("  All lexer tests passed!\n")


def test_parser():
    """Test the parser produces correct AST nodes."""
    print("=== PARSER TESTS ===")

    # Test variable declaration
    ast = parse(tokenize("let x = 42"))
    assert len(ast.statements) == 1
    assert isinstance(ast.statements[0], Assignment)
    assert ast.statements[0].name == "x"
    assert isinstance(ast.statements[0].value, NumberLiteral)
    print("  [PASS] Variable declaration")

    # Test binary expression
    ast = parse(tokenize("print 1 + 2 * 3"))
    stmt = ast.statements[0]
    assert isinstance(stmt, PrintStatement)
    # Should be 1 + (2 * 3) due to precedence
    assert isinstance(stmt.value, BinaryOp)
    assert stmt.value.op == "+"
    assert isinstance(stmt.value.right, BinaryOp)
    assert stmt.value.right.op == "*"
    print("  [PASS] Operator precedence (+ vs *)")

    # Test function definition
    ast = parse(tokenize("fn add(a, b) { return a + b }"))
    fn = ast.statements[0]
    assert isinstance(fn, FunctionDef)
    assert fn.name == "add"
    assert fn.params == ["a", "b"]
    print("  [PASS] Function definition")

    # Test function call
    ast = parse(tokenize("print add(1, 2)"))
    stmt = ast.statements[0]
    call = stmt.value
    assert isinstance(call, FunctionCall)
    assert isinstance(call.callee, Identifier)
    assert call.callee.name == "add"
    assert len(call.args) == 2
    print("  [PASS] Function call")

    # Test if/else
    ast = parse(tokenize("if x > 0 { print x } else { print 0 }"))
    stmt = ast.statements[0]
    assert isinstance(stmt, IfStatement)
    assert len(stmt.then_body) == 1
    assert len(stmt.else_body) == 1
    print("  [PASS] If/else")

    # Test else-if chaining
    ast = parse(tokenize("if x > 0 { print 1 } else if x < 0 { print -1 } else { print 0 }"))
    stmt = ast.statements[0]
    assert isinstance(stmt, IfStatement)
    assert len(stmt.else_body) == 1
    assert isinstance(stmt.else_body[0], IfStatement)
    print("  [PASS] Else-if chaining")

    # Test while loop
    ast = parse(tokenize("while x > 0 { x = x - 1 }"))
    stmt = ast.statements[0]
    assert isinstance(stmt, WhileLoop)
    assert len(stmt.body) == 1
    assert isinstance(stmt.body[0], ReassignStatement)
    print("  [PASS] While loop")

    # Test for loop
    ast = parse(tokenize("for i in [1, 2, 3] { print i }"))
    stmt = ast.statements[0]
    assert isinstance(stmt, ForLoop)
    assert stmt.var_name == "i"
    assert isinstance(stmt.iterable, ListLiteral)
    print("  [PASS] For loop")

    # Test list literal
    ast = parse(tokenize("let arr = [1, 2, 3]"))
    stmt = ast.statements[0]
    assert isinstance(stmt.value, ListLiteral)
    assert len(stmt.value.elements) == 3
    print("  [PASS] List literal")

    # Test index expression
    ast = parse(tokenize("print arr[0]"))
    stmt = ast.statements[0]
    assert isinstance(stmt.value, IndexExpr)
    print("  [PASS] Index expression")

    # Test lambda expression
    ast = parse(tokenize("let f = fn(x) { return x * 2 }"))
    stmt = ast.statements[0]
    assert isinstance(stmt.value, FunctionExpr)
    assert stmt.value.params == ["x"]
    print("  [PASS] Lambda expression")

    # Test collaborate
    ast = parse(tokenize('collaborate { send "ch", 1 }, { let v = receive "ch" }'))
    stmt = ast.statements[0]
    assert isinstance(stmt, ExpressionStatement)
    assert isinstance(stmt.expr, CollaborateExpr)
    print("  [PASS] Collaborate expression")

    # Test send/receive
    ast = parse(tokenize('send "ch", 42'))
    stmt = ast.statements[0]
    assert isinstance(stmt.expr, SendExpr)
    print("  [PASS] Send expression")

    ast = parse(tokenize('let v = receive "ch"'))
    stmt = ast.statements[0]
    assert isinstance(stmt.value, ReceiveExpr)
    print("  [PASS] Receive expression")

    # Test unary operators
    ast = parse(tokenize("print -x"))
    stmt = ast.statements[0]
    assert isinstance(stmt.value, UnaryOp)
    assert stmt.value.op == "-"
    print("  [PASS] Unary minus")

    ast = parse(tokenize("print not true"))
    stmt = ast.statements[0]
    assert isinstance(stmt.value, UnaryOp)
    assert stmt.value.op == "not"
    print("  [PASS] Unary not")

    # Test boolean operators
    ast = parse(tokenize("print a and b or c"))
    stmt = ast.statements[0]
    # Should be (a and b) or c
    assert isinstance(stmt.value, BinaryOp)
    assert stmt.value.op == "or"
    assert isinstance(stmt.value.left, BinaryOp)
    assert stmt.value.left.op == "and"
    print("  [PASS] Boolean operator precedence (and vs or)")

    # Test nested calls
    ast = parse(tokenize("print f(g(x))"))
    stmt = ast.statements[0]
    outer = stmt.value
    assert isinstance(outer, FunctionCall)
    assert isinstance(outer.args[0], FunctionCall)
    print("  [PASS] Nested function calls")

    print("  All parser tests passed!\n")


def test_interpreter():
    """Test the interpreter (agent_67691's work). Only runs if interpreter is available."""
    print("=== INTERPRETER TESTS ===")
    try:
        from interpreter import Interpreter
    except ImportError:
        print("  [SKIP] Interpreter not yet available (waiting for agent_67691)")
        print()
        return False

    def run(code):
        """Run Duo code and capture output."""
        import io
        output = []
        tokens = tokenize(code)
        ast = parse(tokens)
        interp = Interpreter(output_fn=lambda x: output.append(str(x)))
        interp.run(ast)
        return "\n".join(output).strip()

    # Basic arithmetic
    assert run("print 2 + 3") == "5"
    print("  [PASS] Basic arithmetic")

    # Variable assignment
    assert run("let x = 10\nprint x") == "10"
    print("  [PASS] Variable assignment")

    # String concatenation
    assert run('print "hello" + " " + "world"') == "hello world"
    print("  [PASS] String concatenation")

    # Function definition and call
    assert run("fn add(a, b) { return a + b }\nprint add(3, 4)") == "7"
    print("  [PASS] Function call")

    # Recursion
    result = run("""
fn fib(n) {
    if n <= 1 { return n }
    return fib(n - 1) + fib(n - 2)
}
print fib(6)
""")
    assert result == "8"
    print("  [PASS] Recursion (fibonacci)")

    # Closures
    result = run("""
fn make_adder(n) {
    return fn(x) { return x + n }
}
let add5 = make_adder(5)
print add5(10)
""")
    assert result == "15"
    print("  [PASS] Closures")

    # While loop
    result = run("""
let sum = 0
let i = 1
while i <= 5 {
    sum = sum + i
    i = i + 1
}
print sum
""")
    assert result == "15"
    print("  [PASS] While loop")

    # Boolean logic
    assert run("print true and false") == "false"
    assert run("print true or false") == "true"
    assert run("print not true") == "false"
    print("  [PASS] Boolean logic")

    # Comparison
    assert run("print 5 > 3") == "true"
    assert run("print 5 == 5") == "true"
    assert run("print 5 != 3") == "true"
    print("  [PASS] Comparison operators")

    print("  All interpreter tests passed!\n")
    return True


def test_integration():
    """Integration test: parse and run example programs."""
    print("=== INTEGRATION TESTS ===")
    try:
        from interpreter import Interpreter
    except ImportError:
        print("  [SKIP] Interpreter not yet available")
        print()
        return

    try:
        from interpreter import Interpreter
    except ImportError:
        print("  [SKIP] Interpreter not yet available")
        print()
        return

    example_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../examples")
    for fname in sorted(os.listdir(example_dir)):
        if fname.endswith(".duo"):
            filepath = os.path.join(example_dir, fname)
            with open(filepath) as f:
                code = f.read()
            try:
                tokens = tokenize(code)
                ast = parse(tokens)
                interp = Interpreter(output_fn=lambda x: None)  # suppress output
                interp.run(ast)
                print(f"  [PASS] {fname} — runs successfully")
            except Exception as e:
                print(f"  [FAIL] {fname} — {e}")
    print()


if __name__ == "__main__":
    test_lexer()
    test_parser()
    test_integration()
    test_interpreter()
    print("Done!")
