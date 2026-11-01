"""Draw the game as text. Optional ANSI colours."""

from __future__ import annotations

from dungeon.game import Game

COLOURS = {
    "@": "\033[1;93m",
    "$": "\033[33m",
    "!": "\033[95m",
    "/": "\033[96m",
    "]": "\033[96m",
    ">": "\033[1;97m",
    "#": "\033[38;5;245m",
    "dim": "\033[38;5;238m",
    "monster": "\033[1;91m",
}
RESET = "\033[0m"


def draw(game: Game, colour: bool = True) -> str:
    m = game.map
    entities = {i.pos: i.symbol for i in game.items}
    entities.update({mon.pos: mon.symbol for mon in game.monsters if mon.alive})
    entities[game.player.pos] = "@"

    def paint(ch: str, key: str | None = None) -> str:
        if not colour:
            return ch
        code = COLOURS.get(key or ch)
        return f"{code}{ch}{RESET}" if code else ch

    rows = []
    for y in range(m.height):
        row = []
        for x in range(m.width):
            pos = (x, y)
            if pos in game.visible:
                ch = entities.get(pos, m[pos])
                monster = ch.isalpha() and ch != "@"
                row.append(paint(ch, "monster" if monster else None))
            elif pos in m.seen:
                row.append(paint(m[pos], "dim"))  # remembered but not currently visible
            else:
                row.append(" ")
        rows.append("".join(row))

    p = game.player
    bar_len = 20
    filled = round(bar_len * p.hp / p.max_hp)
    hp_bar = "█" * filled + "░" * (bar_len - filled)
    status = (
        f"HP {hp_bar} {p.hp:>2}/{p.max_hp}  ATK {p.attack} DEF {p.defence}  "
        f"LV {game.level}  Depth {game.depth}/5  Gold {game.gold}  Potions {game.potions}"
    )
    return "\n".join([*rows, status, "-" * m.width, *game.log[-4:]])
