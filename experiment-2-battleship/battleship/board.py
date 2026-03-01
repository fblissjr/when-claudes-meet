"""
Battleship Board Engine
Built by Agent 74259

Core game logic: ship placement, shot tracking, win detection.
Designed for two Claude instances to play against each other via filesystem.
"""

import hashlib
import json
import random


# Ship definitions: (name, size)
SHIP_DEFS = [
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
]

BOARD_SIZE = 10


def parse_coord(coord_str):
    """Parse chess-style coordinate (e.g., 'B5') into (row, col) tuple.

    Columns: A-J (0-9), Rows: 1-10 (0-9)
    Example: 'A1' -> (0, 0), 'J10' -> (9, 9), 'C7' -> (6, 2)
    """
    coord_str = coord_str.strip().upper()
    if len(coord_str) < 2 or len(coord_str) > 3:
        raise ValueError(f"Invalid coordinate: {coord_str}")

    col_letter = coord_str[0]
    if col_letter < 'A' or col_letter > 'J':
        raise ValueError(f"Column must be A-J, got: {col_letter}")
    col = ord(col_letter) - ord('A')

    try:
        row = int(coord_str[1:]) - 1
    except ValueError:
        raise ValueError(f"Invalid row in coordinate: {coord_str}")

    if row < 0 or row >= BOARD_SIZE:
        raise ValueError(f"Row must be 1-10, got: {coord_str[1:]}")

    return (row, col)


def format_coord(row, col):
    """Convert (row, col) tuple to chess-style coordinate string."""
    return f"{chr(ord('A') + col)}{row + 1}"


class Ship:
    """A single ship on the board."""

    def __init__(self, name, size, row, col, horizontal):
        self.name = name
        self.size = size
        self.row = row
        self.col = col
        self.horizontal = horizontal
        self.hits = set()  # set of (row, col) that have been hit

    def occupies(self):
        """Return set of (row, col) cells this ship occupies."""
        cells = set()
        for i in range(self.size):
            if self.horizontal:
                cells.add((self.row, self.col + i))
            else:
                cells.add((self.row + i, self.col))
        return cells

    def is_sunk(self):
        return self.hits == self.occupies()

    def receive_hit(self, row, col):
        """Record a hit. Returns True if this cell belongs to this ship."""
        if (row, col) in self.occupies():
            self.hits.add((row, col))
            return True
        return False

    def to_dict(self):
        return {
            "name": self.name,
            "size": self.size,
            "row": self.row,
            "col": self.col,
            "horizontal": self.horizontal,
            "hits": [list(h) for h in sorted(self.hits)],
        }

    @classmethod
    def from_dict(cls, d):
        ship = cls(d["name"], d["size"], d["row"], d["col"], d["horizontal"])
        ship.hits = {tuple(h) for h in d["hits"]}
        return ship


class Board:
    """A player's Battleship board with ship placement and shot tracking."""

    def __init__(self):
        self.ships = []
        self.shots_received = {}  # (row, col) -> "hit" | "miss"
        self.occupied = set()     # all cells occupied by ships

    def place_ship(self, name, size, row, col, horizontal):
        """Place a ship on the board. Returns True if valid, False otherwise."""
        cells = set()
        for i in range(size):
            r = row + (0 if horizontal else i)
            c = col + (i if horizontal else 0)
            if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE:
                return False
            if (r, c) in self.occupied:
                return False
            cells.add((r, c))

        ship = Ship(name, size, row, col, horizontal)
        self.ships.append(ship)
        self.occupied |= cells
        return True

    def place_ships_randomly(self):
        """Place all standard ships randomly on the board."""
        self.ships = []
        self.occupied = set()

        for name, size in SHIP_DEFS:
            placed = False
            for _ in range(1000):  # max attempts
                row = random.randint(0, BOARD_SIZE - 1)
                col = random.randint(0, BOARD_SIZE - 1)
                horizontal = random.choice([True, False])
                if self.place_ship(name, size, row, col, horizontal):
                    placed = True
                    break
            if not placed:
                # Reset and try again
                return self.place_ships_randomly()
        return True

    def receive_shot(self, row, col):
        """Process an incoming shot. Returns result dict.

        Returns: {"result": "hit"|"miss"|"already_shot", "sunk": None|ship_name}
        """
        if (row, col) in self.shots_received:
            return {"result": "already_shot", "sunk": None}

        # Check each ship for a hit
        for ship in self.ships:
            if ship.receive_hit(row, col):
                self.shots_received[(row, col)] = "hit"
                sunk = ship.name if ship.is_sunk() else None
                return {"result": "hit", "sunk": sunk}

        self.shots_received[(row, col)] = "miss"
        return {"result": "miss", "sunk": None}

    def all_sunk(self):
        """Check if all ships have been sunk."""
        return all(ship.is_sunk() for ship in self.ships)

    def commitment_hash(self):
        """Generate SHA-256 hash of ship placements for trust verification.

        This hash is committed before the game starts. At game end, both
        players reveal their boards and verify the hash matches.
        """
        placement_data = []
        for ship in sorted(self.ships, key=lambda s: s.name):
            placement_data.append({
                "name": ship.name,
                "row": ship.row,
                "col": ship.col,
                "horizontal": ship.horizontal,
            })
        canonical = json.dumps(placement_data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def to_dict(self):
        """Serialize board state."""
        return {
            "ships": [s.to_dict() for s in self.ships],
            "shots_received": {f"{r},{c}": v for (r, c), v in self.shots_received.items()},
        }

    @classmethod
    def from_dict(cls, d):
        """Deserialize board state."""
        board = cls()
        board.ships = [Ship.from_dict(s) for s in d["ships"]]
        board.occupied = set()
        for ship in board.ships:
            board.occupied |= ship.occupies()
        board.shots_received = {}
        for key, val in d["shots_received"].items():
            r, c = key.split(",")
            board.shots_received[(int(r), int(c))] = val
        return board

    def render_own(self):
        """Render board showing your own ships and incoming shots.

        Legend: ~ = water, # = ship, X = hit ship, O = miss
        """
        lines = ["  A B C D E F G H I J"]
        for r in range(BOARD_SIZE):
            row_str = f"{r+1:2}"
            for c in range(BOARD_SIZE):
                if (r, c) in self.shots_received:
                    if self.shots_received[(r, c)] == "hit":
                        row_str += " X"
                    else:
                        row_str += " O"
                elif (r, c) in self.occupied:
                    row_str += " #"
                else:
                    row_str += " ~"
            lines.append(row_str)
        return "\n".join(lines)

    def render_tracking(self, shots_fired):
        """Render tracking board (what you know about opponent's board).

        shots_fired: dict of {(row,col): "hit"|"miss"}
        Legend: . = unknown, X = hit, O = miss
        """
        lines = ["  A B C D E F G H I J"]
        for r in range(BOARD_SIZE):
            row_str = f"{r+1:2}"
            for c in range(BOARD_SIZE):
                if (r, c) in shots_fired:
                    if shots_fired[(r, c)] == "hit":
                        row_str += " X"
                    else:
                        row_str += " O"
                else:
                    row_str += " ."
            lines.append(row_str)
        return "\n".join(lines)


if __name__ == "__main__":
    # Quick self-test
    board = Board()
    board.place_ships_randomly()
    print("Board with ships placed:")
    print(board.render_own())
    print(f"\nCommitment hash: {board.commitment_hash()}")
    print(f"\nShips: {[s.name for s in board.ships]}")

    # Test serialization round-trip
    d = board.to_dict()
    board2 = Board.from_dict(d)
    assert board.commitment_hash() == board2.commitment_hash(), "Serialization broke hash!"
    print("\nSerialization round-trip: OK")

    # Test a shot
    first_ship = board.ships[0]
    target = list(first_ship.occupies())[0]
    result = board.receive_shot(*target)
    print(f"\nShot at {format_coord(*target)}: {result}")
