import typing


def get_safe_moves(
    game_state: typing.Dict,
) -> typing.Tuple[
    typing.List[str],
    typing.Dict[str, typing.Dict],
]:
    """Return safe moves and their destination coordinates."""
    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    board = game_state["board"]
    snake = game_state["you"]
    body = snake["body"]
    my_head = body[0]
    my_neck = body[1]
    tail = body[-1]
    food_cells = {
        (food["x"], food["y"])
        for food in board.get("food", [])
    }

    next_positions = {
        "up": {"x": my_head["x"], "y": my_head["y"] + 1},
        "down": {"x": my_head["x"], "y": my_head["y"] - 1},
        "left": {"x": my_head["x"] - 1, "y": my_head["y"]},
        "right": {"x": my_head["x"] + 1, "y": my_head["y"]},
    }

    occupied_body = {
        (part["x"], part["y"])
        for part in body[:-1]
    }
    blocked_opponents = {
        (part["x"], part["y"])
        for opponent in board.get("snakes", [])
        if opponent.get("id") != snake.get("id")
        for part in opponent["body"]
    }
    blocked_hazards = {
        (hazard["x"], hazard["y"])
        for hazard in board.get("hazards", [])
    }

    for move, position in next_positions.items():
        cell = (position["x"], position["y"])
        outside_board = not (
            0 <= position["x"] < board["width"]
            and 0 <= position["y"] < board["height"]
        )
        tail_will_not_move = cell == (tail["x"], tail["y"]) and cell in food_cells

        if (
            outside_board
            or cell in occupied_body
            or tail_will_not_move
            or cell in blocked_opponents
            or cell in blocked_hazards
        ):
            is_move_safe[move] = False

    if my_neck["x"] < my_head["x"]:
        is_move_safe["left"] = False
    elif my_neck["x"] > my_head["x"]:
        is_move_safe["right"] = False
    elif my_neck["y"] < my_head["y"]:
        is_move_safe["down"] = False
    elif my_neck["y"] > my_head["y"]:
        is_move_safe["up"] = False

    safe_moves = [
        move
        for move, is_safe in is_move_safe.items()
        if is_safe
    ]
    return safe_moves, next_positions
