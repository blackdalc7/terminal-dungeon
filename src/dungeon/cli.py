"""Play in the terminal.

    python -m dungeon            # random dungeon
    python -m dungeon --seed 42  # same dungeon every time
"""

from __future__ import annotations

import argparse
import os
import sys

from dungeon.game import Game
from dungeon.render import draw

HELP = "move: w a s d (+Enter, or type several like 'ddd')   p: potion   .: wait   >: stairs   q: quit"


def play(game: Game, read=None, write=print, colour: bool = True, clear: bool = True) -> int:
    """Run the game loop: draw, read a command, apply it, until the game ends or the player quits."""
    read = read or input
    while not game.over:
        if clear:
            write("\033[H\033[2J", end="")
        write(draw(game, colour))
        write(HELP)
        try:
            line = read("> ")
        except EOFError:
            break
        if line.strip().lower() == "q":
            break
        # several moves can be typed at once, e.g. "dddw"
        for ch in line.strip() or ".":
            game.act(ch)
            if game.over:
                break
    write(draw(game, colour))
    verdict = "YOU WIN!" if game.won else ("GAME OVER" if not game.player.alive else "Bye!")
    write(f"\n{verdict}  depth {game.depth}, level {game.level}, {game.kills} kills, "
          f"{game.gold} gold, score {game.score}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dungeon", description="A tiny terminal roguelike")
    parser.add_argument("--seed", type=int, help="dungeon seed (same seed = same dungeon)")
    parser.add_argument("--no-colour", action="store_true", help="disable ANSI colours")
    args = parser.parse_args(argv)
    if os.name == "nt":
        os.system("")  # noqa: S605,S607  (enables ANSI escape codes in the Windows console)
    colour = not args.no_colour and sys.stdout.isatty()
    return play(Game.new(args.seed), colour=colour)
