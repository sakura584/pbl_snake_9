# Welcome to
# __________         __    __  .__                               __
# \______   \_____ _/  |__/  |_|  |   ____   ______ ____ _____  |  | __ ____
#  |    |  _/\__  \\   __\   __\  | _/ __ \ /  ___//    \\__  \ |  |/ // __ \
#  |    |   \ / __ \|  |  |  | |  |_\  ___/ \___ \|   |  \/ __ \|    <\  ___/
#  |________/(______/__|  |__| |____/\_____>______>___|__(______/__|__\\_____>
#
# This file can be a nice home for your Battlesnake logic and helper functions.
#
# To get you started we've included code to prevent your Battlesnake from moving backwards.
# For more info see docs.battlesnake.com

from collections import deque
import typing


# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
    print("INFO")

    return {
        "apiversion": "1",
        "author": "",  # TODO: Your Battlesnake Username
        "color": "#888888",  # TODO: Choose color
        "head": "default",  # TODO: Choose head
        "tail": "default",  # TODO: Choose tail
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    _loop_routes.pop(_game_key(game_state), None)
    print("GAME START")


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    _loop_routes.pop(_game_key(game_state), None)
    print("GAME OVER\n")


# Keep a selected loop for each snake/game, so consecutive turns follow it.
_loop_routes = {}
_DIRECTIONS = {"up": (0, 1), "down": (0, -1),
               "left": (-1, 0), "right": (1, 0)}


def _game_key(state):
    return state.get("game", {}).get("id", "local"), state["you"].get("id", "you")


def _point(cell):
    return cell["x"], cell["y"]


def _find_path_move(state, safe_moves, targets, avoid_food=False):
    """幅優先探索で目的地への最短経路の最初の一手を返す。"""
    board, snake = state["board"], state["you"]
    body = [_point(cell) for cell in snake["body"]]
    food = {_point(cell) for cell in board.get("food", [])}
    # Only the final tail segment moves away this turn. A duplicated tail
    # remains blocked because it also occurs in body[:-1].
    blocked = set(body[:-1])
    blocked.update(_point(cell) for other in board.get("snakes", [])
                   if other.get("id") != snake.get("id") for cell in other["body"])
    blocked.update(_point(cell) for cell in board.get("hazards", []))
    if avoid_food:
        blocked.update(food)
    queue = deque([(body[0], None)])
    visited = {body[0]}
    while queue:
        cell, first_move = queue.popleft()
        if cell in targets and first_move is not None:
            return first_move
        for name, (dx, dy) in _DIRECTIONS.items():
            if first_move is None and name not in safe_moves:
                continue
            target = cell[0] + dx, cell[1] + dy
            if (0 <= target[0] < board["width"]
                    and 0 <= target[1] < board["height"]
                    and target not in blocked and target not in visited):
                visited.add(target)
                queue.append((target, first_move or name))
    return None


def _choose_strategy_move(state, safe_moves):
    """体力を先に確認し、長さ12を境に作戦を切り替える。"""
    snake = state["you"]
    if snake["health"] < 13:
        food = {_point(cell) for cell in state["board"].get("food", [])}
        food_move = _find_path_move(state, safe_moves, food)
        if food_move is not None:
            _loop_routes.pop(_game_key(state), None)
            return food_move

    n = snake["length"]
    if n < 12:
        # 木村担当: 餌を避けながら、毎ターン更新されるしっぽを追う。
        _loop_routes.pop(_game_key(state), None)
        tail_move = _find_path_move(
            state, safe_moves, {_point(snake["body"][-1])}, avoid_food=True)
        if tail_move is not None:
            return tail_move

    # n >= 12 は既存のぐるぐる作戦。しっぽに到達できない場合も退避する。
    return _choose_loop_move(state, safe_moves)


def _choose_loop_move(state, safe_moves):
    board, snake = state["board"], state["you"]
    body = [_point(cell) for cell in snake["body"]]
    head = body[0]
    food = {_point(cell) for cell in board.get("food", [])}
    obstacles = {_point(cell) for other in board.get("snakes", [])
                 if other.get("id") != snake.get("id") for cell in other["body"]}
    obstacles.update(_point(cell) for cell in board.get("hazards", []))
    width, height = board["width"], board["height"]
    key = _game_key(state)

    def direction(a, b):
        return next(name for name, delta in _DIRECTIONS.items()
                    if (b[0] - a[0], b[1] - a[1]) == delta)

    def usable(route):
        if head not in route or len(route) <= len(body):
            return False
        if set(route) & (food | obstacles):
            return False
        index = route.index(head)
        if direction(head, route[(index + 1) % len(route)]) not in safe_moves:
            return False
        simulated = body[:]
        # After the original body has cleared, a food-free simple loop repeats safely.
        for step in range(1, len(body) + 1):
            target = route[(index + step) % len(route)]
            if target in simulated[:-1]:
                return False
            simulated = [target] + simulated[:-1]
        return True

    blocked = set(body[1:]) | obstacles

    route = _loop_routes.get(key)
    if route is None or not usable(route):
        _loop_routes.pop(key, None)
        candidates = []
        # Rectangular perimeters are simple loops. Prefer the shortest loop
        # that fits the current body without requiring any additional growth.
        for left in range(head[0] + 1):
            for right in range(max(left + 1, head[0]), width):
                for bottom in range(head[1] + 1):
                    for top in range(max(bottom + 1, head[1]), height):
                        if head[0] not in (left, right) and head[1] not in (bottom, top):
                            continue
                        perimeter = ([(x, bottom) for x in range(left, right)]
                                     + [(right, y) for y in range(bottom, top)]
                                     + [(x, top) for x in range(right, left, -1)]
                                     + [(left, y) for y in range(top, bottom, -1)])
                        if len(perimeter) > len(body):
                            candidates.extend((perimeter, perimeter[::-1]))
        route = next((r for r in sorted(candidates, key=len) if usable(r)), None)
        if route:
            _loop_routes[key] = route
    if route:
        return direction(head, route[(route.index(head) + 1) % len(route)])

    # If no loop is available yet, avoid food and choose room to manoeuvre.
    def score(name):
        dx, dy = _DIRECTIONS[name]
        target = head[0] + dx, head[1] + dy
        reachable = {target}
        pending = [target]
        while pending:
            x, y = pending.pop()
            for ox, oy in _DIRECTIONS.values():
                cell = x + ox, y + oy
                if (0 <= cell[0] < width and 0 <= cell[1] < height
                        and cell not in blocked and cell not in reachable):
                    reachable.add(cell)
                    pending.append(cell)
        return target not in obstacles, target not in food, len(reachable)

    return max(safe_moves, key=score)


# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:

    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    # We've included code to prevent your Battlesnake from moving backwards
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_neck = game_state["you"]["body"][1]  # Coordinates of your "neck"

    # Create a map with a one-cell border around the board.
    # The border represents walls (-1), and 0 represents an empty cell.
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

    # body is ordered from head to tail. Store the remaining body length at
    # each occupied cell: length at the head, then length - 1, ..., 1.
    remaining_length = game_state["you"]["length"]
    for body_part in game_state["you"]["body"]:
        map_x = body_part["x"] + 1
        map_y = body_part["y"] + 1
        danger_map[map_y][map_x] = remaining_length
        remaining_length -= 1

    # Check walls and body collisions, allowing a tail cell that moves away.
    occupied_body = {_point(part) for part in game_state["you"]["body"][:-1]}
    food_cells = {_point(cell) for cell in game_state["board"].get("food", [])}
    tail = _point(game_state["you"]["body"][-1])
    next_positions = {
        "up": (my_head["x"], my_head["y"] + 1),
        "down": (my_head["x"], my_head["y"] - 1),
        "left": (my_head["x"] - 1, my_head["y"]),
        "right": (my_head["x"] + 1, my_head["y"]),
    }

    for move, (x, y) in next_positions.items():
        cell = (x, y)
        if (danger_map[y + 1][x + 1] == -1 or cell in occupied_body
                or (cell == tail and cell in food_cells)):
            is_move_safe[move] = False

    if my_neck["x"] < my_head["x"]:  # Neck is left of head, don't move left
        is_move_safe["left"] = False

    elif my_neck["x"] > my_head["x"]:  # Neck is right of head, don't move right
        is_move_safe["right"] = False

    elif my_neck["y"] < my_head["y"]:  # Neck is below head, don't move down
        is_move_safe["down"] = False

    elif my_neck["y"] > my_head["y"]:  # Neck is above head, don't move up
        is_move_safe["up"] = False

    # Avoid occupied opponent cells and hazardous cells before choosing a loop.
    blocked_cells = {
        _point(part)
        for opponent in game_state["board"].get("snakes", [])
        if opponent.get("id") != game_state["you"].get("id")
        for part in opponent["body"]
    }
    blocked_cells.update(_point(cell) for cell in game_state["board"].get("hazards", []))
    for name, position in next_positions.items():
        if position in blocked_cells:
            is_move_safe[name] = False

    # Are there any safe moves left?
    safe_moves = []
    for move, isSafe in is_move_safe.items():
        if isSafe:
            safe_moves.append(move)

    if len(safe_moves) == 0:
        print(f"MOVE {game_state['turn']}: No safe moves detected! Moving down")
        return {"move": "down"}

    # First check health, then choose tail following (n < 12) or looping.
    next_move = _choose_strategy_move(game_state, safe_moves)

    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}



# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
