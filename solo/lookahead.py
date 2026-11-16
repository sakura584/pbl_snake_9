from contextlib import redirect_stdout
import copy
import io
import typing

from .common import get_safe_moves
from .long_strategy import move_long
from .short_strategy import move_short


# 現在の移動に加えて、次の1ターンまでを予測する。
# つまり、現在の候補から最大2回分の移動を調べる。
LOOKAHEAD_TURNS = 2


# Battlesnakeの1回の移動で変化する、上下左右の座標差分。
_DIRECTIONS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


# 体長に応じて、現在採用しているshort／long戦略を呼び出す。
def _current_strategy(game_state: typing.Dict) -> typing.Dict:
    """Return the move chosen by the current length-based strategy."""
    if game_state["you"]["length"] >= 12:
        return move_long(game_state)
    return move_short(game_state)


# 現在の状態から、予測で調べる候補方向を作る。
#
# 予測では候補を1つに絞らず、候補をすべて調べる。
# ただし、体力13以上でりんご以外の安全な方向がある場合は、
# 確定したりんご回避ルールに従ってりんご方向を候補から除外する。
def _candidate_moves(game_state: typing.Dict) -> typing.List[str]:
    """Return all moves that the lookahead is allowed to examine."""
    safe_moves, next_positions = get_safe_moves(game_state)
    if not safe_moves:
        return []

    health = game_state["you"]["health"]
    if health < 13:
        return safe_moves

    food_cells = {
        (food["x"], food["y"])
        for food in game_state["board"].get("food", [])
    }
    non_food_moves = [
        move
        for move in safe_moves
        if (
            next_positions[move]["x"],
            next_positions[move]["y"],
        ) not in food_cells
    ]

    # りんご以外の安全な方向がある場合は、それらだけを調べる。
    # すべてりんごの場合は候補を空にせず、生存を優先する。
    return non_food_moves or safe_moves


# 現在の戦略が選ぶ方向を、候補の優先順位として利用する。
#
# 予測では候補をすべて調べるが、生存ターン数が同じ場合は、
# 現在のshort／long戦略が選ぶ方向を優先するために使う。
def _prioritized_candidates(game_state: typing.Dict) -> typing.List[str]:
    """Return all candidates with the current strategy's choice first."""
    candidates = _candidate_moves(game_state)
    if not candidates:
        return []

    # move_short/move_longは移動ログを出すため、予測中は表示を抑える。
    with redirect_stdout(io.StringIO()):
        preferred_move = _current_strategy(game_state)["move"]

    if preferred_move in candidates:
        return [
            preferred_move,
            *[move for move in candidates if move != preferred_move],
        ]

    return candidates


# 指定された方向へ1ターン進んだ後のゲーム状態を作る。
# りんごの補充は行わず、食べたマスからりんごを削除する。
def _simulate_move(
    game_state: typing.Dict,
    move: str,
) -> typing.Optional[typing.Dict]:
    """Return the next simulated state, or None if the snake dies."""
    next_state = copy.deepcopy(game_state)
    snake = next_state["you"]
    body = snake["body"]
    head = body[0]
    dx, dy = _DIRECTIONS[move]
    next_head = {
        "x": head["x"] + dx,
        "y": head["y"] + dy,
    }

    # 実際のゲームと同じく、移動するたびに体力を1減らす。
    next_health = snake["health"] - 1
    food = next_state["board"].get("food", [])
    eaten_food = any(
        cell["x"] == next_head["x"]
        and cell["y"] == next_head["y"]
        for cell in food
    )

    if eaten_food:
        # りんごを食べた場合は、しっぽを消さずに体長を1増やす。
        next_health = 100
        next_state["board"]["food"] = [
            cell
            for cell in food
            if not (
                cell["x"] == next_head["x"]
                and cell["y"] == next_head["y"]
            )
        ]
        next_body = [next_head] + body
    else:
        # りんごを食べない場合は、最後尾が1マス消える。
        next_body = [next_head] + body[:-1]

    # 体力が0以下になったターンは、その時点で死亡とする。
    if next_health <= 0:
        return None

    snake["body"] = next_body
    snake["head"] = next_head
    snake["length"] = len(next_body)
    snake["health"] = next_health
    next_state["turn"] = next_state.get("turn", 0) + 1

    return next_state


# 指定された状態から、残りの予測ターンで生き残れる最大ターン数を調べる。
# すべての候補を再帰的に調べ、最も長く生きる経路の長さを返す。
def _max_survival_turns(
    game_state: typing.Dict,
    remaining_turns: int,
) -> int:
    """Return the maximum number of future moves that can survive."""
    if remaining_turns == 0:
        return 0

    candidates = _prioritized_candidates(game_state)
    if not candidates:
        return 0

    best_score = 0
    for move in candidates:
        next_state = _simulate_move(game_state, move)
        if next_state is None:
            continue

        score = 1 + _max_survival_turns(
            next_state,
            remaining_turns - 1,
        )
        best_score = max(best_score, score)

    return best_score


# 現在の1手を、2ターン先までの生存数で選ぶ。
# 生存数が同じ場合は、候補の並び順に従うため、
# 現在のstrategyが優先する方向を選ぶ。
def choose_move(game_state: typing.Dict) -> typing.Dict:
    """Choose the first move using exhaustive two-turn lookahead."""
    candidates = _prioritized_candidates(game_state)

    if not candidates:
        print(
            f"MOVE {game_state['turn']}: "
            "No safe moves detected! Moving down"
        )
        return {"move": "down"}

    best_move = candidates[0]
    best_score = -1

    # 候補は優先順位順に調べる。
    # 同じ生存数なら、先に調べた現在の戦略の候補を残す。
    for move in candidates:
        next_state = _simulate_move(game_state, move)
        if next_state is None:
            score = 0
        else:
            score = 1 + _max_survival_turns(
                next_state,
                LOOKAHEAD_TURNS - 1,
            )

        if score > best_score:
            best_move = move
            best_score = score

    print(
        f"MOVE {game_state['turn']}: {best_move} "
        f"(lookahead survival: {best_score}/{LOOKAHEAD_TURNS})"
    )
    return {"move": best_move}
