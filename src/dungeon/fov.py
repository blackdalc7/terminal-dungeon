"""Field of view and pathfinding."""

from __future__ import annotations

from collections import deque

from dungeon.mapgen import WALL, Map, Pos


def line(a: Pos, b: Pos) -> list[Pos]:
    """Bresenham's line algorithm: the grid cells on a straight line from a to b."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    cells = []
    while True:
        cells.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return cells
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def visible(m: Map, origin: Pos, radius: int = 7) -> set[Pos]:
    """Cells the player can see: in range, and no wall in between (walls themselves are visible)."""
    ox, oy = origin
    seen = set()
    for y in range(oy - radius, oy + radius + 1):
        for x in range(ox - radius, ox + radius + 1):
            if not m.in_bounds((x, y)) or (x - ox) ** 2 + (y - oy) ** 2 > radius * radius:
                continue
            for cell in line(origin, (x, y)):
                seen.add(cell)
                if m[cell] == WALL:
                    break
    return seen


NEIGHBOURS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def bfs_next_step(
    m: Map, start: Pos, goal: Pos, blocked: set[Pos] = frozenset(), limit: int = 400
) -> Pos | None:
    """Breadth-first search from start to goal. Returns the first step to take, or None."""
    if start == goal:
        return None
    came_from: dict[Pos, Pos | None] = {start: None}
    queue = deque([start])
    while queue and len(came_from) < limit:
        current = queue.popleft()
        if current == goal:
            break
        cx, cy = current
        for dx, dy in NEIGHBOURS:
            nxt = (cx + dx, cy + dy)
            if nxt in came_from or not m.walkable(nxt):
                continue
            if nxt in blocked and nxt != goal:
                continue
            came_from[nxt] = current
            queue.append(nxt)
    if goal not in came_from:
        return None
    step = goal
    while came_from[step] != start:
        step = came_from[step]
    return step
