from helpers import open_room_game

from dungeon import fov
from dungeon.mapgen import WALL


def test_line_endpoints_and_length():
    cells = fov.line((0, 0), (4, 2))
    assert cells[0] == (0, 0)
    assert cells[-1] == (4, 2)
    assert len(cells) == 5


def test_line_vertical_and_backwards():
    assert fov.line((2, 3), (2, 0)) == [(2, 3), (2, 2), (2, 1), (2, 0)]


def test_walls_block_sight():
    g = open_room_game(14, 7)
    for y in range(1, 6):
        g.map[(6, y)] = WALL  # a wall splitting the room
    seen = fov.visible(g.map, (3, 3))
    assert (6, 3) in seen  # you can see the wall itself
    assert (8, 3) not in seen  # but not behind it


def test_radius_limits_sight():
    g = open_room_game(30, 6)
    seen = fov.visible(g.map, (2, 2), radius=4)
    assert (6, 2) in seen
    assert (8, 2) not in seen


def test_bfs_finds_shortest_first_step():
    g = open_room_game()
    assert fov.bfs_next_step(g.map, (2, 2), (5, 2)) == (3, 2)
    assert fov.bfs_next_step(g.map, (2, 2), (2, 2)) is None


def test_bfs_goes_around_walls():
    g = open_room_game(10, 7)
    for y in range(1, 5):
        g.map[(4, y)] = WALL  # wall with a gap at the bottom (y=5)
    step = fov.bfs_next_step(g.map, (3, 1), (5, 1))
    assert step == (3, 2)  # has to head down towards the gap


def test_bfs_respects_blocked_cells_and_unreachable():
    g = open_room_game(8, 3)  # one-row corridor: y=1, x=1..6
    assert fov.bfs_next_step(g.map, (1, 1), (6, 1), blocked={(3, 1)}) is None
    g.map[(4, 1)] = WALL
    assert fov.bfs_next_step(g.map, (1, 1), (6, 1)) is None
