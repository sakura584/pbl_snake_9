import random
import typing

# n >= 12のときの壁ふさぎ回避アルゴリズム
from .common import get_safe_moves


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


# 体長が12以上のときに使う移動戦略。
#
# 1. 壁・自分の体・逆走など、即死する方向を除外する。
# 2. 体力が13未満でりんごがある場合は、最も近いりんごへ近づく方向を優先する。
# 3. 体力が13以上なら、りんごを取らない方向を優先する。
# 4. 残った候補から、壁から壁までふさぐ方向を避ける。
# 5. 最後に、残った候補からランダムに1方向を選ぶ。
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

        # 各候補方向へ1マス進んだ後の体を作り、
        # 行・列を壁から壁までふさぐ方向を取り除く。
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

        # すべての候補が行・列をふさぐ場合は、
        # 即死する方向ではない候補を残して、その中から選ぶ。
        if non_blocking_moves:
            safe_moves = non_blocking_moves

    # 条件を満たした候補の中からランダムに選ぶ。
    next_move = random.choice(safe_moves)
    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}
