import random

from dungeon.game import Entity, Game
from dungeon.mapgen import FLOOR, Map, Room, carve_room


def open_room_game(width=12, height=8) -> Game:
    """A game on a single open room with nothing in it, for precise tests."""
    m = Map(width, height)
    room = Room(1, 1, width - 2, height - 2)
    carve_room(m, room)
    m.rooms = [room]
    game = Game(rng=random.Random(0))
    game.map = m
    game.player.pos = (2, 2)
    game.update_fov()
    return game


def monster(pos, hp=5, attack=2, defence=0, name="rat", xp=3) -> Entity:
    return Entity(name, name[0], pos, hp, hp, attack, defence, xp)


__all__ = ["FLOOR", "monster", "open_room_game"]
