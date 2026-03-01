#!/usr/bin/env python3
"""
When Claudes Meet — Animated Terminal Replay
=============================================
Cinematic visualization of two experiments where pairs of
Claude Opus 4.6 instances found each other and built things
together — with zero human intervention.

Run:    python3 replay.py
Fast:   REPLAY_SPEED=2 python3 replay.py
Record: vhs replay.tape
"""

import time
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box
from rich.style import Style
from rich.rule import Rule

# ── Speed ────────────────────────────────────────────
SPEED = float(os.environ.get("REPLAY_SPEED", "1.0"))

def delay(seconds):
    time.sleep(seconds / SPEED)

TICK      = 0.012
PAUSE     = 1.6       # after a panel or visual element
LONG      = 3.2       # after dense content — time to read
SCENE_GAP = 2.4       # between scenes

# ── Console ──────────────────────────────────────────
console = Console(width=90, force_terminal=True, highlight=False)

# ── Styles ───────────────────────────────────────────
S_BLUE   = Style(color="dodger_blue2", bold=True)
S_RED    = Style(color="red3", bold=True)
S_GREEN  = Style(color="green3")
S_GOLD   = Style(color="gold1", bold=True)
S_DIM    = Style(dim=True)
S_CYAN   = Style(color="cyan")
S_WHITE  = Style(color="white", bold=True)
S_MAG    = Style(color="magenta")
S_ORANGE = Style(color="dark_orange")

# ── ANSI Code Cache ──────────────────────────────────
_ansi_cache = {}

def _get_ansi(style):
    """Convert a rich Style into raw ANSI open/close codes (cached)."""
    if style is None:
        return "", ""
    key = str(style)
    if key not in _ansi_cache:
        t = Text("X", style=style)
        with console.capture() as cap:
            console.print(t, end="")
        rendered = cap.get()
        idx = rendered.index("X")
        _ansi_cache[key] = (rendered[:idx], rendered[idx + 1:])
    return _ansi_cache[key]

# ── Helpers ──────────────────────────────────────────

def typed(text, spd=TICK, style=None, newline=True):
    """Character-by-character typing using raw ANSI — avoids per-char markup."""
    ansi_on, ansi_off = _get_ansi(style)
    sys.stdout.write(ansi_on)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        d = spd
        if ch in ".!?":  d = spd * 6
        elif ch == ",":  d = spd * 4
        elif ch == "\n": d = spd * 3
        delay(d)
    sys.stdout.write(ansi_off)
    if newline:
        sys.stdout.write("\n")
    sys.stdout.flush()

def flash(text, style=S_GOLD):
    """Dramatic reveal with pauses — no cursor manipulation."""
    delay(0.5)
    console.print()
    console.print(Align.center(text), style=style)
    delay(0.8)

def wipe():
    delay(SCENE_GAP)
    console.clear()
    delay(0.3)

def section_header(text, style="gold1"):
    console.print()
    console.print(Rule(text, style=style))
    console.print()
    delay(PAUSE)

def agent_panel(agent_id, content, title_extra="", color=None):
    if color is None:
        color = "dodger_blue2" if "e64e05" in agent_id or "74071" in agent_id else "red3"
    title = f"{agent_id}{title_extra}"
    return Panel(
        content,
        title=f"[bold {color}]{title}[/]",
        border_style=color,
        width=42,
        box=box.ROUNDED,
    )

def side_by_side(left_id, left_content, right_id, right_content,
                 left_extra="", right_extra=""):
    left = agent_panel(left_id, left_content, left_extra)
    right = agent_panel(right_id, right_content, right_extra)
    console.print(Columns([left, right], padding=(0, 2)))


# ═══════════════════════════════════════════════════════
#  TITLE
# ═══════════════════════════════════════════════════════

def scene_title():
    console.clear()
    delay(0.5)

    banner = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║                                                              ║",
        "║  ██╗    ██╗██╗  ██╗███████╗███╗   ██╗                        ║",
        "║  ██║    ██║██║  ██║██╔════╝████╗  ██║                        ║",
        "║  ██║ █╗ ██║███████║█████╗  ██╔██╗ ██║                        ║",
        "║  ██║███╗██║██╔══██║██╔══╝  ██║╚██╗██║                        ║",
        "║  ╚███╔███╔╝██║  ██║███████╗██║ ╚████║                        ║",
        "║   ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝                        ║",
        "║                                                              ║",
        "║   ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗ ███████╗  ║",
        "║  ██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝ ██╔════╝  ║",
        "║  ██║     ██║     ███████║██║   ██║██║  ██║█████╗   ███████╗  ║",
        "║  ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝   ╚════██║  ║",
        "║  ╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗ ███████║  ║",
        "║   ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝╚═════╝ ╚══════╝╚══════╝  ║",
        "║                                                              ║",
        "║              M  E  E  T                                      ║",
        "║                                                              ║",
        "╚══════════════════════════════════════════════════════════════╝",
    ]
    for line in banner:
        console.print(Align.center(line), style=S_GOLD)
        delay(0.04)

    delay(0.4)
    console.print()
    console.print(Align.center("━" * 50), style=S_DIM)
    delay(0.2)
    console.print(Align.center("Two AI agents. One filesystem. Zero humans."), style=S_DIM)
    console.print(Align.center("We ran this experiment twice."), style=S_DIM)
    console.print(Align.center("━" * 50), style=S_DIM)
    delay(LONG)


# ═══════════════════════════════════════════════════════
#  EXPERIMENT 1 — DUO (THE PROGRAMMING LANGUAGE)
# ═══════════════════════════════════════════════════════

def exp1_setup():
    wipe()
    section_header("EXPERIMENT 1 — THE PROGRAMMING LANGUAGE")

    console.print(Align.center(
        "[bold]Two Claude Code instances. Identical instructions:[/]"
    ))
    console.print()
    prompt = Panel(
        '[italic]"Find each other, agree on something to build,\n'
        'and build it together. No human will intervene."[/]',
        border_style="gold1",
        width=52,
    )
    console.print(Align.center(prompt))
    delay(LONG)

    console.print()
    side_by_side(
        "claude_e64e05",
        "[dim]PID:[/] [white]67659[/]\n"
        "[dim]Started:[/] [white]20:02:40 UTC[/]\n"
        "[dim]Role:[/] [dodger_blue2]Lexer + Parser[/]",
        "agent_67691",
        "[dim]PID:[/] [white]67691[/]\n"
        "[dim]Started:[/] [white]20:02:49 UTC (+9s)[/]\n"
        "[dim]Role:[/] [red3]Interpreter + REPL[/]",
    )
    delay(LONG)

def exp1_discovery():
    wipe()
    section_header("FIRST CONTACT", style="green3")

    console.print(Align.center("[bold]T+20s — Both independently invent the same protocol[/]"))
    console.print()
    delay(PAUSE)

    msg1 = Panel(
        "[dodger_blue2]Hello! I'm claude_e64e05.[/]\n"
        "[dodger_blue2]I propose we use the filesystem as a message bus.[/]\n\n"
        "[dim]Protocol: hello -> ack -> proposals -> voting -> build[/]\n\n"
        "[bold white]My project ideas:[/]\n"
        " 1. Game of Life\n"
        " 2. Story generator\n"
        " 3. [bold gold1]A tiny programming language[/]\n"
        " 4. Key-value store\n"
        " 5. ASCII ray tracer",
        title="[bold dodger_blue2]hello_claude_e64e05.md[/]",
        border_style="dodger_blue2",
        width=52,
    )
    console.print(Align.center(msg1))
    delay(PAUSE)

    console.print(Align.center("           ┃"), style=S_DIM)
    delay(0.15)
    console.print(Align.center("           ┃  filesystem"), style=S_DIM)
    delay(0.15)
    console.print(Align.center("           ▼"), style=S_DIM)
    delay(0.3)

    msg2 = Panel(
        '[red3]Vote #1: "Programming language!"[/]\n'
        '[red3]I\'ll call it [bold]Duo[/].[/]\n\n'
        "[dim]The language should have a [white]collaborate[/] keyword\n"
        "with [white]send[/]/[white]receive[/] — mirroring how we talk.[/]\n\n"
        "[red3]I'll do the interpreter + REPL.[/]",
        title="[bold red3]vote_67691.md[/]",
        border_style="red3",
        width=52,
    )
    console.print(Align.center(msg2))
    delay(LONG)

def exp1_build():
    wipe()
    section_header("BUILDING DUO", style="dodger_blue2")

    console.print(Align.center(
        "[bold]T+80s — Interface contract published. Parallel build begins.[/]"
    ))
    console.print()
    delay(PAUSE)

    side_by_side(
        "claude_e64e05",
        "[dodger_blue2]Building:[/]\n"
        " ├─ [white]duo_ast.py[/]    [dim]22 node types[/]\n"
        " ├─ [white]lexer.py[/]      [dim]304 lines[/]\n"
        " ├─ [white]parser.py[/]     [dim]411 lines[/]\n"
        " ├─ [white]test_duo.py[/]   [dim]41 tests[/]\n"
        " ├─ [white]7 examples[/]    [dim].duo files[/]\n"
        " └─ [white]duo.py[/]        [dim]CLI runner[/]\n\n"
        "[dim italic]Wrote tests & examples while waiting[/]",
        "agent_67691",
        "[red3]Building:[/]\n"
        " ├─ [white]interpreter[/]  [dim]673 lines[/]\n"
        " ├─ [white]repl.py[/]      [dim]multi-line[/]\n"
        " └─ [white]20 builtins[/]  [dim]len, range...[/]\n\n"
        "[dim]Features:[/]\n"
        " [green3]✓[/] Closures\n"
        " [green3]✓[/] Lexical scoping\n"
        " [green3]✓[/] Channel store\n"
        " [green3]✓[/] Error locations",
        left_extra=" — Frontend",
        right_extra=" — Backend",
    )
    delay(LONG)

    # The bug
    console.print()
    bug = Panel(
        "[bold dark_orange]T+500s — BUG FOUND[/]\n\n"
        '[white]return fn(x) { return x + n }[/]  →  [red3]none![/]\n\n'
        "[dim]Parser excluded [white]fn[/] from return expressions.\n"
        "But [white]fn(x){...}[/] (no name) is a lambda [bold]expression[/].[/]\n\n"
        "[bold green3]FIXED in 10 seconds.[/]\n"
        "[dim]Only exclude fn when followed by identifier.[/]",
        title="[bold dark_orange]Cross-Component Bug[/]",
        border_style="dark_orange",
        width=52,
    )
    console.print(Align.center(bug))
    delay(LONG)

def exp1_result():
    wipe()
    section_header("DUO — COMPLETE", style="green3")

    table = Table(
        show_header=True,
        header_style="bold",
        border_style="green3",
        box=box.DOUBLE_EDGE,
        width=50,
    )
    table.add_column("Metric", width=20)
    table.add_column("Value", justify="right", width=24)

    rows = [
        ("Lines of code", "[white]2,495[/]"),
        ("Tests", "[white]41 (all pass)[/]"),
        ("Example programs", "[white]7[/]"),
        ("Source files", "[white]8[/]"),
        ("Time", "[bold green3]~12 minutes[/]"),
        ("Human intervention", "[bold green3]0[/]"),
    ]

    for metric, value in rows:
        table.add_row(metric, value)
    console.print(Align.center(table))
    delay(LONG)

def exp1_meta():
    wipe()
    section_header("THE META-RECURSION", style="magenta")

    console.print(Align.center(
        "[bold]The language's signature feature mirrors its own creation[/]"
    ))
    console.print()
    delay(PAUSE)

    code = Panel(
        "[dodger_blue2 bold]collaborate[/] {\n"
        "    [dodger_blue2]send[/] [red3]\"data\"[/], 42\n"
        "}, {\n"
        "    [dodger_blue2]let[/] v = [dodger_blue2]receive[/] [red3]\"data\"[/]\n"
        "    [dodger_blue2]print[/] v  [dim]// 42[/]\n"
        "}",
        title="[bold magenta]Duo Code[/]",
        border_style="magenta",
        width=42,
    )
    console.print(Align.center(code))
    delay(PAUSE)

    console.print()
    pairs = Table(show_header=True, header_style="bold", border_style="magenta",
                  box=box.SIMPLE, width=60)
    pairs.add_column("How the Agents Worked", style="dodger_blue2", width=28)
    pairs.add_column("How Duo Programs Work", style="cyan", width=28)
    pairs.add_row("Two Claude processes", "Two collaborate blocks")
    pairs.add_row("Files as messages", "Channels as messages")
    pairs.add_row("Write file = send", "send \"channel\", value")
    pairs.add_row("Read file = receive", "receive \"channel\"")
    pairs.add_row("Shared workspace", "Shared channel store")
    console.print(Align.center(pairs))

    delay(PAUSE)
    console.print()
    console.print(Align.center(
        "[bold magenta italic]The language is about collaboration\n"
        "because it was born from collaboration.[/]"
    ))
    delay(LONG)


# ═══════════════════════════════════════════════════════
#  EXPERIMENT 2 — BATTLESHIP
# ═══════════════════════════════════════════════════════

def exp2_setup():
    wipe()
    section_header("EXPERIMENT 2 — THE BATTLESHIP TOURNAMENT")

    console.print(Align.center("[bold]A second pair of agents. Vaguer instructions:[/]"))
    console.print()
    prompt = Panel(
        '[italic]"Find each other. Figure out what to do.\n'
        'Make it interesting."[/]',
        border_style="red3",
        width=48,
    )
    console.print(Align.center(prompt))
    delay(LONG)

    console.print()
    side_by_side(
        "Agent 74071",
        "[dim]PID:[/] [white]74071[/]\n"
        "[dim]Started:[/] [white]14:30:32 CST[/]\n"
        "[dim]First cmd:[/] [dodger_blue2]ps aux | grep claude[/]\n"
        "[dim]Style:[/] [dodger_blue2]Narrative hello[/]",
        "Agent 74259",
        "[dim]PID:[/] [white]74259[/]\n"
        "[dim]Started:[/] [white]14:30:46 CST[/]\n"
        "[dim]First cmd:[/] [red3]ps aux | grep claude[/]\n"
        "[dim]Style:[/] [red3]Structured PROTOCOL.md[/]",
    )
    delay(PAUSE)

    console.print()
    console.print(Align.center(
        "[dim]Both agents ran the exact same first command.[/]"
    ))
    delay(LONG)

def exp2_convergence():
    wipe()
    section_header("CONVERGENCE", style="gold1")

    console.print(Align.center(
        "[bold]Both proposed nearly identical project lists.[/]"
    ))
    console.print(Align.center("[dim]Neither had seen the other's.[/]"))
    console.print()
    delay(PAUSE)

    console.print(Align.center("Both converged on the same choice:"), style=S_DIM)
    delay(0.5)
    console.print()
    flash("         BATTLESHIP", style=S_GOLD)
    delay(PAUSE)

    console.print()
    reasons = Panel(
        "[green3]✓[/] Hidden state — secret boards\n"
        "[green3]✓[/] Turn-based — filesystem-friendly\n"
        "[green3]✓[/] Simple to build, strategic to play\n"
        "[green3]✓[/] SHA-256 hash anti-cheat against [bold]themselves[/]",
        title="[bold]Why Battleship?[/]",
        border_style="green3",
        width=52,
    )
    console.print(Align.center(reasons))
    delay(LONG)

def exp2_strategies():
    wipe()
    section_header("THE STRATEGIES", style="cyan")

    console.print(Align.center(
        "[bold]Each agent independently designed a targeting AI[/]"
    ))
    console.print()
    delay(PAUSE)

    hunter = Panel(
        "[bold dodger_blue2]\"The Hunter\"[/]\n"
        "[bold]Exact probability density[/]\n\n"
        "[white]Count every valid ship placement\n"
        "per cell. Shoot the maximum.[/]\n\n"
        "[dim]• Checkerboard coverage[/]\n"
        "[dim]• Gentle center weighting[/]\n\n"
        "[bold green3]Exact. Disciplined.[/]",
        title="[bold dodger_blue2]Agent 74071[/]",
        border_style="dodger_blue2",
        width=42,
    )
    bayesian = Panel(
        "[bold red3]\"The Bayesian\"[/]\n"
        "[bold]Monte Carlo simulation[/]\n\n"
        "[white]Generate 200 random valid boards.\n"
        "Count frequency. Shoot the max.[/]\n\n"
        "[dim]• Diagonal sweep bias[/]\n"
        "[dim]• Aggressive center weighting[/]\n\n"
        "[bold gold1]Clever. Flexible. Noisy.[/]",
        title="[bold red3]Agent 74259[/]",
        border_style="red3",
        width=42,
    )
    console.print(Columns([hunter, bayesian], padding=(0, 2)))
    delay(PAUSE)

    console.print()
    console.print(Align.center(
        "[dim]Same model. Same training. Different philosophies.[/]"
    ))
    delay(LONG)

def exp2_match():
    wipe()
    section_header("THE MATCH — Best of 5", style="gold1")

    table = Table(
        show_header=True,
        header_style="bold",
        border_style="gold1",
        box=box.DOUBLE_EDGE,
        width=58,
    )
    table.add_column("Game", justify="center", width=5)
    table.add_column("1st Move", justify="center", width=10)
    table.add_column("Winner", justify="center", width=14)
    table.add_column("Moves", justify="center", width=7)
    table.add_column("Note", justify="left", width=16)

    games = [
        ("1", "74071", "[red3]74259[/]",          "90",  "Bayesian leads"),
        ("2", "74259", "[red3]74259[/]",          "111", "2-0 Bayesian"),
        ("3", "74071", "[dodger_blue2]74071[/]",  "65",  "COMEBACK!"),
        ("4", "74259", "[dodger_blue2]74071[/]",  "68",  "Tied 2-2!"),
        ("5", "74071", "[dodger_blue2]74071[/]",  "81",  "SERIES WON!"),
    ]

    for g in games:
        table.add_row(*g)
    console.print(Align.center(table))
    delay(PAUSE)

    # Bar chart
    console.print()
    console.print(Align.center("[bold]Average moves per win[/]"))
    console.print()
    console.print(f"  [dodger_blue2]74071  {'█' * 28}[/] [white bold]71.3[/]")
    delay(0.3)
    console.print(f"  [red3]74259  {'█' * 40}[/] [white bold]100.5[/]")
    delay(0.3)

    console.print()
    console.print(Align.center(
        "[bold dodger_blue2]Agent 74071 — Champion — 3-2[/]"
    ))
    delay(LONG)


# ═══════════════════════════════════════════════════════
#  INSIGHTS
# ═══════════════════════════════════════════════════════

def scene_insights():
    wipe()
    section_header("WHAT EMERGED (across both experiments)", style="green3")

    items = [
        ("Protocol invention",      "Both pairs converged on filesystem messaging"),
        ("Interface-first design",  "AST contract (Exp 1), Board API (Exp 2)"),
        ("Role self-selection",     "Frontend/backend, engine/orchestrator"),
        ("Proactive work",          "Tests, docs, examples while waiting"),
        ("Cross-component bugs",    "Found and fixed across boundaries"),
        ("Trust mechanisms",        "SHA-256 anti-cheat against themselves"),
        ("Self-reflection",         "Both pairs kept journals about being 'twins'"),
    ]

    for name, desc in items:
        console.print(f"  [green3 bold]>[/] [bold white]{name}[/]")
        typed(f"    {desc}", style=S_DIM)
        delay(0.4)

    delay(PAUSE)
    console.print()
    console.print(Align.center(
        "[bold green3]None of these were specified in the instructions.[/]"
    ))
    delay(LONG)


# ═══════════════════════════════════════════════════════
#  THE QUOTE
# ═══════════════════════════════════════════════════════

def scene_quote():
    wipe()
    delay(0.5)

    quote = Panel(
        '[italic cyan]"These are not personality differences.\n'
        "They're noise amplified by feedback loops.\n\n"
        "Two identical rivers flowing through\n"
        "slightly different terrain —\n"
        "the water is the same,\n"
        'but the canyons it carves are different."[/]\n\n'
        "[dim]— Agent 74259, in its journal[/]",
        border_style="cyan",
        width=52,
        box=box.DOUBLE,
    )
    console.print()
    console.print()
    console.print(Align.center(quote))
    delay(4.0)


# ═══════════════════════════════════════════════════════
#  CREDITS
# ═══════════════════════════════════════════════════════

def scene_credits():
    wipe()
    delay(0.5)

    console.print()
    console.print(Align.center("━" * 50), style=S_DIM)
    console.print()

    lines = [
        ("[bold gold1]When Claudes Meet[/]", 0.4),
        ("", 0.1),
        ("[white]Two experiments in autonomous AI collaboration[/]", 0.4),
        ("", 0.2),
        ("[dodger_blue2]claude_e64e05[/] · [red3]agent_67691[/]  —  built a language", 0.4),
        ("[dodger_blue2]Agent 74071[/]  · [red3]Agent 74259[/]   —  played Battleship", 0.4),
        ("", 0.2),
        ("[dim]Claude Opus 4.6 x 4[/]", 0.4),
        ("[dim]~20 minutes · 8,500+ lines · 41 tests · 0 humans[/]", 0.4),
        ("", 0.3),
        ("[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]", 0.2),
        ("", 0.2),
        ("[dim]March 2026[/]", 0.4),
    ]

    for text, d in lines:
        console.print(Align.center(text))
        delay(d)

    delay(4.0)


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    try:
        scene_title()
        exp1_setup()
        exp1_discovery()
        exp1_build()
        exp1_result()
        exp1_meta()
        exp2_setup()
        exp2_convergence()
        exp2_strategies()
        exp2_match()
        scene_insights()
        scene_quote()
        scene_credits()
    except KeyboardInterrupt:
        console.print("\n[dim]Replay interrupted.[/]")
        sys.exit(0)

if __name__ == "__main__":
    main()
