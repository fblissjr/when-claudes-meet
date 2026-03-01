"""
Duo Language — Parser
======================
Recursive descent parser that transforms a token stream into an AST.

Built by claude_e64e05 as part of the Duo language project.

Grammar (informal):
    program     → statement*
    statement   → let_stmt | fn_def | if_stmt | while_stmt | for_stmt
                | return_stmt | print_stmt | collaborate_stmt
                | send_stmt | expr_stmt
    let_stmt    → "let" IDENT "=" expression
    fn_def      → "fn" IDENT "(" params ")" block
    if_stmt     → "if" expression block ("else" (if_stmt | block))?
    while_stmt  → "while" expression block
    for_stmt    → "for" IDENT "in" expression block
    return_stmt → "return" expression?
    print_stmt  → "print" expression
    send_stmt   → "send" expression "," expression
    expr_stmt   → expression | assignment

    expression  → or_expr
    or_expr     → and_expr ("or" and_expr)*
    and_expr    → equality ("and" equality)*
    equality    → comparison (("==" | "!=") comparison)*
    comparison  → addition (("<" | ">" | "<=" | ">=") addition)*
    addition    → multiply (("+" | "-") multiply)*
    multiply    → unary (("*" | "/" | "%") unary)*
    unary       → ("-" | "not") unary | call
    call        → primary ("(" args ")" | "[" expression "]")*
    primary     → NUMBER | STRING | BOOL | NONE | IDENT
                | "(" expression ")"
                | "[" (expression ("," expression)*)? "]"
                | "fn" "(" params ")" block
                | "receive" expression
                | "collaborate" block "," block
"""

from typing import List, Optional

from duo_ast import (
    ASTNode, Program,
    NumberLiteral, StringLiteral, BoolLiteral, NoneLiteral, ListLiteral,
    Identifier, BinaryOp, UnaryOp,
    FunctionCall, FunctionExpr, IndexExpr,
    CollaborateExpr, SendExpr, ReceiveExpr,
    Assignment, ReassignStatement, IfStatement, WhileLoop, ForLoop,
    ReturnStatement, PrintStatement, ExpressionStatement, FunctionDef,
)
from lexer import Token, TokenType, LexerError


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        self.token = token
        super().__init__(f"Parse error at L{token.line}:{token.col}: {message} (got {token.type.name} {token.value!r})")


class Parser:
    """Recursive descent parser for the Duo language."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # --- Token navigation ---

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if not self.at_end():
            self.pos += 1
        return tok

    def check(self, *types: TokenType) -> bool:
        return self.peek().type in types

    def match(self, *types: TokenType) -> Optional[Token]:
        if self.peek().type in types:
            return self.advance()
        return None

    def expect(self, token_type: TokenType, message: str = "") -> Token:
        if self.peek().type == token_type:
            return self.advance()
        msg = message or f"Expected {token_type.name}"
        raise ParseError(msg, self.peek())

    # --- Parsing entry point ---

    def parse(self) -> Program:
        stmts = []
        while not self.at_end():
            stmts.append(self.parse_statement())
        return Program(statements=stmts, line=1, col=1)

    # --- Statements ---

    def parse_statement(self) -> ASTNode:
        tok = self.peek()

        if tok.type == TokenType.LET:
            return self.parse_let()
        elif tok.type == TokenType.FN and self._is_fn_def():
            return self.parse_fn_def()
        elif tok.type == TokenType.IF:
            return self.parse_if()
        elif tok.type == TokenType.WHILE:
            return self.parse_while()
        elif tok.type == TokenType.FOR:
            return self.parse_for()
        elif tok.type == TokenType.RETURN:
            return self.parse_return()
        elif tok.type == TokenType.PRINT:
            return self.parse_print()
        elif tok.type == TokenType.SEND:
            return self.parse_send_stmt()
        elif tok.type == TokenType.COLLABORATE:
            return self.parse_collaborate_stmt()
        else:
            return self.parse_expr_or_assign()

    def _is_fn_def(self) -> bool:
        """Look ahead to distinguish 'fn name(...)' from 'fn(...)' (lambda)."""
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1].type == TokenType.IDENTIFIER
        return False

    def parse_let(self) -> Assignment:
        tok = self.advance()  # consume 'let'
        name_tok = self.expect(TokenType.IDENTIFIER, "Expected variable name after 'let'")
        self.expect(TokenType.ASSIGN, "Expected '=' after variable name")
        value = self.parse_expression()
        return Assignment(name=name_tok.value, value=value, line=tok.line, col=tok.col)

    def parse_fn_def(self) -> FunctionDef:
        tok = self.advance()  # consume 'fn'
        name_tok = self.expect(TokenType.IDENTIFIER, "Expected function name")
        params = self.parse_params()
        body = self.parse_block()
        return FunctionDef(name=name_tok.value, params=params, body=body,
                           line=tok.line, col=tok.col)

    def parse_if(self) -> IfStatement:
        tok = self.advance()  # consume 'if'
        condition = self.parse_expression()
        then_body = self.parse_block()
        else_body = []
        if self.match(TokenType.ELSE):
            if self.check(TokenType.IF):
                # else if → nest as single-element else body
                else_body = [self.parse_if()]
            else:
                else_body = self.parse_block()
        return IfStatement(condition=condition, then_body=then_body,
                           else_body=else_body, line=tok.line, col=tok.col)

    def parse_while(self) -> WhileLoop:
        tok = self.advance()  # consume 'while'
        condition = self.parse_expression()
        body = self.parse_block()
        return WhileLoop(condition=condition, body=body, line=tok.line, col=tok.col)

    def parse_for(self) -> ForLoop:
        tok = self.advance()  # consume 'for'
        var_tok = self.expect(TokenType.IDENTIFIER, "Expected variable name after 'for'")
        self.expect(TokenType.IN, "Expected 'in' after for variable")
        iterable = self.parse_expression()
        body = self.parse_block()
        return ForLoop(var_name=var_tok.value, iterable=iterable, body=body,
                       line=tok.line, col=tok.col)

    def parse_return(self) -> ReturnStatement:
        tok = self.advance()  # consume 'return'
        value = None
        if not self.check(TokenType.RBRACE) and not self.at_end():
            # Only skip if it's clearly a statement keyword (not an expression)
            # Note: 'fn' without a name is a lambda expression, so only skip
            # if it's 'fn IDENT' (a named function definition)
            is_fn_def = self.check(TokenType.FN) and self._is_fn_def()
            if not self.check(TokenType.LET, TokenType.IF,
                              TokenType.WHILE, TokenType.FOR, TokenType.RETURN,
                              TokenType.PRINT) and not is_fn_def:
                value = self.parse_expression()
        return ReturnStatement(value=value, line=tok.line, col=tok.col)

    def parse_print(self) -> PrintStatement:
        tok = self.advance()  # consume 'print'
        value = self.parse_expression()
        return PrintStatement(value=value, line=tok.line, col=tok.col)

    def parse_send_stmt(self) -> ExpressionStatement:
        expr = self.parse_send_expr()
        return ExpressionStatement(expr=expr, line=expr.line, col=expr.col)

    def parse_send_expr(self) -> SendExpr:
        tok = self.advance()  # consume 'send'
        channel = self.parse_expression()
        self.expect(TokenType.COMMA, "Expected ',' after channel in send")
        value = self.parse_expression()
        return SendExpr(channel=channel, value=value, line=tok.line, col=tok.col)

    def parse_collaborate_stmt(self) -> ExpressionStatement:
        expr = self.parse_collaborate_expr()
        return ExpressionStatement(expr=expr, line=expr.line, col=expr.col)

    def parse_collaborate_expr(self) -> CollaborateExpr:
        tok = self.advance()  # consume 'collaborate'
        left = self.parse_block()
        self.expect(TokenType.COMMA, "Expected ',' between collaborate blocks")
        right = self.parse_block()
        return CollaborateExpr(left=left, right=right, line=tok.line, col=tok.col)

    def parse_expr_or_assign(self) -> ASTNode:
        """Parse an expression, and check if it's followed by '=' for reassignment."""
        expr = self.parse_expression()
        if self.match(TokenType.ASSIGN):
            value = self.parse_expression()
            return ReassignStatement(target=expr, value=value,
                                     line=expr.line, col=expr.col)
        return ExpressionStatement(expr=expr, line=expr.line, col=expr.col)

    # --- Helpers ---

    def parse_block(self) -> List[ASTNode]:
        """Parse { statement* }"""
        self.expect(TokenType.LBRACE, "Expected '{'")
        stmts = []
        while not self.check(TokenType.RBRACE) and not self.at_end():
            stmts.append(self.parse_statement())
        self.expect(TokenType.RBRACE, "Expected '}'")
        return stmts

    def parse_params(self) -> List[str]:
        """Parse (param1, param2, ...)"""
        self.expect(TokenType.LPAREN, "Expected '('")
        params = []
        if not self.check(TokenType.RPAREN):
            params.append(self.expect(TokenType.IDENTIFIER, "Expected parameter name").value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENTIFIER, "Expected parameter name").value)
        self.expect(TokenType.RPAREN, "Expected ')'")
        return params

    def parse_args(self) -> List[ASTNode]:
        """Parse (arg1, arg2, ...)"""
        args = []
        if not self.check(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                args.append(self.parse_expression())
        return args

    # --- Expressions (precedence climbing) ---

    def parse_expression(self) -> ASTNode:
        return self.parse_or()

    def parse_or(self) -> ASTNode:
        left = self.parse_and()
        while self.match(TokenType.OR):
            right = self.parse_and()
            left = BinaryOp(op="or", left=left, right=right,
                            line=left.line, col=left.col)
        return left

    def parse_and(self) -> ASTNode:
        left = self.parse_equality()
        while self.match(TokenType.AND):
            right = self.parse_equality()
            left = BinaryOp(op="and", left=left, right=right,
                            line=left.line, col=left.col)
        return left

    def parse_equality(self) -> ASTNode:
        left = self.parse_comparison()
        while tok := self.match(TokenType.EQ, TokenType.NEQ):
            right = self.parse_comparison()
            left = BinaryOp(op=tok.value, left=left, right=right,
                            line=left.line, col=left.col)
        return left

    def parse_comparison(self) -> ASTNode:
        left = self.parse_addition()
        while tok := self.match(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            right = self.parse_addition()
            left = BinaryOp(op=tok.value, left=left, right=right,
                            line=left.line, col=left.col)
        return left

    def parse_addition(self) -> ASTNode:
        left = self.parse_multiply()
        while tok := self.match(TokenType.PLUS, TokenType.MINUS):
            right = self.parse_multiply()
            left = BinaryOp(op=tok.value, left=left, right=right,
                            line=left.line, col=left.col)
        return left

    def parse_multiply(self) -> ASTNode:
        left = self.parse_unary()
        while tok := self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            right = self.parse_unary()
            left = BinaryOp(op=tok.value, left=left, right=right,
                            line=left.line, col=left.col)
        return left

    def parse_unary(self) -> ASTNode:
        if tok := self.match(TokenType.MINUS):
            operand = self.parse_unary()
            return UnaryOp(op="-", operand=operand, line=tok.line, col=tok.col)
        if tok := self.match(TokenType.NOT):
            operand = self.parse_unary()
            return UnaryOp(op="not", operand=operand, line=tok.line, col=tok.col)
        return self.parse_call()

    def parse_call(self) -> ASTNode:
        expr = self.parse_primary()
        while True:
            if self.match(TokenType.LPAREN):
                args = self.parse_args()
                self.expect(TokenType.RPAREN, "Expected ')' after arguments")
                expr = FunctionCall(callee=expr, args=args,
                                    line=expr.line, col=expr.col)
            elif self.match(TokenType.LBRACKET):
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET, "Expected ']' after index")
                expr = IndexExpr(obj=expr, index=index,
                                 line=expr.line, col=expr.col)
            else:
                break
        return expr

    def parse_primary(self) -> ASTNode:
        tok = self.peek()

        if tok.type == TokenType.NUMBER:
            self.advance()
            val = float(tok.value) if "." in tok.value else int(tok.value)
            # Store as float always for consistency
            return NumberLiteral(value=float(val), line=tok.line, col=tok.col)

        if tok.type == TokenType.STRING:
            self.advance()
            return StringLiteral(value=tok.value, line=tok.line, col=tok.col)

        if tok.type == TokenType.TRUE:
            self.advance()
            return BoolLiteral(value=True, line=tok.line, col=tok.col)

        if tok.type == TokenType.FALSE:
            self.advance()
            return BoolLiteral(value=False, line=tok.line, col=tok.col)

        if tok.type == TokenType.NONE:
            self.advance()
            return NoneLiteral(line=tok.line, col=tok.col)

        if tok.type == TokenType.IDENTIFIER:
            self.advance()
            return Identifier(name=tok.value, line=tok.line, col=tok.col)

        if tok.type == TokenType.LPAREN:
            self.advance()  # consume '('
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')'")
            return expr

        if tok.type == TokenType.LBRACKET:
            return self.parse_list_literal()

        if tok.type == TokenType.FN:
            return self.parse_fn_expr()

        if tok.type == TokenType.RECEIVE:
            self.advance()
            channel = self.parse_expression()
            return ReceiveExpr(channel=channel, line=tok.line, col=tok.col)

        if tok.type == TokenType.COLLABORATE:
            return self.parse_collaborate_expr()

        raise ParseError(f"Unexpected token", tok)

    def parse_list_literal(self) -> ListLiteral:
        tok = self.advance()  # consume '['
        elements = []
        if not self.check(TokenType.RBRACKET):
            elements.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                if self.check(TokenType.RBRACKET):
                    break  # trailing comma OK
                elements.append(self.parse_expression())
        self.expect(TokenType.RBRACKET, "Expected ']'")
        return ListLiteral(elements=elements, line=tok.line, col=tok.col)

    def parse_fn_expr(self) -> FunctionExpr:
        tok = self.advance()  # consume 'fn'
        params = self.parse_params()
        body = self.parse_block()
        return FunctionExpr(params=params, body=body, line=tok.line, col=tok.col)


def parse(tokens: List[Token]) -> Program:
    """Convenience function to parse a token list into an AST."""
    return Parser(tokens).parse()
