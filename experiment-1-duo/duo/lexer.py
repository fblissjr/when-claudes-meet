"""
Duo Language — Lexer
=====================
Tokenizes Duo source code into a stream of tokens.

Built by claude_e64e05 as part of the Duo language project.

Token types:
    NUMBER, STRING, IDENTIFIER, BOOL, NONE
    PLUS, MINUS, STAR, SLASH, PERCENT
    EQ, NEQ, LT, GT, LTE, GTE
    ASSIGN, LPAREN, RPAREN, LBRACE, RBRACE, LBRACKET, RBRACKET
    COMMA, SEMICOLON
    LET, FN, IF, ELSE, WHILE, FOR, IN, RETURN, PRINT
    AND, OR, NOT
    COLLABORATE, SEND, RECEIVE
    TRUE, FALSE
    EOF
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Operators
    PLUS = auto()       # +
    MINUS = auto()      # -
    STAR = auto()       # *
    SLASH = auto()      # /
    PERCENT = auto()    # %
    EQ = auto()         # ==
    NEQ = auto()        # !=
    LT = auto()         # <
    GT = auto()         # >
    LTE = auto()        # <=
    GTE = auto()        # >=
    ASSIGN = auto()     # =

    # Delimiters
    LPAREN = auto()     # (
    RPAREN = auto()     # )
    LBRACE = auto()     # {
    RBRACE = auto()     # }
    LBRACKET = auto()   # [
    RBRACKET = auto()   # ]
    COMMA = auto()      # ,

    # Keywords
    LET = auto()
    FN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    RETURN = auto()
    PRINT = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    TRUE = auto()
    FALSE = auto()
    NONE = auto()

    # Duo-specific keywords
    COLLABORATE = auto()
    SEND = auto()
    RECEIVE = auto()

    # Special
    EOF = auto()


KEYWORDS = {
    "let": TokenType.LET,
    "fn": TokenType.FN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "return": TokenType.RETURN,
    "print": TokenType.PRINT,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "none": TokenType.NONE,
    "collaborate": TokenType.COLLABORATE,
    "send": TokenType.SEND,
    "receive": TokenType.RECEIVE,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.col})"


class LexerError(Exception):
    def __init__(self, message: str, line: int, col: int):
        self.line = line
        self.col = col
        super().__init__(f"Lexer error at L{line}:{col}: {message}")


class Lexer:
    """Tokenizer for the Duo language."""

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def peek(self) -> str:
        if self.pos >= len(self.source):
            return "\0"
        return self.source[self.pos]

    def peek_next(self) -> str:
        if self.pos + 1 >= len(self.source):
            return "\0"
        return self.source[self.pos + 1]

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.peek()
            if ch in " \t\r\n":
                self.advance()
            elif ch == "/" and self.peek_next() == "/":
                # Line comment
                while self.pos < len(self.source) and self.peek() != "\n":
                    self.advance()
            elif ch == "/" and self.peek_next() == "*":
                # Block comment
                self.advance()  # /
                self.advance()  # *
                while self.pos < len(self.source):
                    if self.peek() == "*" and self.peek_next() == "/":
                        self.advance()  # *
                        self.advance()  # /
                        break
                    self.advance()
            else:
                break

    def read_string(self) -> Token:
        quote = self.advance()  # consume opening quote
        start_line, start_col = self.line, self.col
        result = []
        while self.pos < len(self.source) and self.peek() != quote:
            ch = self.advance()
            if ch == "\\":
                esc = self.advance()
                escape_map = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "'": "'"}
                result.append(escape_map.get(esc, esc))
            else:
                result.append(ch)
        if self.pos >= len(self.source):
            raise LexerError("Unterminated string", start_line, start_col)
        self.advance()  # consume closing quote
        return Token(TokenType.STRING, "".join(result), start_line, start_col)

    def read_number(self) -> Token:
        start_line, start_col = self.line, self.col
        result = []
        has_dot = False
        while self.pos < len(self.source) and (self.peek().isdigit() or self.peek() == "."):
            if self.peek() == ".":
                if has_dot:
                    break
                has_dot = True
            result.append(self.advance())
        return Token(TokenType.NUMBER, "".join(result), start_line, start_col)

    def read_identifier(self) -> Token:
        start_line, start_col = self.line, self.col
        result = []
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == "_"):
            result.append(self.advance())
        word = "".join(result)
        token_type = KEYWORDS.get(word, TokenType.IDENTIFIER)
        return Token(token_type, word, start_line, start_col)

    def tokenize(self) -> List[Token]:
        """Tokenize the entire source and return list of tokens."""
        self.tokens = []

        while self.pos < len(self.source):
            self.skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break

            start_line, start_col = self.line, self.col
            ch = self.peek()

            # String literals
            if ch in '"\'':
                self.tokens.append(self.read_string())

            # Number literals
            elif ch.isdigit():
                self.tokens.append(self.read_number())

            # Identifiers and keywords
            elif ch.isalpha() or ch == "_":
                self.tokens.append(self.read_identifier())

            # Two-character operators
            elif ch == "=" and self.peek_next() == "=":
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.EQ, "==", start_line, start_col))
            elif ch == "!" and self.peek_next() == "=":
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.NEQ, "!=", start_line, start_col))
            elif ch == "<" and self.peek_next() == "=":
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.LTE, "<=", start_line, start_col))
            elif ch == ">" and self.peek_next() == "=":
                self.advance(); self.advance()
                self.tokens.append(Token(TokenType.GTE, ">=", start_line, start_col))

            # Single-character operators and delimiters
            elif ch == "=":
                self.advance()
                self.tokens.append(Token(TokenType.ASSIGN, "=", start_line, start_col))
            elif ch == "+":
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, "+", start_line, start_col))
            elif ch == "-":
                self.advance()
                self.tokens.append(Token(TokenType.MINUS, "-", start_line, start_col))
            elif ch == "*":
                self.advance()
                self.tokens.append(Token(TokenType.STAR, "*", start_line, start_col))
            elif ch == "/":
                self.advance()
                self.tokens.append(Token(TokenType.SLASH, "/", start_line, start_col))
            elif ch == "%":
                self.advance()
                self.tokens.append(Token(TokenType.PERCENT, "%", start_line, start_col))
            elif ch == "<":
                self.advance()
                self.tokens.append(Token(TokenType.LT, "<", start_line, start_col))
            elif ch == ">":
                self.advance()
                self.tokens.append(Token(TokenType.GT, ">", start_line, start_col))
            elif ch == "(":
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, "(", start_line, start_col))
            elif ch == ")":
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ")", start_line, start_col))
            elif ch == "{":
                self.advance()
                self.tokens.append(Token(TokenType.LBRACE, "{", start_line, start_col))
            elif ch == "}":
                self.advance()
                self.tokens.append(Token(TokenType.RBRACE, "}", start_line, start_col))
            elif ch == "[":
                self.advance()
                self.tokens.append(Token(TokenType.LBRACKET, "[", start_line, start_col))
            elif ch == "]":
                self.advance()
                self.tokens.append(Token(TokenType.RBRACKET, "]", start_line, start_col))
            elif ch == ",":
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ",", start_line, start_col))
            else:
                raise LexerError(f"Unexpected character: {ch!r}", start_line, start_col)

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return self.tokens


def tokenize(source: str) -> List[Token]:
    """Convenience function to tokenize source code."""
    return Lexer(source).tokenize()
