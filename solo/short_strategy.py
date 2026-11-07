import random
import typing

from .common import get_safe_moves


def move_short(game_state: typing.Dict) -> typing.Dict:
    """Temporary strategy for snakes shorter than 12 cells."""
    safe_moves, _ = get_safe_moves(game_state)

    if not safe_moves:
        print(
            f"MOVE {game_state['turn']}: "
            "No safe moves detected! Moving down"
        )
        return {"move": "down"}

    next_move = random.choice(safe_moves)
    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}
