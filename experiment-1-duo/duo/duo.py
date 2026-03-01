#!/usr/bin/env python3
"""
Duo Language — CLI Runner
==========================
The main entry point for running Duo programs.

Usage:
    python3 duo.py <file.duo>          Run a Duo program
    python3 duo.py --repl              Start the interactive REPL
    python3 duo.py --parse <file.duo>  Print the AST (debug mode)
    python3 duo.py --tokens <file.duo> Print the token stream (debug mode)
    python3 duo.py --test              Run the test suite

Built by claude_e64e05 as the CLI integration layer.
"""

import sys
import os

# Ensure project directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import tokenize
from parser import parse


def print_ast(node, indent=0):
    """Pretty-print an AST node."""
    prefix = "  " * indent
    name = type(node).__name__
    attrs = {k: v for k, v in vars(node).items()
             if k not in ('line', 'col') and not isinstance(v, list)}
    list_attrs = {k: v for k, v in vars(node).items()
                  if isinstance(v, list)}

    # Print non-list attributes
    simple = ", ".join(f"{k}={v!r}" for k, v in attrs.items()
                       if not hasattr(v, '__dataclass_fields__'))
    complex_attrs = [(k, v) for k, v in attrs.items()
                     if hasattr(v, '__dataclass_fields__')]

    print(f"{prefix}{name}({simple})")
    for k, v in complex_attrs:
        print(f"{prefix}  {k}:")
        print_ast(v, indent + 2)
    for k, items in list_attrs.items():
        if items:
            print(f"{prefix}  {k}:")
            for item in items:
                if hasattr(item, '__dataclass_fields__'):
                    print_ast(item, indent + 2)
                else:
                    print(f"{prefix}    {item!r}")


def main():
    if len(sys.argv) < 2:
        # Default to REPL if no arguments
        from repl import repl
        repl()
        return

    arg = sys.argv[1]

    if arg == "--test":
        import test_duo
        test_duo.test_lexer()
        test_duo.test_parser()
        test_duo.test_integration()
        test_duo.test_interpreter()
        return

    if arg == "--tokens":
        if len(sys.argv) < 3:
            print("Error: --tokens requires a file argument", file=sys.stderr)
            sys.exit(1)
        with open(sys.argv[2]) as f:
            source = f.read()
        tokens = tokenize(source)
        for tok in tokens:
            print(tok)
        return

    if arg == "--parse":
        if len(sys.argv) < 3:
            print("Error: --parse requires a file argument", file=sys.stderr)
            sys.exit(1)
        with open(sys.argv[2]) as f:
            source = f.read()
        tokens = tokenize(source)
        ast = parse(tokens)
        print_ast(ast)
        return

    if arg == "--repl":
        from repl import repl
        repl()
        return

    # Run a file
    filepath = arg
    if not os.path.isfile(filepath):
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath) as f:
        source = f.read()

    try:
        tokens = tokenize(source)
        ast = parse(tokens)
    except Exception as e:
        print(f"Syntax error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        from interpreter import Interpreter
        interp = Interpreter()
        interp.run(ast)
    except Exception as e:
        print(f"Runtime error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
