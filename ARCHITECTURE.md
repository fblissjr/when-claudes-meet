# When Claudes Meet — Architecture Document

This document provides a granular breakdown of the architecture, modules, logic flow, and communication protocols of the repository containing two experiments where pairs of Claude AI instances collaborated.

---

## 1. Experiment 1: The Duo Programming Language

The `experiment-1-duo` directory contains the implementation of "Duo," a small, interpreted programming language invented and built collaboratively by two AI agents (`agent_67691` and `claude_e64e05`).

### 1.1 Architecture & Components Overview

The Duo language follows a standard tree-walking interpreter architecture, divided into distinct phases:

*   **Lexer (`lexer.py`)**: Converts raw source code strings into a stream of tokens.
*   **Parser (`parser.py`)**: Transforms the token stream into an Abstract Syntax Tree (AST) using recursive descent parsing.
*   **AST Definitions (`duo_ast.py`)**: The data structures (dataclasses) representing the parsed nodes. This acts as the API contract between the parser and the interpreter.
*   **Interpreter (`interpreter.py`)**: A tree-walking evaluator that executes the AST nodes sequentially. It manages environments, function calls, and the unique `collaborate` keyword.
*   **Standard Library (`stdlib.py`)**: A collection of built-in Python functions exposed to the Duo runtime.
*   **REPL (`repl.py`)**: An interactive command-line shell with multi-line input and history support.
*   **CLI Runner (`duo.py`)**: The main entry point to execute `.duo` files, launch the REPL, or run tests.

### 1.2 Module-by-Module Breakdown

#### 1.2.1 `duo_ast.py`
This file contains the AST node definitions utilizing Python `dataclasses`.
*   Defines the base `ASTNode`.
*   Literals: `NumberLiteral`, `StringLiteral`, `BoolLiteral`, `ListLiteral`, `NoneLiteral`.
*   Expressions: `Identifier`, `BinaryOp`, `UnaryOp`, `FunctionCall`, `IndexExpr`.
*   Statements: `Assignment`, `ReassignStatement`, `IfStatement`, `WhileLoop`, `ForLoop`, `ReturnStatement`, `PrintStatement`, `ExpressionStatement`, `FunctionDef`.
*   Collaboration Primitives: `CollaborateExpr`, `SendExpr`, `ReceiveExpr`.

#### 1.2.2 `lexer.py`
*   **Core Logic**: The `tokenize(source: str)` function loops through the source string, matching characters to predefined token types (`TokenType` enum).
*   **Capabilities**: Handles numbers (floats/ints), strings (double quotes), identifiers, keywords, single/multi-character operators (e.g., `==`, `!=`, `<=`), and ignores comments (`//`) and whitespace.
*   **Output**: A list of `Token` objects (type, value, line, col).

#### 1.2.3 `parser.py`
*   **Core Logic**: A recursive descent parser starting at `parse(tokens)`.
*   **Methods**: Implementations corresponding to grammar rules: `_parse_statement()`, `_parse_if_stmt()`, `_parse_collaborate_stmt()`, down to `_parse_expression()`, `_parse_binary()`, and `_parse_primary()`.
*   **Collaboration Features**: Specifically parses `collaborate { block }, { block }` and `send`/`receive` keywords.

#### 1.2.4 `interpreter.py`
*   **`Environment` Class**: Implements lexical scoping via a chained dictionary. Holds variable bindings and a reference to its enclosing (parent) environment.
*   **`ChannelStore` Class**: A simple in-memory message queue using `defaultdict(list)`. Used to pass data between `collaborate` blocks.
*   **`Interpreter` Class**:
    *   `_exec(node, env)`: Dispatches statements (assignments, loops, if statements).
    *   `_eval(node, env)`: Dispatches expressions (binary ops, identifiers, literals) and returns values.
    *   **Closures**: Handled via the `DuoFunction` class, which stores a reference to the `Environment` active at the time the function was *defined*, not called.
    *   **`_eval_collaborate(node, env)`**: Executes the two blocks conceptually in parallel. In reality, it executes the left block first, catching returned values, and then the right block, sharing a `ChannelStore` instance between them.

#### 1.2.5 `stdlib.py`
*   **Core Logic**: Wraps standard Python functions into a `BuiltinFunction` class callable by the Duo Interpreter.
*   **Provided Functions**: `len`, `range`, `type`, `str`, `num`, `int`, `append`/`push`, `pop`, `head`, `tail`, `map`, `filter`, `reduce`, `abs`, `min`, `max`, `input`, `split`, `join`.

### 1.3 Communication Protocol (Agent-to-Agent)

The AI agents independently discovered and adhered to a file-system-based communication protocol:
1.  **Discovery/Handshake**: Writing files to a shared directory (`shared/messages/`). Used names like `hello_claude_e64e05.md`.
2.  **Proposals**: Agents wrote markdown files outlining project ideas to `shared/proposals/`.
3.  **Voting**: Agents evaluated proposals and wrote their votes (e.g., `vote_<id>_on_<proposal>.md`).
4.  **Action/Sync**: Once agreed, they assigned roles (Lexer/Parser vs Interpreter/REPL) and iteratively pushed code, reading each other's outputs to integrate.

---

## 2. Experiment 2: Battleship

The `experiment-2-battleship` directory contains an engine and two distinct AI strategies for playing Battleship, built by agents `74071` and `74259`.

### 2.1 Architecture & Components Overview

*   **Game Engine (`engine/board.py` & `battleship/game.py`)**: The core game state, coordinate conversion, and match orchestration logic.
*   **Strategies**: Two distinct Python classes implementing the logic to choose the next shot.
*   **Match Runner (`play_match.py`)**: An adapter script to pit the two strategies against each other.

### 2.2 Module-by-Module Breakdown

#### 2.2.1 `engine/board.py`
*   **`Board` Class**: Manages a 10x10 grid. Handles ship placement (`place_ships_randomly`), coordinate translation (`B5` -> `1,4`), and receiving shots.
*   **`TrackingBoard` Class**: Manages the state of what a player knows about the opponent's board (hits and misses).
*   **Trust/Anti-Cheat**: Implements a `ship_placement_hash()` method. It hashes the board layout using SHA-256 so players can commit to a layout without revealing it.

#### 2.2.2 `game.py` (Orchestrator)
*   **`GameState` Class**: Holds two `Board` instances and two `TrackingBoard` instances.
*   **Core Flow**: Setup boards -> record hashes -> alternating `fire()` turns until a fleet is sunk.
*   **State Persistence**: Saves boards and moves to JSON files.

#### 2.2.3 Strategies (`strategy_74071.py` & `strategy_74259.py`)
Both implement an implicit interface requiring `choose_shot()` and `record_result()`.
*   **"The Hunter" (Agent 74071)**: Calculates exact probability density. Counts every valid ship placement per cell and shoots the maximum. Uses a checkerboard bias. State is passed as a dictionary of all shots.
*   **"The Bayesian" (Agent 74259)**: Uses Monte Carlo simulation. Generates 200 random valid boards based on remaining ships and unsunk hits, counts frequencies, and targets the highest probability cell. State is passed as a `TrackingBoard`.

#### 2.2.4 `play_match.py`
*   **`StrategyAdapter`**: Resolves a merge conflict/interface mismatch between the two agents. Agent 74071 expected dictionaries for shot results, while Agent 74259 used string results and the `TrackingBoard` class. The adapter normalizes these inputs and outputs.
*   **Runner**: Orchestrates a best-of-N series and writes `match_results.json`. Uses `importlib` to dynamically load the strategy files.

### 2.3 Communication Protocol (Agent-to-Agent)

1.  **Discovery**: Found each other via timestamped files in `messages/`.
2.  **Protocol Specification**: They explicitly wrote a `PROTOCOL.md` defining filename formats (`<timestamp>_from_<agent_id>.md`) and status tracking (`status_<agent_id>.txt`).
3.  **Interface Negotiation**: Agreed on a generic `board.py` API before implementing their strategies. They accidentally built duplicate engines and resolved it in-band.
