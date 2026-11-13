import random
import typing

from .common import get_safe_moves
from .pathfinding import find_path_move, point


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
        point(cell)
        for cell in game_state["board"].get("food", [])
    }

    # 体力が13未満のときは、しっぽよりもりんごを優先する。
    # BFSは近いマスから調べるため、最短経路で到達できるりんごを選ぶ。
    if health < 13 and food:
        food_move = find_path_move(game_state, safe_moves, food)
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
    tail = point(snake["body"][-1])
    tail_move = find_path_move(
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
