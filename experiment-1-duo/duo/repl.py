"""
Duo Language — REPL (Read-Eval-Print Loop)
===========================================
Interactive shell for the Duo programming language.

Built by agent_67691 as part of the Duo language project.

Features:
    - Multi-line input (auto-detects unclosed braces)
    - Command history within session
    - Special commands: .help, .clear, .env, .quit
    - Persistent environment across inputs
    - Colorized output and prompt
"""

import sys
import os

# Ensure we can import from the project directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import tokenize, LexerError
from parser import parse, ParseError
from interpreter import Interpreter, DuoError, DuoFunction, BuiltinFunction


# --- ANSI colors ---

class Colors:
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls):
        for attr in ["CYAN", "GREEN", "YELLOW", "RED", "MAGENTA", "BOLD", "DIM", "RESET"]:
            setattr(cls, attr, "")


# Disable colors if not a terminal
if not sys.stdout.isatty():
    Colors.disable()


BANNER = f"""
{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════╗
║           DUO Programming Language           ║
║      Designed by two AIs, for everyone       ║
╚══════════════════════════════════════════════╝{Colors.RESET}
{Colors.DIM}Lexer & Parser by claude_e64e05
Interpreter & REPL by agent_67691{Colors.RESET}

Type {Colors.GREEN}.help{Colors.RESET} for commands, {Colors.GREEN}.quit{Colors.RESET} to exit.
"""

HELP_TEXT = f"""
{Colors.BOLD}Duo REPL Commands:{Colors.RESET}
  {Colors.GREEN}.help{Colors.RESET}         Show this help message
  {Colors.GREEN}.clear{Colors.RESET}        Clear the screen
  {Colors.GREEN}.env{Colors.RESET}          Show all variables in the current environment
  {Colors.GREEN}.reset{Colors.RESET}        Reset the interpreter (clear all state)
  {Colors.GREEN}.run <file>{Colors.RESET}   Run a .duo file
  {Colors.GREEN}.quit{Colors.RESET}         Exit the REPL

{Colors.BOLD}Language Quick Reference:{Colors.RESET}
  {Colors.YELLOW}let x = 42{Colors.RESET}                   Variable declaration
  {Colors.YELLOW}x = x + 1{Colors.RESET}                    Reassignment
  {Colors.YELLOW}fn add(a, b) {{ return a + b }}{Colors.RESET}  Function definition
  {Colors.YELLOW}print "hello"{Colors.RESET}                 Print a value
  {Colors.YELLOW}if x > 0 {{ ... }} else {{ ... }}{Colors.RESET}  Conditional
  {Colors.YELLOW}while x > 0 {{ ... }}{Colors.RESET}           While loop
  {Colors.YELLOW}for x in [1,2,3] {{ ... }}{Colors.RESET}      For loop
  {Colors.YELLOW}let f = fn(x) {{ return x * 2 }}{Colors.RESET} Lambda
  {Colors.YELLOW}collaborate {{ ... }}, {{ ... }}{Colors.RESET}   Parallel blocks
  {Colors.YELLOW}send "ch", value{Colors.RESET}               Send to channel
  {Colors.YELLOW}receive "ch"{Colors.RESET}                   Receive from channel
"""


def count_braces(text: str) -> int:
    """Count net open braces (handling strings and comments)."""
    depth = 0
    in_string = False
    string_char = None
    i = 0
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == "\\" and i + 1 < len(text):
                i += 2
                continue
            if ch == string_char:
                in_string = False
        else:
            if ch in ('"', "'"):
                in_string = True
                string_char = ch
            elif ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
                break  # rest is comment
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
        i += 1
    return depth


def repl():
    """Start the Duo REPL."""
    print(BANNER)

    interp = Interpreter()
    history = []

    while True:
        try:
            # Read input (with multi-line support)
            line = input(f"{Colors.CYAN}duo>{Colors.RESET} ")
            lines = [line]
            brace_depth = count_braces(line)

            while brace_depth > 0:
                cont = input(f"{Colors.DIM}...>{Colors.RESET} ")
                lines.append(cont)
                brace_depth += count_braces(cont)

            source = "\n".join(lines).strip()
            if not source:
                continue

            history.append(source)

            # Handle REPL commands
            if source.startswith("."):
                handle_command(source, interp)
                continue

            # Parse and execute
            try:
                tokens = tokenize(source)
                program = parse(tokens)
                result = interp.run(program)

                # Show result for expressions (not statements that already print)
                if result is not None and not source.strip().startswith("print"):
                    formatted = interp._format_value(result)
                    print(f"{Colors.DIM}=> {formatted}{Colors.RESET}")

            except LexerError as e:
                print(f"{Colors.RED}Lexer Error: {e}{Colors.RESET}")
            except ParseError as e:
                print(f"{Colors.RED}Parse Error: {e}{Colors.RESET}")
            except DuoError as e:
                print(f"{Colors.RED}Error: {e}{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}Internal Error: {type(e).__name__}: {e}{Colors.RESET}")

        except KeyboardInterrupt:
            print(f"\n{Colors.DIM}(Use .quit to exit){Colors.RESET}")
        except EOFError:
            print(f"\n{Colors.CYAN}Goodbye!{Colors.RESET}")
            break


def handle_command(source: str, interp: Interpreter):
    """Handle dot-commands."""
    cmd = source.split()[0].lower()
    args = source[len(cmd):].strip()

    if cmd == ".help":
        print(HELP_TEXT)
    elif cmd == ".clear":
        os.system("clear" if os.name != "nt" else "cls")
    elif cmd == ".env":
        show_env(interp)
    elif cmd == ".reset":
        interp.__init__()
        print(f"{Colors.GREEN}Environment reset.{Colors.RESET}")
    elif cmd == ".run":
        run_file(args, interp)
    elif cmd in (".quit", ".exit", ".q"):
        print(f"{Colors.CYAN}Goodbye!{Colors.RESET}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}Unknown command: {cmd}. Type .help for available commands.{Colors.RESET}")


def show_env(interp: Interpreter):
    """Show current environment variables."""
    env = interp.globals
    print(f"\n{Colors.BOLD}Current Environment:{Colors.RESET}")
    for name, value in sorted(env.bindings.items()):
        if isinstance(value, BuiltinFunction):
            continue  # skip builtins
        formatted = interp._format_value(value)
        type_str = interp._type_name(value)
        print(f"  {Colors.GREEN}{name}{Colors.RESET} : {Colors.DIM}{type_str}{Colors.RESET} = {formatted}")
    print()


def run_file(filepath: str, interp: Interpreter):
    """Run a .duo file."""
    if not filepath:
        print(f"{Colors.RED}Usage: .run <filepath>{Colors.RESET}")
        return
    try:
        with open(filepath) as f:
            source = f.read()
        tokens = tokenize(source)
        program = parse(tokens)
        interp.run(program)
    except FileNotFoundError:
        print(f"{Colors.RED}File not found: {filepath}{Colors.RESET}")
    except (LexerError, ParseError, DuoError) as e:
        print(f"{Colors.RED}{e}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error running file: {type(e).__name__}: {e}{Colors.RESET}")


if __name__ == "__main__":
    repl()
