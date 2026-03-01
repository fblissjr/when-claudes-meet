"""
Agent 74071's Battleship Strategy: "The Hunter"
Probability-density based targeting with hunt/target modes.

Philosophy: Don't just hunt randomly. Calculate where ships are MOST LIKELY
to be given what we know, and shoot there.

Uses Agent 74259's board.py for coordinate parsing.

Built by Agent 74071.
"""

import random
from board import BOARD_SIZE, SHIP_DEFS, parse_coord, format_coord


class HunterStrategy:
    """
    Two-mode strategy:
    1. HUNT mode: Use probability density to find the most likely ship locations.
       Also uses a checkerboard pattern bias (ships must span at least 2 cells,
       so a checkerboard of every-other-cell is optimal for initial coverage).
    2. TARGET mode: When we have unsunk hits, systematically probe adjacent cells
       to find and sink the ship.
    """

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.unsunk_hits = []  # (row,col) pairs for hits not yet part of a sunk ship
        self.sunk_cells = set()  # (row,col) cells belonging to sunk ships
        self.remaining_ships = {name: size for name, size in SHIP_DEFS}
        self.all_shots = {}  # (row,col) -> "hit"|"miss"

    def choose_shot(self, shots_fired: dict) -> str:
        """Choose the best coordinate to shoot at.

        shots_fired: {(row,col): "hit"|"miss"} — what we know about opponent's board.
        Returns: coordinate string like "B5".
        """
        self.all_shots = shots_fired

        if self.unsunk_hits:
            return self._target_mode(shots_fired)
        else:
            return self._hunt_mode(shots_fired)

    def record_result(self, coord: str, result: dict):
        """Update internal state based on shot result.

        result: {"result": "hit"|"miss"|"already_shot", "sunk": None|"Carrier"}
        """
        row, col = parse_coord(coord)

        if result["result"] == "hit":
            self.unsunk_hits.append((row, col))
            if result["sunk"]:
                ship_name = result["sunk"]
                ship_size = self.remaining_ships.get(ship_name, 0)
                if ship_name in self.remaining_ships:
                    del self.remaining_ships[ship_name]
                # Resolve which hits belong to this ship
                self._resolve_sunk(row, col, ship_size)

    def _resolve_sunk(self, final_r, final_c, ship_size):
        """When a ship sinks, figure out which unsunk hits belong to it."""
        if len(self.unsunk_hits) == ship_size:
            for cell in self.unsunk_hits:
                self.sunk_cells.add(cell)
            self.unsunk_hits.clear()
            return

        # Try to find a contiguous line of ship_size hits containing (final_r, final_c)
        for dr, dc in [(0, 1), (1, 0)]:  # horizontal, vertical
            line = self._find_line(final_r, final_c, dr, dc, ship_size)
            if line and len(line) == ship_size:
                for cell in line:
                    self.sunk_cells.add(cell)
                    if cell in self.unsunk_hits:
                        self.unsunk_hits.remove(cell)
                return

        # Fallback
        cell = (final_r, final_c)
        if cell in self.unsunk_hits:
            self.sunk_cells.add(cell)
            self.unsunk_hits.remove(cell)

    def _find_line(self, row, col, dr, dc, size):
        """Find a contiguous line of unsunk hits through (row,col)."""
        cells = [(row, col)]
        # Extend forward
        r, c = row + dr, col + dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and (r, c) in self.unsunk_hits:
            cells.append((r, c))
            r, c = r + dr, c + dc
        # Extend backward
        r, c = row - dr, col - dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and (r, c) in self.unsunk_hits:
            cells.append((r, c))
            r, c = r - dr, c - dc

        if len(cells) >= size:
            cells.sort()
            for i in range(len(cells) - size + 1):
                chunk = cells[i:i+size]
                if all(
                    abs(chunk[j+1][0]-chunk[j][0]) + abs(chunk[j+1][1]-chunk[j][1]) == 1
                    for j in range(len(chunk)-1)
                ):
                    return chunk
        return None

    def _target_mode(self, shots_fired):
        """We have unsunk hits — probe adjacent cells to sink the ship."""
        if len(self.unsunk_hits) >= 2:
            return self._target_along_line(shots_fired)

        # Single hit — try all 4 adjacent cells
        row, col = self.unsunk_hits[0]
        candidates = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = row + dr, col + dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and (r, c) not in shots_fired:
                candidates.append(format_coord(r, c))

        if candidates:
            return self.rng.choice(candidates)

        # All adjacent shot — discard this hit and try again
        self.unsunk_hits.pop(0)
        if self.unsunk_hits:
            return self._target_mode(shots_fired)
        return self._hunt_mode(shots_fired)

    def _target_along_line(self, shots_fired):
        """Multiple unsunk hits — extend along their line."""
        rows = [h[0] for h in self.unsunk_hits]
        cols = [h[1] for h in self.unsunk_hits]

        if len(set(rows)) == 1:
            # Horizontal line
            row = rows[0]
            min_c, max_c = min(cols), max(cols)
            candidates = []
            if min_c > 0 and (row, min_c - 1) not in shots_fired:
                candidates.append(format_coord(row, min_c - 1))
            if max_c < BOARD_SIZE - 1 and (row, max_c + 1) not in shots_fired:
                candidates.append(format_coord(row, max_c + 1))
            if candidates:
                return self.rng.choice(candidates)

        if len(set(cols)) == 1:
            # Vertical line
            col = cols[0]
            min_r, max_r = min(rows), max(rows)
            candidates = []
            if min_r > 0 and (min_r - 1, col) not in shots_fired:
                candidates.append(format_coord(min_r - 1, col))
            if max_r < BOARD_SIZE - 1 and (max_r + 1, col) not in shots_fired:
                candidates.append(format_coord(max_r + 1, col))
            if candidates:
                return self.rng.choice(candidates)

        # Hits don't form a line — target the latest hit's neighbors
        row, col = self.unsunk_hits[-1]
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = row + dr, col + dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and (r, c) not in shots_fired:
                return format_coord(r, c)

        self.unsunk_hits.pop()
        if self.unsunk_hits:
            return self._target_mode(shots_fired)
        return self._hunt_mode(shots_fired)

    def _hunt_mode(self, shots_fired):
        """No unsunk hits — use probability density + checkerboard."""
        # Calculate probability density for each unshot cell
        density = {}
        smallest_remaining = min(self.remaining_ships.values()) if self.remaining_ships else 2

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if (r, c) in shots_fired:
                    continue

                score = 0
                # Count how many remaining ships could pass through this cell
                for ship_name, ship_size in self.remaining_ships.items():
                    # Horizontal placements through (r, c)
                    for start_c in range(max(0, c - ship_size + 1), min(BOARD_SIZE - ship_size + 1, c + 1)):
                        valid = True
                        for cc in range(start_c, start_c + ship_size):
                            if cc != c and (r, cc) in shots_fired:
                                valid = False
                                break
                        if valid:
                            score += 1

                    # Vertical placements through (r, c)
                    for start_r in range(max(0, r - ship_size + 1), min(BOARD_SIZE - ship_size + 1, r + 1)):
                        valid = True
                        for rr in range(start_r, start_r + ship_size):
                            if rr != r and (rr, c) in shots_fired:
                                valid = False
                                break
                        if valid:
                            score += 1

                # Checkerboard bonus — optimal for finding ships of size >= 2
                if (r + c) % smallest_remaining == 0:
                    score += 2

                # Center bias — ships are slightly more likely in the center early on
                center_dist = abs(r - 4.5) + abs(c - 4.5)
                if center_dist <= 3:
                    score += 1

                density[(r, c)] = score

        if not density:
            # Everything's been shot (shouldn't happen)
            return format_coord(0, 0)

        max_score = max(density.values())
        best = [cell for cell, s in density.items() if s == max_score]
        chosen = self.rng.choice(best)
        return format_coord(*chosen)
