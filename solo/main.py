# Welcome to
# __________         __    __  .__                               .__
# \______   \_____ _/  |__/  |_|  |   ____   ______ ____ _____  |  | __ __
#  |    |  _/\__  \\   __\   __\  | _/ __ \ /  ___//    \\__  \ |  |/ // __ \
#  |    |   \ / __ \|  |  |  | |  |_\  ___/ \___ \|   |  \/ __ \|    <\  ___/
#  |________/(______/__|  |__| |____/\_____>______>___|__(______/__|__\_____>
#
# This file is the shared Battlesnake entry point.

import typing

from .long_strategy import move_long
from .short_strategy import move_short


def info() -> typing.Dict:
    print("INFO")

    return {
        "apiversion": "1",
        "author": "",  # TODO: Your Battlesnake Username
        "color": "#888888",  # TODO: Choose color
        "head": "default",  # TODO: Choose head
        "tail": "default",  # TODO: Choose tail
    }


def start(game_state: typing.Dict):
    print("GAME START")


def end(game_state: typing.Dict):
    print("GAME OVER\n")


def move(game_state: typing.Dict) -> typing.Dict:
    """Dispatch each turn to the strategy for the current snake length."""
    if game_state["you"]["length"] >= 12:
        return move_long(game_state)

    return move_short(game_state)


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
