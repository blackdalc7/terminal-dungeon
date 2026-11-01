import random

import pytest

from dungeon import fov
from dungeon.mapgen import FLOOR, STAIRS, WALL, Map, Room, generate


def test_same_seed_same_map():
    a = generate(rng=random.Random(5))
    b = generate(rng=random.Random(5))
    assert a.tiles == b.tiles


def test_rooms_dont_overlap_and_stay_inside():
    m = generate(rng=random.Random(1))
    for i, r in enumerate(m.rooms):
        assert r.x >= 1 and r.y >= 1 and r.x + r.w < m.width and r.y + r.h < m.height
        for other in m.rooms[i + 1 :]:
            assert not r.intersects(other, gap=0)


def test_border_is_solid_wall():
    m = generate(rng=random.Random(2))
    assert all(t == WALL for t in m.tiles[0])
    assert all(t == WALL for t in m.tiles[-1])
    assert all(row[0] == WALL and row[-1] == WALL for row in m.tiles)


@pytest.mark.parametrize("seed", range(25))
def test_every_room_and_the_stairs_are_reachable(seed):
    m = generate(rng=random.Random(seed))
    start = m.rooms[0].center
    for room in m.rooms[1:]:
        assert fov.bfs_next_step(m, start, room.center, limit=10_000) is not None
    assert m[m.rooms[-1].center] == STAIRS


def test_tiny_map_fails_loudly():
    with pytest.raises(ValueError, match="at least"):
        generate(width=8, height=6, rng=random.Random(0))


def test_room_helpers():
    r = Room(2, 3, 4, 2)
    assert r.center == (4, 4)
    assert len(r.cells()) == 8
    assert r.intersects(Room(5, 3, 2, 2))
    assert not r.intersects(Room(8, 3, 2, 2))


def test_map_indexing():
    m = Map(5, 4)
    m[(1, 2)] = FLOOR
    assert m[(1, 2)] == FLOOR
    assert m.walkable((1, 2))
    assert not m.walkable((0, 0))
    assert not m.walkable((9, 9))
    assert m.floor_cells() == [(1, 2)]
