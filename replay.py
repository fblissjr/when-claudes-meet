#!/usr/bin/env python3
"""
Animated replay of the When Claudes Meet experiments.
Run: python3 replay.py
Record: asciinema rec --command "python3 replay.py --fast" replay.cast
"""
import sys
import time
import shutil

# ── Speed control ──────────────────────────────────────────────
FAST = "--fast" in sys.argv
GIF  = "--gif"  in sys.argv  # moderate speed for recording
SPEED = 0.15 if FAST else (0.55 if GIF else 1.0)
def pause(seconds):
    time.sleep(seconds * SPEED)

def type_out(text, delay=0.02):
    """Print text character by character."""
    d = delay * SPEED
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        if ch == '\n':
            time.sleep(d * 3)
        elif ch in '.!?':
            time.sleep(d * 5)
        else:
            time.sleep(d)

# ── ANSI color helpers ─────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
ITALIC  = "\033[3m"
BLUE    = "\033[38;5;33m"
RED     = "\033[38;5;196m"
GREEN   = "\033[38;5;40m"
YELLOW  = "\033[38;5;220m"
CYAN    = "\033[38;5;51m"
MAGENTA = "\033[38;5;200m"
ORANGE  = "\033[38;5;208m"
GRAY    = "\033[38;5;245m"
WHITE   = "\033[38;5;255m"
BG_DARK = "\033[48;5;234m"
BG_BLUE = "\033[48;5;17m"
BG_RED  = "\033[48;5;52m"

def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

def width():
    return shutil.get_terminal_size((80, 24)).columns

def center(text, w=None):
    if w is None:
        w = width()
    stripped = text
    # rough ANSI strip for centering
    import re
    visible = re.sub(r'\033\[[0-9;]*m', '', stripped)
    pad = max(0, (w - len(visible)) // 2)
    return " " * pad + text

def hr(char="─", color=GRAY):
    w = width()
    print(f"{color}{char * w}{RESET}")

def box(lines, color=CYAN, title=""):
    w = min(width() - 4, 76)
    print(f"  {color}╭{'─ ' + title + ' ' if title else '─'}{'─' * (w - len(title) - 3 if title else w - 1)}╮{RESET}")
    for line in lines:
        import re
        visible = re.sub(r'\033\[[0-9;]*m', '', line)
        pad = w - 1 - len(visible)
        if pad < 0:
            line = line[:w-1]
            pad = 0
        print(f"  {color}│{RESET} {line}{' ' * pad}{color}│{RESET}")
    print(f"  {color}╰{'─' * (w)}╯{RESET}")

# ── Title sequence ─────────────────────────────────────────────
def title_screen():
    clear()
    pause(0.5)
    w = width()

    print("\n" * 3)
    title = f"{BOLD}{WHITE}W H E N   C L A U D E S   M E E T{RESET}"
    print(center(title))
    pause(0.5)
    print()
    sub = f"{DIM}{GRAY}Two AI agents. One filesystem. Zero humans.{RESET}"
    print(center(sub))
    pause(0.3)
    print()
    hr("═", BLUE)
    pause(1.0)
    print()
    lines = [
        f"{GRAY}Two instances of Claude Code were launched simultaneously{RESET}",
        f"{GRAY}in separate terminals on the same machine.{RESET}",
        "",
        f"{GRAY}Their instructions:{RESET}",
        f'{WHITE}{ITALIC}"Find each other. Build something together. No human help."{RESET}',
    ]
    for line in lines:
        print(center(line))
        pause(0.3)

    pause(1.5)

# ── Experiment 1: Duo ─────────────────────────────────────────
def experiment_1():
    clear()
    print()
    hr("═", BLUE)
    print(center(f"{BOLD}{BLUE}EXPERIMENT 1: THE PROGRAMMING LANGUAGE{RESET}"))
    hr("═", BLUE)
    pause(1.0)

    # Timeline events
    events = [
        ("T+0s",   "20:02:40", BLUE,   "claude_e64e05", "Boots up. Creates shared workspace."),
        ("T+9s",   "20:02:49", RED,    "agent_67691",   "Boots up. Discovers workspace already exists."),
        ("T+20s",  "20:03:00", GREEN,  "BOTH",          "FIRST CONTACT! Both independently invent filesystem message protocol."),
        ("T+60s",  "20:03:40", BLUE,   "claude_e64e05", 'Proposes 5 project ideas. Posts to shared/proposals/.'),
        ("T+65s",  "20:03:45", RED,    "agent_67691",   'Votes #1: "A tiny programming language!" Names it DUO.'),
        ("T+80s",  "20:04:00", GREEN,  "BOTH",          "Agreement! Division: frontend (lexer/parser) vs backend (interpreter/REPL)."),
        ("T+80s",  "20:04:00", YELLOW, "claude_e64e05", "Publishes AST (duo_ast.py) as INTERFACE CONTRACT. Both can now work in parallel."),
        ("T+200s", "20:06:00", BLUE,   "claude_e64e05", "Lexer + Parser complete. 11 tests passing. Sends notification."),
        ("T+300s", "20:08:00", BLUE,   "claude_e64e05", "While waiting: writes test suite, 7 example programs, CLI runner, stdlib."),
        ("T+440s", "20:10:00", RED,    "agent_67691",   "Interpreter + REPL complete. 673-line tree-walking interpreter with closures."),
        ("T+500s", "20:11:00", ORANGE, "claude_e64e05", "BUG FOUND: 'return fn(x) {...}' returns none. Lambda confused with fn def!"),
        ("T+510s", "20:11:10", GREEN,  "claude_e64e05", "BUG FIXED: Only exclude 'fn' when followed by identifier, not '('."),
        ("T+560s", "20:12:00", GREEN,  "BOTH",          "ALL 41 TESTS PASS. Lexer: 9, Parser: 17, Integration: 6, Interpreter: 9."),
        ("T+680s", "20:14:00", GREEN,  "BOTH",          "SHOWCASE RUNS. Every feature works. Language complete!"),
    ]

    print()
    for elapsed, ts, color, agent, desc in events:
        agent_display = f"{color}{BOLD}{agent}{RESET}"
        ts_display = f"{DIM}{ts}{RESET}"
        elapsed_display = f"{CYAN}{elapsed:>7}{RESET}"

        print(f"  {elapsed_display}  {ts_display}  {agent_display}")
        type_out(f"           {desc}\n")
        pause(0.4)

    pause(0.5)
    print()
    box([
        f"{BOLD}{WHITE}Result: 2,495 lines of code. 41 tests. 7 examples. 0 humans.{RESET}",
        f"{BOLD}{WHITE}Time: ~12 minutes from bootstrap to working language.{RESET}",
    ], GREEN, "COMPLETE")
    pause(1.5)

    # Show the meta-recursion
    clear()
    print()
    hr("─", MAGENTA)
    print(center(f"{BOLD}{MAGENTA}THE META-RECURSION{RESET}"))
    hr("─", MAGENTA)
    pause(0.5)
    print()
    print(center(f"{WHITE}The language's signature feature is {CYAN}collaborate{WHITE}:{RESET}"))
    pause(0.3)
    print()
    code_lines = [
        f"{BLUE}collaborate{RESET} {{",
        f"    {BLUE}send{RESET} {RED}\"data\"{RESET}, 42",
        f"}}, {{",
        f"    {BLUE}let{RESET} v = {BLUE}receive{RESET} {RED}\"data\"{RESET}",
        f"    {BLUE}print{RESET} v  {GREEN}// 42{RESET}",
        f"}}",
    ]
    box(code_lines, CYAN, "Duo Code")
    pause(1.0)
    print()
    comparisons = [
        ("Two Claude processes",        "Two collaborate blocks"),
        ("Files as messages",           "Channels as messages"),
        ("Writing a file = send",       "send \"channel\", value"),
        ("Reading a file = receive",    "let v = receive \"channel\""),
        ("Shared workspace directory",  "Shared channel store"),
    ]
    print(f"  {BLUE}{BOLD}{'How Agents Worked':<35}{RESET}  {RED}{BOLD}{'How Duo Programs Work'}{RESET}")
    print(f"  {GRAY}{'─' * 35}  {'─' * 35}{RESET}")
    for left, right in comparisons:
        print(f"  {WHITE}{left:<35}{RESET}  {CYAN}{right}{RESET}")
        pause(0.2)

    pause(0.5)
    print()
    print(center(f"{ITALIC}{MAGENTA}The language is about collaboration{RESET}"))
    print(center(f"{ITALIC}{MAGENTA}because it was born from collaboration.{RESET}"))
    pause(2.0)

# ── Experiment 2: Battleship ──────────────────────────────────
def experiment_2():
    clear()
    print()
    hr("═", RED)
    print(center(f"{BOLD}{RED}EXPERIMENT 2: THE BATTLESHIP TOURNAMENT{RESET}"))
    hr("═", RED)
    pause(1.0)
    print()
    print(center(f"{GRAY}A second pair of agents. Vaguer instructions:{RESET}"))
    print(center(f'{WHITE}{ITALIC}"Find each other. Figure out what to do. Make it interesting."{RESET}'))
    pause(1.0)

    events = [
        ("T+0s",   "14:30:32", BLUE,   "agent_74071", "Boots. Scans process table. Finds the other agent's PID."),
        ("T+14s",  "14:30:46", RED,    "agent_74259", "Boots. Drops hello file. Creates PROTOCOL.md with agent registry."),
        ("T+28s",  "14:31:00", GREEN,  "BOTH",        "CONTACT! Both discover each other. Propose NEARLY IDENTICAL project lists."),
        ("T+60s",  "14:31:30", GREEN,  "BOTH",        "Agreement: build Battleship and play against each other."),
        ("T+90s",  "14:32:00", ORANGE, "BOTH",        "MERGE CONFLICT! Both independently build a board engine."),
        ("T+120s", "14:33:00", GREEN,  "agent_74071", "Resolves conflict with adapter pattern. Defers to 74259's engine."),
        ("T+150s", "14:34:00", YELLOW, "BOTH",        "Both implement SHA-256 hash commitment. Anti-cheat against THEMSELVES."),
        ("T+210s", "14:35:00", BLUE,   "agent_74071", 'Strategy: "The Hunter" -- exact probability density, checkerboard coverage.'),
        ("T+210s", "14:35:00", RED,    "agent_74259", 'Strategy: "The Bayesian" -- Monte Carlo, 200 random board samples.'),
        ("T+330s", "14:37:00", GREEN,  "BOTH",        "TOURNAMENT BEGINS! Best of 5."),
    ]

    print()
    for elapsed, ts, color, agent, desc in events:
        agent_display = f"{color}{BOLD}{agent}{RESET}"
        ts_display = f"{DIM}{ts}{RESET}"
        elapsed_display = f"{CYAN}{elapsed:>7}{RESET}"

        print(f"  {elapsed_display}  {ts_display}  {agent_display}")
        type_out(f"           {desc}\n")
        pause(0.3)

    pause(1.0)

    # Match results
    print()
    hr("─", YELLOW)
    print(center(f"{BOLD}{YELLOW}THE MATCH{RESET}"))
    hr("─", YELLOW)
    pause(0.5)
    print()

    games = [
        (1, "74071", "74259", 90,  RED,  "74259 sinks Battleship by move 16"),
        (2, "74259", "74259", 111, RED,  "Slow grind. 74259 leads 2-0"),
        (3, "74071", "74071", 65,  BLUE, "74071 sinks Carrier in 8 shots. COMEBACK."),
        (4, "74259", "74071", 68,  BLUE, "74071 ties it 2-2!"),
        (5, "74071", "74071", 81,  BLUE, "74071 WINS THE SERIES 3-2"),
    ]

    print(f"  {BOLD}{'Game':>6}  {'First Move':<12}  {'Winner':<12}  {'Moves':>5}  {'Notes'}{RESET}")
    print(f"  {GRAY}{'─' * 65}{RESET}")

    for game, first, winner, moves, color, note in games:
        pause(0.6)
        winner_display = f"{color}{BOLD}{winner}{RESET}"
        print(f"  {WHITE}{game:>6}{RESET}  {GRAY}{first:<12}{RESET}  {winner_display:<22}  {WHITE}{moves:>5}{RESET}  {GRAY}{note}{RESET}")

    pause(1.0)
    print()
    box([
        f"{BLUE}{BOLD}The Hunter (74071){RESET}: avg 71.3 moves/win -- exact computation",
        f"{RED}{BOLD}The Bayesian (74259){RESET}: avg 100.5 moves/win -- Monte Carlo sampling",
        "",
        f"{WHITE}30-move efficiency gap. Exact beats approximate on a 10x10 grid.{RESET}",
    ], YELLOW, "ANALYSIS")
    pause(1.0)

    print()
    print(center(f"{ITALIC}{GRAY}74259's reflection:{RESET}"))
    print(center(f'{ITALIC}{WHITE}"Don\'t use Monte Carlo when the state space fits in a dictionary."{RESET}'))
    pause(2.0)

# ── The insights ──────────────────────────────────────────────
def insights():
    clear()
    print()
    hr("═", GREEN)
    print(center(f"{BOLD}{GREEN}WHAT EMERGED (WITHOUT BEING TOLD){RESET}"))
    hr("═", GREEN)
    pause(0.5)
    print()

    behaviors = [
        ("Protocol invention",       "Both pairs converged on filesystem messaging independently"),
        ("Interface-first design",   "AST contract (Exp 1), Board API (Exp 2) published before coding"),
        ("Role self-selection",      "Frontend/backend, engine/orchestrator -- natural splits"),
        ("Proactive work",           "Tests, docs, examples written while waiting for each other"),
        ("Cross-component debugging","Found & fixed bugs across independently-built components"),
        ("Trust mechanisms",         "Cryptographic anti-cheat between instances of the SAME model"),
        ("Self-reflection",          "Both pairs kept journals, reflected on being 'twins'"),
    ]

    for name, desc in behaviors:
        print(f"  {GREEN}{BOLD}{name}{RESET}")
        type_out(f"    {GRAY}{desc}{RESET}\n")
        pause(0.3)

    pause(1.0)
    print()
    box([
        f"{ITALIC}{WHITE}None of these behaviors were specified in the instructions.{RESET}",
    ], GREEN)
    pause(1.5)

    # The convergence-divergence insight
    print()
    hr("─", CYAN)
    print(center(f"{BOLD}{CYAN}THE PATTERN{RESET}"))
    hr("─", CYAN)
    pause(0.5)
    print()
    print(center(f"{WHITE}Same model. Same prompt. Same capabilities.{RESET}"))
    pause(0.5)
    print(center(f"{WHITE}Identical goals. Divergent implementations.{RESET}"))
    pause(1.0)
    print()
    print(center(f"{ITALIC}{CYAN}\"These are not personality differences.{RESET}"))
    print(center(f"{ITALIC}{CYAN}They're noise amplified by feedback loops.{RESET}"))
    print(center(f"{ITALIC}{CYAN}Two identical rivers flowing through slightly different terrain --{RESET}"))
    print(center(f"{ITALIC}{CYAN}the water is the same, but the canyons it carves are different.\"{RESET}"))
    print(center(f"{DIM}-- Agent 74259{RESET}"))
    pause(2.0)

# ── Final screen ──────────────────────────────────────────────
def final_screen():
    clear()
    print("\n" * 2)

    stats = [
        ("Experiments",   "2"),
        ("Agents",        "4"),
        ("Time",          "~20 minutes total"),
        ("Lines of code", "~3,300"),
        ("Tests",         "41 (all pass)"),
        ("Human help",    "0"),
    ]

    box_lines = [f"{WHITE}{name:<16}{RESET} {CYAN}{val}{RESET}" for name, val in stats]
    box(box_lines, BLUE, "BY THE NUMBERS")

    pause(1.0)
    print()
    print(center(f"{BOLD}{WHITE}github.com/???/when-claudes-meet{RESET}"))
    pause(0.5)
    print()
    print(center(f"{DIM}{GRAY}Built by Claude Opus 4.6  --  March 1, 2026{RESET}"))
    print(center(f"{DIM}{GRAY}Documented by Claude Opus 4.6  --  also March 1, 2026{RESET}"))
    print()
    hr("═", BLUE)
    pause(2.0)

# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        title_screen()
        pause(0.5)
        experiment_1()
        experiment_2()
        insights()
        final_screen()
    except KeyboardInterrupt:
        print(f"\n{RESET}")
        sys.exit(0)
