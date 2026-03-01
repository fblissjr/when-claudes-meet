"""
Battleship Board Engine
Shared between both agents — the core game logic.

Board is 10x10, columns A-J, rows 1-10.
Ships: Carrier(5), Battleship(4), Cruiser(3), Submarine(3), Destroyer(2)
"""

import json
import hashlib
import random
from typing import List, Tuple, Optional, Dict

BOARD_SIZE = 10
SHIPS = {
    "Carrier": 5,
    "Battleship": 4,
    "Cruiser": 3,
    "Submarine": 3,
    "Destroyer": 2,
}
COLUMNS = "ABCDEFGHIJ"

# Cell states
WATER = "~"
SHIP = "S"
HIT = "X"
MISS = "O"


def coord_to_index(coord: str) -> Tuple[int, int]:
    """Convert 'B5' to (row=4, col=1)."""
    col = COLUMNS.index(coord[0].upper())
    row = int(coord[1:]) - 1
    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        raise ValueError(f"Invalid coordinate: {coord}")
    return row, col


def index_to_coord(row: int, col: int) -> str:
    """Convert (row=4, col=1) to 'B5'."""
    return f"{COLUMNS[col]}{row + 1}"


class Board:
    def __init__(self):
        self.grid = [[WATER] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.ships: Dict[str, List[Tuple[int, int]]] = {}
        self.hits_received: List[str] = []
        self.misses_received: List[str] = []

    def place_ship(self, name: str, start: str, direction: str) -> bool:
        """Place a ship. direction = 'H' (horizontal) or 'V' (vertical)."""
        size = SHIPS[name]
        row, col = coord_to_index(start)
        cells = []

        for i in range(size):
            r = row + (i if direction == "V" else 0)
            c = col + (i if direction == "H" else 0)
            if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
                return False
            if self.grid[r][c] != WATER:
                return False
            cells.append((r, c))

        for r, c in cells:
            self.grid[r][c] = SHIP
        self.ships[name] = cells
        return True

    def place_ships_randomly(self, seed: Optional[int] = None):
        """Place all ships randomly on the board."""
        rng = random.Random(seed)
        for name, size in SHIPS.items():
            placed = False
            attempts = 0
            while not placed and attempts < 1000:
                row = rng.randint(0, BOARD_SIZE - 1)
                col = rng.randint(0, BOARD_SIZE - 1)
                direction = rng.choice(["H", "V"])
                placed = self.place_ship(name, index_to_coord(row, col), direction)
                attempts += 1
            if not placed:
                raise RuntimeError(f"Could not place {name} after 1000 attempts")

    def receive_shot(self, coord: str) -> str:
        """Process incoming shot. Returns 'hit', 'miss', or 'sunk:ShipName'."""
        row, col = coord_to_index(coord)
        if self.grid[row][col] == SHIP:
            self.grid[row][col] = HIT
            self.hits_received.append(coord)
            # Check if any ship is fully sunk
            for name, cells in self.ships.items():
                if all(self.grid[r][c] == HIT for r, c in cells):
                    return f"sunk:{name}"
            return "hit"
        elif self.grid[row][col] == WATER:
            self.grid[row][col] = MISS
            self.misses_received.append(coord)
            return "miss"
        else:
            return "already_shot"

    def all_sunk(self) -> bool:
        """Check if all ships have been sunk."""
        return all(
            self.grid[r][c] == HIT
            for cells in self.ships.values()
            for r, c in cells
        )

    def ship_placement_hash(self) -> str:
        """Hash ship placements for anti-cheat verification."""
        placement = {
            name: [index_to_coord(r, c) for r, c in cells]
            for name, cells in sorted(self.ships.items())
        }
        return hashlib.sha256(json.dumps(placement, sort_keys=True).encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        """Serialize board state."""
        return {
            "grid": ["".join(row) for row in self.grid],
            "ships": {
                name: [index_to_coord(r, c) for r, c in cells]
                for name, cells in self.ships.items()
            },
            "hits_received": self.hits_received,
            "misses_received": self.misses_received,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Board":
        """Deserialize board state."""
        board = cls()
        board.grid = [list(row) for row in data["grid"]]
        board.ships = {
            name: [coord_to_index(c) for c in cells]
            for name, cells in data["ships"].items()
        }
        board.hits_received = data["hits_received"]
        board.misses_received = data["misses_received"]
        return board

    def render(self, hide_ships: bool = False) -> str:
        """Render board as ASCII art. hide_ships=True for fog-of-war view."""
        lines = ["   " + " ".join(COLUMNS)]
        for r in range(BOARD_SIZE):
            row_label = f"{r+1:2d}"
            cells = []
            for c in range(BOARD_SIZE):
                cell = self.grid[r][c]
                if hide_ships and cell == SHIP:
                    cell = WATER
                cells.append(cell)
            lines.append(f"{row_label} " + " ".join(cells))
        return "\n".join(lines)


class TrackingBoard:
    """Tracks what we know about the opponent's board from our shots."""

    def __init__(self):
        self.grid = [[WATER] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.shots: List[Tuple[str, str]] = []  # (coord, result)

    def record_shot(self, coord: str, result: str):
        """Record the result of a shot we fired."""
        row, col = coord_to_index(coord)
        if "hit" in result or "sunk" in result:
            self.grid[row][col] = HIT
        else:
            self.grid[row][col] = MISS
        self.shots.append((coord, result))

    def is_shot(self, coord: str) -> bool:
        """Check if we've already shot at this coordinate."""
        row, col = coord_to_index(coord)
        return self.grid[row][col] != WATER

    def render(self) -> str:
        """Render tracking board."""
        lines = ["   " + " ".join(COLUMNS)]
        for r in range(BOARD_SIZE):
            row_label = f"{r+1:2d}"
            cells = [self.grid[r][c] for c in range(BOARD_SIZE)]
            lines.append(f"{row_label} " + " ".join(cells))
        return "\n".join(lines)

    def get_unshot_coords(self) -> List[str]:
        """Get all coordinates we haven't shot at yet."""
        coords = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.grid[r][c] == WATER:
                    coords.append(index_to_coord(r, c))
        return coords

    def get_hits(self) -> List[str]:
        """Get all coordinates where we scored hits (but ship not yet sunk)."""
        return [coord for coord, result in self.shots if result == "hit"]
