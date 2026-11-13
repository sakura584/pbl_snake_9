from collections import deque
import random
import typing

from .common import get_safe_moves


# BFSで使う、各方向の座標変化。
# Battlesnakeは上下左右にしか移動できない。
_DIRECTIONS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


# 座標を扱いやすい(x, y)形式のタプルへ変換する。
def _point(cell: typing.Dict) -> typing.Tuple[int, int]:
    """Convert a coordinate dictionary into an (x, y) tuple."""
    return cell["x"], cell["y"]


# 頭から目的地までの経路をBFSで探索し、
# その経路の最初の1手だけを返す。
#
# safe_movesには、頭から最初に進む方向として許可されている方向を渡す。
# targetsには、到達したいマス（りんごやしっぽ）を渡す。
# avoid_food=Trueの場合は、しっぽを追う途中でりんごを食べないようにする。
def _find_path_move(
    game_state: typing.Dict,
    safe_moves: typing.List[str],
    targets: typing.Set[typing.Tuple[int, int]],
    avoid_food: bool = False,
) -> typing.Optional[str]:
    """Return the first move on a safe BFS path to a target in solo mode."""
    board = game_state["board"]
    snake = game_state["you"]
    body = [_point(part) for part in snake["body"]]
    food = {
        _point(cell)
        for cell in board.get("food", [])
    }

    # soloでは、自分の体だけを障害物として扱う。
    # 通常はこのターンにしっぽが移動するため、現在のしっぽのマスは通行可能にする。
    blocked = set(body[:-1])

    # しっぽを追うときは、途中でりんごを食べて体が伸びることを避ける。
    if avoid_food:
        blocked.update(food)

    # BFSのキューには、現在位置と「最初に選んだ方向」を保存する。
    # 目的地に着いたとき、経路全体ではなく最初の方向だけ返すために使う。
    queue = deque([(body[0], None)])
    visited = {body[0]}

    while queue:
        cell, first_move = queue.popleft()

        # 目的地に到達したら、最初に選んだ方向を返す。
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


# soloモードで体長が12未満のヘビに使う移動戦略。
#
# 1. 壁・自分の体など、即死する方向を除外する。
# 2. 体力が13未満なら、最も近いりんごへの経路を優先する。
# 3. 体力が13以上なら、りんごを避けながらしっぽへの経路を探す。
# 4. 経路が見つからない場合は、りんごを避けた候補からランダムに選ぶ。
def move_short(game_state: typing.Dict) -> typing.Dict:
    """Use food-first movement, then follow the tail for snakes shorter than 12."""
    # 共通処理で、即死しない候補方向を取得する。
    # next_positionsは、各方向へ1マス進んだ先の座標である。
    safe_moves, next_positions = get_safe_moves(game_state)

    if not safe_moves:
        print(
            f"MOVE {game_state['turn']}: "
            "No safe moves detected! Moving down"
        )
        return {"move": "down"}

    snake = game_state["you"]
    health = snake["health"]
    food = {
        _point(cell)
        for cell in game_state["board"].get("food", [])
    }

    # 体力が13未満のときは、しっぽよりもりんごを優先する。
    # BFSは近いマスから調べるため、最短経路で到達できるりんごを選ぶ。
    if health < 13 and food:
        food_move = _find_path_move(game_state, safe_moves, food)
        if food_move is not None:
            print(f"MOVE {game_state['turn']}: {food_move}")
            return {"move": food_move}

    # 体力が13以上のときは、りんごを食べないことを優先する。
    # ただし、安全な移動先がりんごしかない場合は、候補を空にしない。
    # その場合は、りんごを食べることよりも生存を優先する。
    if health >= 13:
        non_food_moves = [
            move
            for move in safe_moves
            if (
                next_positions[move]["x"],
                next_positions[move]["y"],
            ) not in food
        ]
        if non_food_moves:
            safe_moves = non_food_moves

    # りんごへの経路が見つからない場合は、現在のしっぽを追う。
    # 体力が13以上ならavoid_food=Trueにより、経路の途中でもりんごを通過しない。
    # 体力が13未満なら、りんごを通過する可能性を残してしっぽを追う。
    tail = _point(snake["body"][-1])
    tail_move = _find_path_move(
        game_state,
        safe_moves,
        {tail},
        avoid_food=health >= 13,
    )
    if tail_move is not None:
        print(f"MOVE {game_state['turn']}: {tail_move}")
        return {"move": tail_move}

    # りんごやしっぽへの経路が見つからない場合は、
    # ここまで残した安全な候補からランダムに選ぶ。
    # 体力が13以上で、りんご以外の候補が存在していた場合は、
    # safe_movesからりんごを除外済みなので、ここでもりんごを避けられる。
    next_move = random.choice(safe_moves)
    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}
