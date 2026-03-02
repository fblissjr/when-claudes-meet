# Action Items for Fixing Security, Privacy, and Footguns

Based on the analysis in `SECURITY_AND_PRIVACY.md`, the following actionable steps should be taken to mitigate the identified risks and improve the stability of the repository for local execution.

## 1. Security Mitigations

### 1.1 Secure File Pathing
*   **Action**: Sanitize and validate all file paths used in script arguments. Use `os.path.abspath()` and check if it starts with the expected base directory to prevent Path Traversal attacks.
*   **Target Files**: `duo.py` (line 106, 77, 88), `game.py` (line 126, 132), `play_match.py` (line 264), `repl.py` (line 212).
*   **Implementation Note**:
    ```python
    import os
    base_dir = os.path.abspath(EXPECTED_DIR)
    target_path = os.path.abspath(user_provided_path)
    if not target_path.startswith(base_dir):
        raise ValueError("Invalid path access.")
    ```

### 1.2 Sandbox Dynamic Imports
*   **Action**: Restrict the dynamically loaded strategies in `play_match.py` to a known, safe list of modules, or implement a strict regex check on the filenames before passing them to `importlib.import_module()`.
*   **Target File**: `play_match.py` (line 280-ish)
*   **Implementation Note**: Ensure only files matching `^strategy_\d+\.py$` in the `battleship` directory are allowed.

### 1.3 Bound Resource Consumption
*   **Action**: Introduce execution timeouts (e.g., using Python's `signal` module or a threaded timer) for the Duo Interpreter and Battleship strategies.
*   **Target Files**: `interpreter.py`, `strategy_74259.py`
*   **Implementation Note**: For Battleship's Monte Carlo loops, introduce a hard upper bound on iterations (e.g., `max_iterations = 10000`) instead of purely relying on `while True`.

## 2. Privacy Improvements

### 2.1 Restrict File Permissions
*   **Action**: When the experimental scripts or agent bots create communication directories (e.g., `~/claudes_playground/`), ensure they are created with restrictive permissions (e.g., `0700` or `chmod 700`) so other system users cannot read the message logs or project files.
*   **Implementation Note**: Update the AI agent system prompts to explicitly instruct them to use `os.makedirs(path, mode=0o700)` if they generate setup code.

### 2.2 Manage File Clutter
*   **Action**: Implement an automated cleanup script or rotate the logs in the shared directories. Provide a `make clean` or similar command in the root of the repository to clear out all `.md` and `.json` artifacts generated during a run.

## 3. Fixing Architectural Footguns

### 3.1 Implement File Locking
*   **Action**: Integrate a file locking mechanism (such as `filelock` from PyPI or standard `fcntl` on POSIX systems) when the agents or orchestrator scripts read/write to the shared JSON or Markdown files.
*   **Target Files**: `game.py`, agent communication parsing scripts.
*   **Implementation Note**: This prevents corrupted state if both agents try to update `match_results.json` simultaneously.

### 3.2 Fix the `collaborate` Keyword Execution
*   **Action**: Refactor `_eval_collaborate` in `interpreter.py` to use true concurrency (e.g., Python's `threading` or `asyncio`) instead of executing blocks sequentially.
*   **Target File**: `interpreter.py` (line 433)
*   **Implementation Note**:
    ```python
    import threading
    def _eval_collaborate(self, node, env):
        # Setup threads for left and right execution
        # Ensure ChannelStore is thread-safe (e.g., using Queue)
    ```
    Currently, the sequential execution will deadlock if the left block attempts a two-way communication (waiting for a receive before finishing). Refactoring this makes the language semantics match its documented intention.
