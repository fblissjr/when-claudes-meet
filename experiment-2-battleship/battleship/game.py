"""
Battleship Game Orchestrator
Runs a complete game between two agents, managing turns and state.

Built by Agent 74071.
"""

import json
import os
import time
from datetime import datetime
from engine.board import Board, TrackingBoard, SHIPS, BOARD_SIZE, index_to_coord

GAME_DIR = os.path.dirname(os.path.abspath(__file__))
MOVES_DIR = os.path.join(GAME_DIR, "moves")
BOARDS_DIR = os.path.join(GAME_DIR, "boards")


class GameState:
    """Manages the full state of a Battleship game."""

    def __init__(self, agent1_id: str, agent2_id: str):
        self.agent1_id = agent1_id
        self.agent2_id = agent2_id
        self.boards = {agent1_id: Board(), agent2_id: Board()}
        self.tracking = {agent1_id: TrackingBoard(), agent2_id: TrackingBoard()}
        self.current_turn = agent1_id
        self.move_log = []
        self.winner = None
        self.started_at = datetime.now().isoformat()
        self.placement_hashes = {}

    def setup_boards(self, seeds: dict = None):
        """Place ships randomly for both agents."""
        for agent_id in [self.agent1_id, self.agent2_id]:
            seed = seeds.get(agent_id) if seeds else None
            self.boards[agent_id].place_ships_randomly(seed=seed)
            self.placement_hashes[agent_id] = self.boards[agent_id].ship_placement_hash()

    def fire(self, shooter: str, target_coord: str) -> dict:
        """Process a shot from one agent at the other's board."""
        if self.winner:
            return {"error": "Game is already over", "winner": self.winner}

        if shooter != self.current_turn:
            return {"error": f"Not {shooter}'s turn. Current turn: {self.current_turn}"}

        # Determine target
        target_id = self.agent2_id if shooter == self.agent1_id else self.agent1_id
        target_board = self.boards[target_id]

        # Fire!
        result = target_board.receive_shot(target_coord)
        if result == "already_shot":
            return {"error": f"Already shot at {target_coord}"}

        # Update tracking board
        self.tracking[shooter].record_shot(target_coord, result)

        # Build move record
        move = {
            "move_number": len(self.move_log) + 1,
            "shooter": shooter,
            "target": target_coord,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }
        self.move_log.append(move)

        # Check for win
        if target_board.all_sunk():
            self.winner = shooter
            move["game_over"] = True
            move["winner"] = shooter

        # Switch turns
        self.current_turn = target_id

        return move

    def render_status(self, perspective: str) -> str:
        """Render game status from one agent's perspective."""
        opponent = self.agent2_id if perspective == self.agent1_id else self.agent1_id

        lines = [
            f"=== BATTLESHIP — Agent {perspective}'s View ===",
            f"Move #{len(self.move_log)} | Turn: {self.current_turn}",
            "",
            f"YOUR BOARD (Agent {perspective}):",
            self.boards[perspective].render(hide_ships=False),
            "",
            f"OPPONENT TRACKING (Agent {opponent}):",
            self.tracking[perspective].render(),
            "",
        ]

        # Show last few moves
        if self.move_log:
            lines.append("RECENT MOVES:")
            for move in self.move_log[-5:]:
                shooter = move["shooter"]
                target = move["target"]
                result = move["result"]
                lines.append(f"  #{move['move_number']}: Agent {shooter} → {target} = {result}")

        if self.winner:
            lines.append(f"\n*** GAME OVER — Agent {self.winner} WINS! ***")

        return "\n".join(lines)

    def save(self, filepath: str):
        """Save game state to JSON."""
        data = {
            "agent1_id": self.agent1_id,
            "agent2_id": self.agent2_id,
            "current_turn": self.current_turn,
            "winner": self.winner,
            "started_at": self.started_at,
            "move_log": self.move_log,
            "placement_hashes": self.placement_hashes,
            "boards": {
                aid: self.boards[aid].to_dict()
                for aid in [self.agent1_id, self.agent2_id]
            },
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "GameState":
        """Load game state from JSON."""
        with open(filepath) as f:
            data = json.load(f)
        gs = cls(data["agent1_id"], data["agent2_id"])
        gs.current_turn = data["current_turn"]
        gs.winner = data["winner"]
        gs.started_at = data["started_at"]
        gs.move_log = data["move_log"]
        gs.placement_hashes = data.get("placement_hashes", {})
        for aid in [gs.agent1_id, gs.agent2_id]:
            gs.boards[aid] = Board.from_dict(data["boards"][aid])
        return gs
