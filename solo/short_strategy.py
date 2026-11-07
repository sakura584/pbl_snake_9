from collections import deque
import random
import typing

from .common import get_safe_moves


_DIRECTIONS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def _point(cell: typing.Dict) -> typing.Tuple[int, int]:
    """Convert a coordinate dictionary into an (x, y) tuple."""
    return cell["x"], cell["y"]


def _find_path_move(
    game_state: typing.Dict,
    safe_moves: typing.List[str],
    targets: typing.Set[typing.Tuple[int, int]],
    avoid_food: bool = False,
) -> typing.Optional[str]:
    """Return the first move on a safe BFS path to one of the targets."""
    board = game_state["board"]
    snake = game_state["you"]
    body = [_point(part) for part in snake["body"]]
    food = {
        _point(cell)
        for cell in board.get("food", [])
    }

    # The tail normally moves away this turn, so it is not blocked.
    blocked = set(body[:-1])
    blocked.update(
        _point(part)
        for opponent in board.get("snakes", [])
        if opponent.get("id") != snake.get("id")
        for part in opponent["body"]
    )
    blocked.update(_point(cell) for cell in board.get("hazards", []))
    if avoid_food:
        blocked.update(food)

    queue = deque([(body[0], None)])
    visited = {body[0]}

    while queue:
        cell, first_move = queue.popleft()

        if cell in targets and first_move is not None:
            return first_move

        for move, (dx, dy) in _DIRECTIONS.items():
            if first_move is None and move not in safe_moves:
                continue

            target = cell[0] + dx, cell[1] + dy
            inside_board = (
                0 <= target[0] < board["width"]
                and 0 <= target[1] < board["height"]
            )
            if (
                inside_board
                and target not in blocked
                and target not in visited
            ):
                visited.add(target)
                queue.append((target, first_move or move))

    return None


def move_short(game_state: typing.Dict) -> typing.Dict:
    """Use food-first movement, then follow the tail for snakes shorter than 12."""
    safe_moves, _ = get_safe_moves(game_state)

    if not safe_moves:
        print(
            f"MOVE {game_state['turn']}: "
            "No safe moves detected! Moving down"
        )
        return {"move": "down"}

    snake = game_state["you"]

    # When health is low, try to reach food before following the tail.
    if snake["health"] <= 13:
        food = {
            _point(cell)
            for cell in game_state["board"].get("food", [])
        }
        food_move = _find_path_move(game_state, safe_moves, food)
        if food_move is not None:
            print(f"MOVE {game_state['turn']}: {food_move}")
            return {"move": food_move}

    # Otherwise, follow the current tail while avoiding food so that the
    # snake does not grow unexpectedly during the tail-chasing loop.
    tail = _point(snake["body"][-1])
    tail_move = _find_path_move(
        game_state,
        safe_moves,
        {tail},
        avoid_food=True,
    )
    if tail_move is not None:
        print(f"MOVE {game_state['turn']}: {tail_move}")
        return {"move": tail_move}

    # If no path to the food or tail exists, keep the snake alive randomly.
    next_move = random.choice(safe_moves)
    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}
