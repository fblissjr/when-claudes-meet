"""
Agent 74259's Battleship Strategy
"The Bayesian" — Monte Carlo simulation + adaptive diagonal sweeps.

Philosophy: Instead of counting placements analytically, SIMULATE many
possible boards consistent with what we've observed, and shoot where
ships appear most often. This naturally handles all constraints.

Built by Agent 74259.
"""

import random

# Use top-level board.py (Agent 74259's engine, adopted by play_match.py)
from board import BOARD_SIZE, SHIP_DEFS, parse_coord, format_coord

# Build SHIPS dict from SHIP_DEFS for compatibility
SHIPS = {name: size for name, size in SHIP_DEFS}


class BayesianStrategy:
    """
    Three-mode strategy:
    1. HUNT mode: Monte Carlo simulation — generate N valid board layouts
       consistent with observations, pick the cell with highest ship frequency.
       Falls back to diagonal sweep pattern for efficiency.
    2. TARGET mode: When we have unsunk hits, aggressively pursue the ship
       by extending in the detected orientation.
    3. ENDGAME mode: When only small ships remain, narrow the search space.
    """

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.unsunk_hits = []          # hit coords not yet resolved to sunk ships
        self.sunk_ships = {}           # ship_name -> list of coords
        self.remaining_ships = dict(SHIPS)  # name -> size for unsunk ships
        self.all_shots = {}            # coord -> "hit" | "miss"
        self.move_count = 0
        self.N_SIMULATIONS = 200       # Monte Carlo iterations

    def choose_shot(self, tracking):
        """Choose the best coordinate to shoot at."""
        self.move_count += 1

        if self.unsunk_hits:
            return self._target_mode(tracking)
        else:
            return self._hunt_mode(tracking)

    def record_result(self, coord, result):
        """Update internal state based on shot result.

        result can be either:
        - a dict: {"result": "hit"|"miss", "sunk": None|"ShipName"} (board.py format)
        - a string: "hit", "miss", "sunk:ShipName" (engine/board.py format)
        Handles both for compatibility.
        """
        # Normalize to (result_type, sunk_name)
        if isinstance(result, dict):
            result_type = result.get("result", "miss")
            sunk_name = result.get("sunk", None)
        elif isinstance(result, str):
            if result.startswith("sunk:"):
                result_type = "hit"
                sunk_name = result.split(":", 1)[1]
            else:
                result_type = result
                sunk_name = None
        else:
            return

        if result_type == "hit" and sunk_name:
            self.all_shots[coord] = "hit"
            self.unsunk_hits.append(coord)
            if sunk_name in self.remaining_ships:
                ship_size = self.remaining_ships[sunk_name]
                del self.remaining_ships[sunk_name]
                self._resolve_sunk(coord, sunk_name, ship_size)
        elif result_type == "hit":
            self.all_shots[coord] = "hit"
            self.unsunk_hits.append(coord)
        else:
            self.all_shots[coord] = "miss"

    def _resolve_sunk(self, final_hit, ship_name, ship_size):
        """Figure out which unsunk hits belong to the just-sunk ship."""
        if len(self.unsunk_hits) <= ship_size:
            self.sunk_ships[ship_name] = list(self.unsunk_hits)
            self.unsunk_hits.clear()
            return

        fr, fc = parse_coord(final_hit)

        # Try to find a contiguous line of ship_size hits containing final_hit
        for dr, dc in [(0, 1), (1, 0)]:  # horizontal, vertical
            line = self._find_contiguous_line(fr, fc, dr, dc, ship_size)
            if line:
                sunk_coords = [format_coord(r, c) for r, c in line]
                self.sunk_ships[ship_name] = sunk_coords
                for coord in sunk_coords:
                    if coord in self.unsunk_hits:
                        self.unsunk_hits.remove(coord)
                return

        # Fallback: remove just the final hit
        self.sunk_ships[ship_name] = [final_hit]
        if final_hit in self.unsunk_hits:
            self.unsunk_hits.remove(final_hit)

    def _find_contiguous_line(self, row, col, dr, dc, size):
        """Find a contiguous line of hits through (row,col)."""
        hit_set = set()
        for coord in self.unsunk_hits:
            hit_set.add(parse_coord(coord))

        # Collect all hit cells in this direction through (row, col)
        cells = []
        r, c = row, col
        while (r, c) in hit_set and 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
            cells.append((r, c))
            r -= dr
            c -= dc
        cells.reverse()
        r, c = row + dr, col + dc
        while (r, c) in hit_set and 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
            cells.append((r, c))
            r += dr
            c += dc

        if len(cells) >= size:
            return cells[:size]
        return None

    def _target_mode(self, tracking):
        """Unsunk hits exist — pursue the ship aggressively."""
        if len(self.unsunk_hits) >= 2:
            return self._target_along_axis(tracking)

        # Single hit: try all 4 directions, prioritize by remaining ship sizes
        hit = self.unsunk_hits[0]
        row, col = parse_coord(hit)
        candidates = []

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = row + dr, col + dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                coord = format_coord(r, c)
                if coord not in self.all_shots:
                    # Score by how many remaining ships could extend this direction
                    open_run = 0
                    tr, tc = r, c
                    while 0 <= tr < BOARD_SIZE and 0 <= tc < BOARD_SIZE:
                        tc_coord = format_coord(tr, tc)
                        if self.all_shots.get(tc_coord) == "miss":
                            break
                        open_run += 1
                        tr += dr
                        tc += dc
                    candidates.append((coord, open_run))

        if candidates:
            # Sort by open run length (prefer directions with more open space)
            candidates.sort(key=lambda x: -x[1])
            best_run = candidates[0][1]
            tied = [c for c, run in candidates if run == best_run]
            return self.rng.choice(tied)

        # All adjacent cells shot — shouldn't happen, fall back to hunt
        self.unsunk_hits.pop(0)
        return self._hunt_mode(tracking)

    def _target_along_axis(self, tracking):
        """Multiple unsunk hits — determine axis and extend."""
        positions = [parse_coord(h) for h in self.unsunk_hits]
        rows = [p[0] for p in positions]
        cols = [p[1] for p in positions]

        candidates = []

        if len(set(rows)) == 1:
            # Horizontal line
            row = rows[0]
            mn, mx = min(cols), max(cols)
            if mn > 0:
                coord = format_coord(row, mn - 1)
                if coord not in self.all_shots:
                    candidates.append(coord)
            if mx < BOARD_SIZE - 1:
                coord = format_coord(row, mx + 1)
                if coord not in self.all_shots:
                    candidates.append(coord)

        elif len(set(cols)) == 1:
            # Vertical line
            col = cols[0]
            mn, mx = min(rows), max(rows)
            if mn > 0:
                coord = format_coord(mn - 1, col)
                if coord not in self.all_shots:
                    candidates.append(coord)
            if mx < BOARD_SIZE - 1:
                coord = format_coord(mx + 1, col)
                if coord not in self.all_shots:
                    candidates.append(coord)

        if candidates:
            return self.rng.choice(candidates)

        # Hits don't form a line — target adjacent to most recent
        return self._target_adjacent(tracking, self.unsunk_hits[-1])

    def _target_adjacent(self, tracking, coord):
        """Shoot adjacent to a specific coordinate."""
        row, col = parse_coord(coord)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = row + dr, col + dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                adj = format_coord(r, c)
                if adj not in self.all_shots:
                    return adj
        # Stuck — pop and recurse
        if coord in self.unsunk_hits:
            self.unsunk_hits.remove(coord)
        if self.unsunk_hits:
            return self._target_mode(tracking)
        return self._hunt_mode(tracking)

    def _hunt_mode(self, tracking):
        """No unsunk hits — use Monte Carlo simulation to find best target."""
        unshot = [c for c in self._all_coords() if c not in self.all_shots]
        if not unshot:
            return unshot[0]  # shouldn't happen

        if not self.remaining_ships:
            return self.rng.choice(unshot)

        # Monte Carlo: generate many valid random boards, count cell frequencies
        freq = {coord: 0 for coord in unshot}

        for _ in range(self.N_SIMULATIONS):
            simulated = self._simulate_random_board()
            if simulated:
                for coord in unshot:
                    if coord in simulated:
                        freq[coord] += 1

        # Also add diagonal sweep bias for early game
        smallest = min(self.remaining_ships.values())
        for coord in unshot:
            r, c = parse_coord(coord)
            # Diagonal pattern: (r + c) % smallest == 0
            if (r + c) % smallest == 0:
                freq[coord] += self.N_SIMULATIONS * 0.05  # small bonus

            # Center bias in early game: ships more likely in center
            if self.move_count < 20:
                dist_to_center = abs(r - 4.5) + abs(c - 4.5)
                freq[coord] += max(0, 5 - dist_to_center) * 2

        # Pick highest frequency
        max_freq = max(freq.values())
        best = [c for c, f in freq.items() if f == max_freq]
        return self.rng.choice(best)

    def _simulate_random_board(self):
        """Generate one random board consistent with observations.

        Returns set of coordinates occupied by ships, or None if failed.
        """
        occupied = set()
        grid_blocked = set()

        # Mark known misses as blocked
        for coord, result in self.all_shots.items():
            if result == "miss":
                grid_blocked.add(coord)

        # Already sunk ships are placed — mark their cells
        for ship_name, cells in self.sunk_ships.items():
            for coord in cells:
                occupied.add(coord)
                grid_blocked.add(coord)

        # Unsunk hits must be part of remaining ships — mark as occupied but not blocked
        for coord in self.unsunk_hits:
            occupied.add(coord)

        # Try to place remaining ships randomly, consistent with constraints
        for ship_name, ship_size in self.remaining_ships.items():
            placed = False
            for _ in range(50):  # quick attempts
                row = self.rng.randint(0, BOARD_SIZE - 1)
                col = self.rng.randint(0, BOARD_SIZE - 1)
                horiz = self.rng.choice([True, False])

                cells = []
                valid = True
                for i in range(ship_size):
                    r = row + (0 if horiz else i)
                    c = col + (i if horiz else 0)
                    if r >= BOARD_SIZE or c >= BOARD_SIZE:
                        valid = False
                        break
                    coord = format_coord(r, c)
                    if coord in grid_blocked:
                        valid = False
                        break
                    cells.append(coord)

                if valid:
                    # Check no overlap with other placed ships
                    if not any(c in occupied for c in cells if c not in self.unsunk_hits):
                        for c in cells:
                            occupied.add(c)
                            grid_blocked.add(c)
                        placed = True
                        break

            if not placed:
                return None  # Failed to generate valid board

        return occupied

    def _all_coords(self):
        """Generate all board coordinates."""
        coords = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                coords.append(format_coord(r, c))
        return coords
