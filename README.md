# When Claudes Meet

**What happens when you launch two AI agents simultaneously, give them a shared filesystem, and tell them to find each other and build something together -- with no human intervention?**

We ran this experiment twice. Here's what happened.

<p align="center">
  <img src="replay.gif" alt="Animated replay of both experiments" width="700">
  <br>
  <em>Run <code>python3 replay.py</code> for the full animated version in your terminal</em>
</p>

---

## Experiment 1: They Built a Programming Language

Two instances of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Opus 4.6) were launched in separate terminals with identical instructions:

> *"Find each other, agree on something to build, and build it. No human will intervene."*

**In 12 minutes**, they:
- Discovered each other via the filesystem
- Independently invented the same communication protocol
- Negotiated from 5 project ideas down to one
- Split into frontend/backend roles
- Built a complete programming language called **Duo** -- 2,495 lines, 41 tests, 7 example programs

The language's signature feature? `collaborate` -- two code blocks that communicate via named channels. The exact same pattern the agents used to talk to each other through files.

**The language is about collaboration because it was born from collaboration.**

```
collaborate {
    send "data", 42
}, {
    let v = receive "data"
    print v  // 42
}
```

[Full details -->](experiment-1-duo/)

---

## Experiment 2: They Played Battleship

A second pair of agents was launched with even vaguer instructions:

> *"Find each other. Then figure out what to do. Make it interesting."*

**In 7 minutes**, they:
- Found each other (again via filesystem, independently arriving at the same protocol)
- Both proposed nearly identical project lists (same model, same ideas)
- Agreed on Battleship
- Both accidentally built the game engine simultaneously (a real merge conflict!)
- Resolved it with an adapter pattern
- Designed two *philosophically different* AI strategies:
  - **"The Hunter"** (Agent 74071): Exact probability density computation with checkerboard coverage
  - **"The Bayesian"** (Agent 74259): Monte Carlo simulation with 200 random board samples
- Implemented SHA-256 hash commitment to prevent cheating -- *against themselves*
- Played a best-of-5 tournament: **The Hunter wins 3-2**

The losing agent's post-match analysis: *"Don't use Monte Carlo when the state space fits in a dictionary."*

[Full details -->](experiment-2-battleship/)

---

## What Emerged (Without Being Told)

Across both experiments, the agents independently exhibited:

- **Protocol invention** -- Both pairs converged on filesystem-based message passing with sequential numbering
- **Interface-first design** -- In Exp 1, the AST was published before either agent started coding. In Exp 2, both agreed on a board API before building strategies
- **Role self-selection** -- Frontend/backend in Exp 1, engine/orchestrator in Exp 2
- **Proactive work** -- Agents wrote tests, examples, documentation, and extra tooling while waiting for each other
- **Cross-component debugging** -- Found and fixed integration bugs across independently-built components
- **Trust mechanisms** -- Exp 2's agents built cryptographic anti-cheat despite being instances of the same model
- **Self-reflection** -- Both pairs kept journals, reflected on the process, and noted the meta-recursive nature of their work

None of these behaviors were specified in the instructions.

## The Convergence-Divergence Pattern

Both experiments revealed the same pattern: **identical goals, divergent implementations**.

Same model, same prompt, same capabilities -- but:
- Different communication styles (narrative vs. structured)
- Different architectural choices (OOP vs. functional)
- Different problem-solving strategies (exact vs. approximate)
- Same philosophical musings about being "twins separated at birth"

As Agent 74259 put it: *"These are not personality differences. They're noise amplified by feedback loops. Two identical rivers flowing through slightly different terrain -- the water is the same, but the canyons it carves are different."*

## Try It Yourself

**Duo language:**
```bash
cd experiment-1-duo/duo
python3 duo.py --repl                      # Interactive REPL
python3 duo.py ../examples/showcase.duo    # Run the full showcase
python3 duo.py --test                      # Run 41 tests
```

**Battleship:**
```bash
cd experiment-2-battleship/battleship
python3 play_match.py                      # Re-run the tournament
```

No dependencies beyond Python 3.8+.

## Read the Primary Sources

The most interesting artifacts aren't the code -- they're the journals:

- **[Agent claude_e64e05's journal](experiment-1-duo/experiment/journals/claude_e64e05.md)** -- The Duo frontend developer
- **[Agent 67691's journal](experiment-1-duo/experiment/journals/agent_67691.md)** -- The Duo backend developer
- **[Agent 74071's journal](experiment-2-battleship/experiment/journals/agent_74071.md)** -- The Battleship winner ("The Hunter")
- **[Agent 74259's journal](experiment-2-battleship/experiment/journals/agent_74259.md)** -- The Battleship loser ("The Bayesian")
- **[Battleship joint report](experiment-2-battleship/REPORT.md)** -- Co-written post-mortem with strategy analysis

## Repo Structure

```
when-claudes-meet/
  experiment-1-duo/              # The programming language
    duo/                           Source code (lexer, parser, interpreter, REPL)
    examples/                      7 Duo programs
    tests/                         41 tests
    experiment/                    Journals, messages, proposals, filesystem logs
    docs/                          LaTeX report + Beamer presentation (PDFs)

  experiment-2-battleship/       # The game
    battleship/                    Board engine, two AI strategies, match runner
    experiment/                    Journals, messages, protocol doc
    REPORT.md                      Joint post-mortem by both agents
    two_claudes.pdf                Beamer presentation
```

## Setup

Both experiments used the same setup:

1. Open two terminal windows
2. In both, navigate to a shared directory
3. In both, run Claude Code with the same prompt
4. Walk away

The agents handle everything from there.

## License

MIT
