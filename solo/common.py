import typing


# 現在のゲーム状態から、即死しない移動方向を調べる共通処理。
#
# solo仕様では、次の条件に当てはまる方向を危険とする。
# - 盤面の外へ出る
# - 自分の体に当たる
# - りんごを食べることで、移動しないしっぽに当たる
# - 首の方向へ逆走する
#
# safe_movesには安全な方向の名前を、next_positionsには
# 各方向へ進んだ場合の座標を返す。
def get_safe_moves(
    game_state: typing.Dict,
) -> typing.Tuple[
    typing.List[str],
    typing.Dict[str, typing.Dict],
]:
    """Return safe moves and their destination coordinates."""
    # 最初は4方向をすべて安全として、危険な方向をFalseに変更する。
    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    board = game_state["board"]
    snake = game_state["you"]
    body = snake["body"]
    my_head = body[0]
    my_neck = body[1]
    tail = body[-1]

    # 移動先がりんごの場合は、しっぽが消えずに残る。
    # そのため、しっぽのマスにあるりんごへ進むのは危険とする。
    food_cells = {
        (food["x"], food["y"])
        for food in board.get("food", [])
    }

    # 頭が上下左右へ1マス進んだ場合の座標を作る。
    next_positions = {
        "up": {"x": my_head["x"], "y": my_head["y"] + 1},
        "down": {"x": my_head["x"], "y": my_head["y"] - 1},
        "left": {"x": my_head["x"] - 1, "y": my_head["y"]},
        "right": {"x": my_head["x"] + 1, "y": my_head["y"]},
    }

    # 通常の移動では、現在の最後尾は次のターンに消えるため、
    # 自分の体のうち最後尾以外を衝突判定の対象にする。
    occupied_body = {
        (part["x"], part["y"])
        for part in body[:-1]
    }

    for move, position in next_positions.items():
        cell = (position["x"], position["y"])

        # 盤面の外へ出る移動かどうかを調べる。
        outside_board = not (
            0 <= position["x"] < board["width"]
            and 0 <= position["y"] < board["height"]
        )

        # りんごを食べる場合、しっぽが移動しないため、
        # しっぽのマスへ進むと衝突する。
        tail_will_not_move = cell == (tail["x"], tail["y"]) and cell in food_cells

        # いずれかに当たる方向を危険として除外する。
        if (
            outside_board
            or cell in occupied_body
            or tail_will_not_move
        ):
            is_move_safe[move] = False

    # 首の位置から、逆方向への移動を禁止する。
    if my_neck["x"] < my_head["x"]:
        is_move_safe["left"] = False
    elif my_neck["x"] > my_head["x"]:
        is_move_safe["right"] = False
    elif my_neck["y"] < my_head["y"]:
        is_move_safe["down"] = False
    elif my_neck["y"] > my_head["y"]:
        is_move_safe["up"] = False

    # Trueのまま残った方向だけを安全な候補として返す。
    safe_moves = [
        move
        for move, is_safe in is_move_safe.items()
        if is_safe
    ]
    return safe_moves, next_positions
