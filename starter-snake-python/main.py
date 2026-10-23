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

import random
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
    print("GAME START")


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    print("GAME OVER\n")


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

    # Check the four cells next to the head. Any non-zero value is unsafe:
    # -1 is a wall and a positive value is part of our body.
    next_positions = {
        "up": (my_head["x"], my_head["y"] + 1),
        "down": (my_head["x"], my_head["y"] - 1),
        "left": (my_head["x"] - 1, my_head["y"]),
        "right": (my_head["x"] + 1, my_head["y"]),
    }

    for move, (x, y) in next_positions.items():
        if danger_map[y + 1][x + 1] != 0:
            is_move_safe[move] = False

    if my_neck["x"] < my_head["x"]:  # Neck is left of head, don't move left
        is_move_safe["left"] = False

    elif my_neck["x"] > my_head["x"]:  # Neck is right of head, don't move right
        is_move_safe["right"] = False

    elif my_neck["y"] < my_head["y"]:  # Neck is below head, don't move down
        is_move_safe["down"] = False

    elif my_neck["y"] > my_head["y"]:  # Neck is above head, don't move up
        is_move_safe["up"] = False

    # TODO: Step 3 - Prevent your Battlesnake from colliding with other Battlesnakes
    # opponents = game_state['board']['snakes']

    # Are there any safe moves left?
    safe_moves = []
    for move, isSafe in is_move_safe.items():
        if isSafe:
            safe_moves.append(move)

    if len(safe_moves) == 0:
        print(f"MOVE {game_state['turn']}: No safe moves detected! Moving down")
        return {"move": "down"}

    # Choose a random move from the safe ones
    next_move = random.choice(safe_moves)

    # TODO: Step 4 - Move towards food instead of random, to regain health and survive longer
    # food = game_state['board']['food']

    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}


# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
