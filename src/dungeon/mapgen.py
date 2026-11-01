"""Procedural map generation: random rooms joined by L-shaped corridors."""

from __future__ import annotations

import random
from dataclasses import dataclass

WALL, FLOOR, STAIRS = "#", ".", ">"

Pos = tuple[int, int]  # (x, y)


@dataclass(frozen=True)
class Room:
    """A rectangular room on the map."""
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> Pos:
        return (self.x + self.w // 2, self.y + self.h // 2)

    def intersects(self, other: Room, gap: int = 1) -> bool:
        return not (
            self.x + self.w + gap <= other.x
            or other.x + other.w + gap <= self.x
            or self.y + self.h + gap <= other.y
            or other.y + other.h + gap <= self.y
        )

    def cells(self) -> list[Pos]:
        return [(x, y) for y in range(self.y, self.y + self.h) for x in range(self.x, self.x + self.w)]


class Map:
    """The tile grid of one floor and the rooms carved into it."""
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.tiles = [[WALL] * width for _ in range(height)]
        self.rooms: list[Room] = []
        self.seen: set[Pos] = set()

    def __getitem__(self, pos: Pos) -> str:
        x, y = pos
        return self.tiles[y][x]

    def __setitem__(self, pos: Pos, tile: str) -> None:
        x, y = pos
        self.tiles[y][x] = tile

    def in_bounds(self, pos: Pos) -> bool:
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def walkable(self, pos: Pos) -> bool:
        return self.in_bounds(pos) and self[pos] != WALL

    def floor_cells(self) -> list[Pos]:
        return [(x, y) for y in range(self.height) for x in range(self.width) if self[(x, y)] == FLOOR]


def carve_room(m: Map, room: Room) -> None:
    for cell in room.cells():
        m[cell] = FLOOR


def carve_corridor(m: Map, a: Pos, b: Pos, rng: random.Random) -> None:
    """L-shaped corridor: horizontal then vertical, or the other way round."""
    (x1, y1), (x2, y2) = a, b
    corner = (x2, y1) if rng.random() < 0.5 else (x1, y2)
    for (sx, sy), (ex, ey) in ((a, corner), (corner, b)):
        for x in range(min(sx, ex), max(sx, ex) + 1):
            for y in range(min(sy, ey), max(sy, ey) + 1):
                m[(x, y)] = FLOOR


def generate(width: int = 60, height: int = 22, max_rooms: int = 12, rng: random.Random | None = None) -> Map:
    if width < 16 or height < 8:
        raise ValueError("map must be at least 16x8")
    rng = rng or random.Random()
    for _attempt in range(100):  # small maps sometimes only fit one room, so just try again
        m = _try_generate(width, height, max_rooms, rng)
        if len(m.rooms) >= 2:
            m[m.rooms[-1].center] = STAIRS
            return m
    raise RuntimeError("could not place two rooms, try a bigger map")  # pragma: no cover


def _try_generate(width: int, height: int, max_rooms: int, rng: random.Random) -> Map:
    m = Map(width, height)
    for _ in range(max_rooms * 5):
        if len(m.rooms) >= max_rooms:
            break
        w, h = rng.randint(4, 10), rng.randint(3, 6)
        if w > width - 2 or h > height - 2:
            continue
        room = Room(rng.randint(1, width - w - 1), rng.randint(1, height - h - 1), w, h)
        if any(room.intersects(other) for other in m.rooms):
            continue
        carve_room(m, room)
        if m.rooms:
            carve_corridor(m, m.rooms[-1].center, room.center, rng)
        m.rooms.append(room)
    return m
