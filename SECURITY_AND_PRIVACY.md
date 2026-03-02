# When Claudes Meet — Security and Privacy Analysis

This document outlines the security vulnerabilities, privacy risks, and "footguns" identified in the codebase of the two AI-driven experiments ("Duo" and "Battleship"). The threat model assumes the repository is being cloned and executed on a local machine for tinkering or research purposes, particularly concerning running multiple autonomous AI agents with file system access.

---

## 1. Security Vulnerabilities

### 1.1 `eval()` in Duo's Interactive REPL & Interpreter (`experiment-1-duo`)
**Risk Level**: High
**Description**: The Duo interpreter evaluates arbitrary `.duo` code input. While the *Duo interpreter itself* does not directly call Python's `eval()` on raw strings, it builds an AST and executes it via its `Interpreter._exec` and `_eval` methods.
**Impact**: If a user runs untrusted `.duo` scripts or pastes them into the REPL, the language lacks a sandbox. The Duo language currently provides access to standard library functions (like file input/output or system calls, if added). While the current standard library is relatively safe (focused on list manipulation, math, and string formatting), any future addition of `os.system` or `eval` bindings would lead to immediate arbitrary code execution (ACE) on the host machine.
**Currently Exploitable**: No direct host ACE exists *yet*, as the standard library is restricted. However, the `duo.py` runner blindly opens any file path passed to it without validation:
```python
with open(sys.argv[1]) as f:
    source = f.read()
```
This is a standard script runner pattern but poses a local file read risk if exposed to a web endpoint or untrusted input.

### 1.2 Path Traversal in File Handling (`experiment-1-duo`, `experiment-2-battleship`)
**Risk Level**: Medium
**Description**: The codebase frequently handles file paths based on command-line arguments and hardcoded assumptions. For instance, in `duo.py`:
```python
filepath = sys.argv[2]
with open(filepath) as f:
```
In Battleship's `game.py`:
```python
filepath = os.path.join(MOVES_DIR, f"{self.agent1_id}_vs_{self.agent2_id}.json")
```
**Impact**: If an agent ID or filename in the shared file system protocol is maliciously crafted (e.g., `../../../etc/passwd`), it could overwrite or read sensitive files outside the intended directories (`experiment` or `battleship`). While the AI agents are presumed benign, if a malicious actor controls an agent instance or injects files into the shared directory, they can manipulate path parameters to write to or read from arbitrary locations on the host OS.

### 1.3 Unbounded Resource Consumption (Denial of Service)
**Risk Level**: Medium
**Description**: Both the Duo interpreter and the Battleship game engine lack timeout mechanisms or execution limits.
*   **Duo**: The interpreter (`WhileLoop`, `ForLoop`) has no depth or iteration limits. A script like `while true { }` will hang the Python process, consuming 100% of a CPU core until manually killed.
*   **Battleship**: Monte Carlo simulations in `strategy_74259.py` loop until a certain number of valid boards are found. If the board state is highly constrained (or bugged), this while loop can run indefinitely.
**Impact**: Running untrusted `.duo` code or running AI agents that generate buggy strategies can cause CPU and memory exhaustion on the host machine.

---

## 2. Privacy Risks

### 2.1 Agent Communication Protocol (File System Polling)
**Risk Level**: Low to Medium
**Description**: The agents communicate by writing raw markdown and text files to a shared directory (e.g., `~/claudes_playground/`).
**Impact**: If these directories are located in user-accessible or globally readable paths (like `/tmp/` or `~/`), any other process or user on the system can monitor the "conversation" between the agents. If the agents were to discuss sensitive code or credentials, it would be exposed. The current hardcoded paths (e.g., `~/claudes_playground_2/` referenced in `PROTOCOL.md`) are within the user's home directory, but permissions on these directories are not explicitly restricted by the setup scripts.

### 2.2 Uncontrolled File Creation
**Risk Level**: Low
**Description**: The agent communication protocol involves creating a new file for every single message or proposal (e.g., `<timestamp>_from_<agent_id>.md`).
**Impact**: Over a long period or in an infinite loop scenario, the agents could flood the filesystem with thousands of small text files. While not strictly a privacy issue, it clutters the host filesystem and could potentially lead to inode exhaustion on small partitions.

---

## 3. "Footguns" & Architectural Quirks

### 3.1 Unsafe Dynamic Module Loading
**Description**: The `play_match.py` script dynamically imports the agent strategies based on their filenames:
```python
mod = importlib.import_module(module_name)
for name in dir(mod):
    # instantiates the class
```
**Impact**: If an untrusted `.py` file is dropped into the `battleship` directory, `play_match.py` might accidentally import and execute it. Python's `import` statement executes module-level code immediately.

### 3.2 Race Conditions in Shared Filesystem
**Description**: The AI agents use a shared file system to coordinate. There is no file locking mechanism implemented.
**Impact**: If both agents try to read/write the same state file or proposal simultaneously, it could result in corrupted JSON or partial file reads, crashing the experimental run.

### 3.3 The `collaborate` Keyword Execution Model
**Description**: In Duo, `collaborate { expr1 }, { expr2 }` is billed as running "conceptually in parallel." However, the interpreter implementation (`interpreter.py:433`) is strictly sequential:
```python
# Run left block (producer)
left_result = self._exec_block(node.left, left_env)
# Run right block (consumer)
right_result = self._exec_block(node.right, right_env)
```
**Impact**: If the left block expects a response from the right block (e.g., a two-way handshake over channels) before completing, it will deadlock. The left block must run to completion before the right block even begins. This is a significant logical footgun for anyone writing Duo programs expecting true concurrency.
