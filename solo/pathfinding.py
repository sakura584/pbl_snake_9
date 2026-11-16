from collections import deque
import typing


# BFSで使う、各方向の座標変化。
# Battlesnakeは上下左右にしか移動できない。
_DIRECTIONS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


# 座標を扱いやすい(x, y)形式のタプルへ変換する。
def point(cell: typing.Dict) -> typing.Tuple[int, int]:
    """Convert a coordinate dictionary into an (x, y) tuple."""
    return cell["x"], cell["y"]


# 頭から目的地までの経路をBFSで探索し、
# その経路の最初の1手だけを返す。
#
# safe_movesには、頭から最初に進む方向として許可されている方向を渡す。
# targetsには、到達したいマス（りんごやしっぽ）を渡す。
# avoid_food=Trueの場合は、経路の途中でりんごを通らないようにする。
def find_path_move(
    game_state: typing.Dict,
    safe_moves: typing.List[str],
    targets: typing.Set[typing.Tuple[int, int]],
    avoid_food: bool = False,
) -> typing.Optional[str]:
    """Return the first move on a safe BFS path to a target in solo mode."""
    board = game_state["board"]
    snake = game_state["you"]
    body = [point(part) for part in snake["body"]]
    food = {
        point(cell)
        for cell in board.get("food", [])
    }

    # soloでは、自分の体だけを障害物として扱う。
    # 通常はこのターンにしっぽが移動するため、現在のしっぽは通行可能にする。
    blocked = set(body[:-1])

    # りんごを避ける場合は、りんごのマスも障害物に追加する。
    if avoid_food:
        blocked.update(food)

    # BFSのキューには、現在位置と「最初に選んだ方向」を保存する。
    # 近いマスから調べるため、最初に見つかった目的地が最短経路になる。
    queue = deque([(body[0], None)])
    visited = {body[0]}

    while queue:
        cell, first_move = queue.popleft()

        # 目的地に到達したら、経路全体ではなく最初の方向だけ返す。
        if cell in targets and first_move is not None:
            return first_move

        for move, (dx, dy) in _DIRECTIONS.items():
            # 頭から最初に進む方向は、即死判定済みのsafe_movesに限定する。
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
                # 未探索の安全なマスを、次に探索する候補へ追加する。
                visited.add(target)
                queue.append((target, first_move or move))

    # 目的地まで到達できる経路がない場合はNoneを返す。
    return None
