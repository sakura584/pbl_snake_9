import typing

# 即死(壁激突 or 自分に突っ込む) 回避する方向を4方向から絞る
def get_safe_moves(
    game_state: typing.Dict,
) -> typing.Tuple[
    typing.List[str],
    typing.Dict[str, typing.Dict],
]:
    """Return safe moves and their destination coordinates."""
    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    my_head = game_state["you"]["body"][0]
    my_neck = game_state["you"]["body"][1]
    board_width = game_state["board"]["width"]
    board_height = game_state["board"]["height"]

    danger_map = [
        [0 for _ in range(board_width + 2)]
        for _ in range(board_height + 2)
    ]

    for x in range(board_width + 2):
        danger_map[0][x] = -1
        danger_map[board_height + 1][x] = -1

    for y in range(board_height + 2):
        danger_map[y][0] = -1
        danger_map[y][board_width + 1] = -1

    remaining_length = game_state["you"]["length"]
    for body_part in game_state["you"]["body"]:
        map_x = body_part["x"] + 1
        map_y = body_part["y"] + 1
        danger_map[map_y][map_x] = remaining_length
        remaining_length -= 1

    next_positions = {
        "up": {"x": my_head["x"], "y": my_head["y"] + 1},
        "down": {"x": my_head["x"], "y": my_head["y"] - 1},
        "left": {"x": my_head["x"] - 1, "y": my_head["y"]},
        "right": {"x": my_head["x"] + 1, "y": my_head["y"]},
    }

    for move, position in next_positions.items():
        if danger_map[position["y"] + 1][position["x"] + 1] != 0:
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
