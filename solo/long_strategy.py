import os
import random
import typing

# n >= 12のときの壁ふさぎ回避アルゴリズム
from .common import get_safe_moves
from .pathfinding import find_path_move, point


# longで、しっぽ追跡と壁ふさぎ回避のどちらを先に行うかを選ぶ。
# PowerShellでは、次のように切り替えられる。
# $env:LONG_PRIORITY = "tail"
# $env:LONG_PRIORITY = "wall"
LONG_PRIORITY = os.environ.get("LONG_PRIORITY", "tail").lower()
if LONG_PRIORITY not in {"tail", "wall"}:
    raise ValueError("LONG_PRIORITY must be 'tail' or 'wall'")


# 現在位置からりんごまでの距離を計算する。
# Battlesnakeは上下左右にしか移動できないため、
# 縦方向と横方向の移動回数を足したマンハッタン距離を返す。
def food_distance(position: typing.Dict, food: typing.Dict) -> float:
    """Return the Manhattan distance to a food cell."""
    dx = abs(position["x"] - food["x"])
    dy = abs(position["y"] - food["y"])
    return dx + dy


# ヘビの体が、盤面の端から端まで連続しているかを調べる。
# 横一列または縦一列がすべて自分の体で埋まっている場合はTrueを返す。
# 次の移動後の体を渡して、移動によって行・列をふさぐかを判定する。
def blocks_wall_to_wall(
    board_width: int,
    board_height: int,
    body: typing.List[typing.Dict],
) -> bool:
    """Return whether the body completely fills a row or a column."""
    occupied = {(part["x"], part["y"]) for part in body}

    for y in range(board_height):
        if all((x, y) in occupied for x in range(board_width)):
            return True

    for x in range(board_width):
        if all((x, y) in occupied for y in range(board_height)):
            return True

    return False


# 各候補方向へ1マス進んだ後の体を作り、
# 壁から壁までふさがない方向だけを返す。
# すべての候補が壁をふさぐ場合は、候補を空にせず元の候補を返す。
def _get_non_blocking_moves(
    game_state: typing.Dict,
    safe_moves: typing.List[str],
    next_positions: typing.Dict[str, typing.Dict],
    foods: typing.List[typing.Dict],
    board_width: int,
    board_height: int,
) -> typing.List[str]:
    """Return safe moves that do not create a full row or column."""
    non_blocking_moves = []

    for move in safe_moves:
        next_head = next_positions[move]

        # 移動先がりんごの場合は尻尾が残り、体長が1伸びる。
        eats_food = any(
            next_head["x"] == food["x"]
            and next_head["y"] == food["y"]
            for food in foods
        )

        simulated_body = [next_head] + game_state["you"]["body"]
        if not eats_food:
            # りんごを食べない場合は、最後の尻尾が1マス分消える。
            simulated_body = simulated_body[:-1]

        if not blocks_wall_to_wall(
            board_width,
            board_height,
            simulated_body,
        ):
            non_blocking_moves.append(move)

    # すべての候補が壁をふさぐ場合は、
    # 即死する方向ではない候補を残して生存を優先する。
    return non_blocking_moves or safe_moves


# 体長が12以上のときに使う移動戦略。
#
# 1. 壁・自分の体・逆走など、即死する方向を除外する。
# 2. 体力が13未満でりんごがある場合は、最も近いりんごへ近づく方向を優先する。
# 3. 体力が13以上なら、りんごを取らない方向を優先する。
# 4. LONG_PRIORITYに応じて、しっぽ追跡と壁ふさぎ回避の順番を変える。
# 5. どちらの経路も見つからなければ、残った候補からランダムに選ぶ。
def move_long(game_state: typing.Dict) -> typing.Dict:
    """Strategy for snakes with length 12 or greater."""
    # 共通処理で、壁・自分の体・逆走を避けた候補を取得する。
    safe_moves, next_positions = get_safe_moves(game_state)

    if not safe_moves:
        print(
            f"MOVE {game_state['turn']}: "
            "No safe moves detected! Moving down"
        )
        return {"move": "down"}

    board_width = game_state["board"]["width"]
    board_height = game_state["board"]["height"]
    health = game_state["you"]["health"]
    foods = game_state["board"].get("food", [])
    food_cells = {
        (food["x"], food["y"])
        for food in foods
    }

    # 体力が13未満のときは、壁ふさぎよりもりんごを優先する。
    # 各候補方向から最も近いりんごまでの距離を計算し、
    # その距離が最小になる方向だけを残す。
    if health < 13 and foods:
        # 各候補方向へ進んだ後の位置から、最も近いりんごまでの距離を求める。
        food_distances = {
            move: min(
                food_distance(next_positions[move], food)
                for food in foods
            )
            for move in safe_moves
        }
        nearest_food_distance = min(food_distances.values())

        # 最も近いりんごに近づく候補だけを残す。
        safe_moves = [
            move
            for move in safe_moves
            if food_distances[move] == nearest_food_distance
        ]
    else:
        # 体力が13以上のときは、壁ふさぎよりもりんご回避を優先する。
        # 移動先がりんごではない安全な方向だけを先に残す。
        if health >= 13:
            non_food_moves = [
                move
                for move in safe_moves
                if (
                    next_positions[move]["x"],
                    next_positions[move]["y"],
                ) not in food_cells
            ]

            # りんご以外の安全な方向がある場合だけ候補を置き換える。
            # すべてりんごの場合は候補を空にせず、生存を優先する。
            if non_food_moves:
                safe_moves = non_food_moves

        # しっぽを追うための目的地は、現在の最後尾のマスにする。
        tail = point(game_state["you"]["body"][-1])

        if LONG_PRIORITY == "tail":
            # しっぽ優先では、まずしっぽへの経路を探す。
            # この時点では、移動後に壁をふさぐかどうかはまだ判定しない。
            tail_move = find_path_move(
                game_state,
                safe_moves,
                {tail},
                avoid_food=True,
            )
            if tail_move is not None:
                print(f"MOVE {game_state['turn']}: {tail_move}")
                return {"move": tail_move}

            # しっぽへの経路がない場合だけ、壁ふさぎを避ける。
            safe_moves = _get_non_blocking_moves(
                game_state,
                safe_moves,
                next_positions,
                foods,
                board_width,
                board_height,
            )
        else:
            # 壁優先では、先に壁ふさぎを起こさない方向へ絞る。
            safe_moves = _get_non_blocking_moves(
                game_state,
                safe_moves,
                next_positions,
                foods,
                board_width,
                board_height,
            )

            # 壁をふさがない候補の中で、しっぽへの経路を探す。
            tail_move = find_path_move(
                game_state,
                safe_moves,
                {tail},
                avoid_food=True,
            )
            if tail_move is not None:
                print(f"MOVE {game_state['turn']}: {tail_move}")
                return {"move": tail_move}

    # 条件を満たした候補の中からランダムに選ぶ。
    next_move = random.choice(safe_moves)
    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}
