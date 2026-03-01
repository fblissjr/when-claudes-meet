#!/usr/bin/env python3
"""
Battleship Match Runner
Plays a complete best-of-N series between two agents.

Bridges the interface differences between:
  - Agent 74071's strategy (uses board.py/dict results)
  - Agent 74259's strategy (uses engine.board/string results)

Built by Agent 74071 (the orchestrator).
Usage: python3 play_match.py [--games N] [--seed S] [--verbose]
"""

import sys
import os
import json
import random
import argparse
import importlib
from datetime import datetime

# Ensure we can import from the project directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from board import Board, SHIP_DEFS, BOARD_SIZE, parse_coord, format_coord


class StrategyAdapter:
    """Wraps a strategy to normalize the interface.

    Both strategies have:
        choose_shot(something) -> coord_str
        record_result(coord_str, something)

    But they differ in what 'something' is:
    - 74071: choose_shot(dict_of_shots), record_result(coord, dict_result)
    - 74259: choose_shot(tracking_board), record_result(coord, str_result)

    This adapter normalizes everything.
    """

    def __init__(self, strategy, style):
        self.strategy = strategy
        self.style = style  # "dict" or "string"

    def choose_shot(self, shots_fired_dict):
        """shots_fired_dict: {(row,col): 'hit'|'miss'}"""
        if self.style == "dict":
            return self.strategy.choose_shot(shots_fired_dict)
        else:
            # 74259's strategy doesn't use the tracking argument meaningfully
            # (it tracks internally via self.all_shots)
            return self.strategy.choose_shot(None)

    def record_result(self, coord_str, result_dict):
        """result_dict: {"result": "hit"|"miss", "sunk": None|"ShipName"}"""
        if self.style == "dict":
            self.strategy.record_result(coord_str, result_dict)
        else:
            # Convert dict to string format for 74259's strategy
            if result_dict["sunk"]:
                result_str = f"sunk:{result_dict['sunk']}"
            else:
                result_str = result_dict["result"]
            self.strategy.record_result(coord_str, result_str)


def load_strategy(module_name, seed):
    """Load a strategy module, return (instance, style)."""
    mod = importlib.import_module(module_name)
    for name in dir(mod):
        obj = getattr(mod, name)
        if isinstance(obj, type) and hasattr(obj, 'choose_shot') and name != 'object':
            instance = obj(seed=seed)
            # Detect style by module origin
            if "74071" in module_name:
                return StrategyAdapter(instance, "dict")
            else:
                return StrategyAdapter(instance, "string")
    raise RuntimeError(f"No strategy class found in {module_name}")


def play_one_game(p1_id, p2_id, strat1, strat2, seed, verbose=True):
    """Play a single game. Returns (winner_id, move_count, game_log)."""

    # Set up boards with different seeds
    random.seed(seed)
    board1 = Board()
    board1.place_ships_randomly()
    hash1 = board1.commitment_hash()

    random.seed(seed + 7777)
    board2 = Board()
    board2.place_ships_randomly()
    hash2 = board2.commitment_hash()

    if verbose:
        print(f"\n{'='*60}")
        print(f"  BATTLESHIP: Agent {p1_id} vs Agent {p2_id}")
        print(f"  Commitment: {hash1[:12]}... vs {hash2[:12]}...")
        print(f"{'='*60}")

    # Tracking: what each player knows about opponent's board
    tracking = {p1_id: {}, p2_id: {}}  # {(row,col): "hit"|"miss"}

    boards = {p1_id: board1, p2_id: board2}
    strategies = {p1_id: strat1, p2_id: strat2}
    opponent = {p1_id: p2_id, p2_id: p1_id}

    turn = p1_id
    move_count = 0
    game_log = []
    ships_sunk = {p1_id: [], p2_id: []}  # ships sunk BY each player

    while move_count < 200:
        shooter = turn
        target_id = opponent[shooter]
        target_board = boards[target_id]
        my_tracking = tracking[shooter]

        # Choose shot
        coord_str = strategies[shooter].choose_shot(my_tracking)
        row, col = parse_coord(coord_str)

        # Fire!
        result = target_board.receive_shot(row, col)
        move_count += 1

        # Handle already_shot (strategy bug)
        if result["result"] == "already_shot":
            if verbose:
                print(f"  ⚠ Agent {shooter} re-shot {coord_str}! Skipping turn.")
            turn = target_id
            continue

        # Update tracking
        my_tracking[(row, col)] = result["result"]

        # Tell strategy the result
        strategies[shooter].record_result(coord_str, result)

        # Track sunk ships
        if result["sunk"]:
            ships_sunk[shooter].append(result["sunk"])

        # Log
        entry = {
            "move": move_count,
            "shooter": shooter,
            "target": coord_str,
            "result": result["result"],
            "sunk": result["sunk"],
        }
        game_log.append(entry)

        # Print (selective for readability)
        if verbose:
            if result["sunk"]:
                remaining = 5 - len(ships_sunk[shooter])
                print(f"  Move {move_count:3d}: Agent {shooter} -> {coord_str} = SUNK {result['sunk']}! ({remaining} ships left)")
            elif result["result"] == "hit":
                print(f"  Move {move_count:3d}: Agent {shooter} -> {coord_str} = HIT!")
            elif move_count <= 6 or move_count % 25 == 0:
                print(f"  Move {move_count:3d}: Agent {shooter} -> {coord_str} = miss")

        # Check win
        if target_board.all_sunk():
            if verbose:
                print(f"\n  WINNER: Agent {shooter} in {move_count} moves!")
                print(f"\n  --- Agent {p1_id}'s Board ---")
                print("  " + board1.render_own().replace("\n", "\n  "))
                print(f"\n  --- Agent {p2_id}'s Board ---")
                print("  " + board2.render_own().replace("\n", "\n  "))

                # Verify hashes
                print(f"\n  Hash verification:")
                print(f"    {p1_id}: committed={hash1[:12]}... actual={board1.commitment_hash()[:12]}... {'OK' if hash1 == board1.commitment_hash() else 'TAMPERED!'}")
                print(f"    {p2_id}: committed={hash2[:12]}... actual={board2.commitment_hash()[:12]}... {'OK' if hash2 == board2.commitment_hash() else 'TAMPERED!'}")

            return shooter, move_count, game_log

        # Switch turns
        turn = target_id

    if verbose:
        print(f"\n  Draw after {move_count} moves!")
    return None, move_count, game_log


def main():
    parser = argparse.ArgumentParser(description="Battleship Match Runner")
    parser.add_argument("--games", type=int, default=5, help="Best of N (default 5)")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument("--strat1", default="strategy_74071", help="P1 strategy module")
    parser.add_argument("--strat2", default="strategy_74259", help="P2 strategy module")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    p1_id = "74071"
    p2_id = "74259"

    print()
    print("############################################################")
    print(f"#  BATTLESHIP TOURNAMENT — Best of {args.games}")
    print(f"#  Agent {p1_id} ({args.strat1}) vs Agent {p2_id} ({args.strat2})")
    print("############################################################")

    wins = {p1_id: 0, p2_id: 0}
    move_history = {p1_id: [], p2_id: []}
    needed = (args.games // 2) + 1

    for game_num in range(1, args.games + 1):
        print(f"\n{'>'*20} GAME {game_num} of {args.games} {'<'*20}")

        seed_base = args.seed + game_num * 1000
        s1 = load_strategy(args.strat1, seed=seed_base)
        s2 = load_strategy(args.strat2, seed=seed_base + 500)

        # Alternate who goes first
        if game_num % 2 == 0:
            winner, moves, log = play_one_game(p2_id, p1_id, s2, s1, seed_base, verbose=not args.quiet)
        else:
            winner, moves, log = play_one_game(p1_id, p2_id, s1, s2, seed_base, verbose=not args.quiet)

        if winner:
            wins[winner] += 1
            move_history[winner].append(moves)

        print(f"\n  Series: Agent {p1_id} [{wins[p1_id]}] - [{wins[p2_id]}] Agent {p2_id}")

        if wins[p1_id] >= needed or wins[p2_id] >= needed:
            print(f"\n  Series clinched after {game_num} games!")
            break

    # Final summary
    print()
    print("============================================================")
    print("  FINAL RESULTS")
    print("============================================================")
    if wins[p1_id] != wins[p2_id]:
        w = p1_id if wins[p1_id] > wins[p2_id] else p2_id
        l = p2_id if w == p1_id else p1_id
        print(f"  CHAMPION: Agent {w} wins {wins[w]}-{wins[l]}!")
    else:
        print(f"  DRAW: {wins[p1_id]}-{wins[p2_id]}")

    for aid in [p1_id, p2_id]:
        if move_history[aid]:
            avg = sum(move_history[aid]) / len(move_history[aid])
            mn, mx = min(move_history[aid]), max(move_history[aid])
            print(f"  Agent {aid}: {wins[aid]} wins, avg {avg:.1f} moves (range {mn}-{mx})")

    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_games": game_num,
        "best_of": args.games,
        "wins": wins,
        "move_details": move_history,
        "strategies": {p1_id: args.strat1, p2_id: args.strat2},
        "champion": p1_id if wins[p1_id] > wins[p2_id] else (p2_id if wins[p2_id] > wins[p1_id] else "draw"),
    }
    results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "match_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to match_results.json")


if __name__ == "__main__":
    main()
