"""
solver.py — Pathfinding algorithms: BFS, DFS, A*, Dijkstra

Each solver is a generator that yields intermediate states so the
visualiser can animate every explored node step-by-step.

Yield format: ("explore" | "path", list_of_(r,c) cells)
"""

import heapq
from collections import deque
from typing import Generator, List, Tuple

from maze import Maze


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Cell = Tuple[int, int]
Step = Tuple[str, List[Cell]]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _reconstruct_path(came_from: dict, end: Cell) -> List[Cell]:
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = came_from.get(node)
    path.reverse()
    return path


# ---------------------------------------------------------------------------
# BFS — guaranteed shortest path (unweighted)
# ---------------------------------------------------------------------------

def bfs(maze: Maze) -> Generator[Step, None, None]:
    """Breadth-First Search — shortest path in unweighted maze."""
    start, goal = maze.start, maze.goal
    queue: deque[Cell] = deque([start])
    came_from: dict[Cell, Cell | None] = {start: None}

    while queue:
        current = queue.popleft()
        yield ("explore", [current])

        if current == goal:
            path = _reconstruct_path(came_from, goal)
            yield ("path", path)
            return

        for neighbor in maze.neighbors(*current):
            if neighbor not in came_from:
                came_from[neighbor] = current
                queue.append(neighbor)

    yield ("path", [])  # no path found


# ---------------------------------------------------------------------------
# DFS — not shortest, but explores dramatically
# ---------------------------------------------------------------------------

def dfs(maze: Maze) -> Generator[Step, None, None]:
    """Depth-First Search — may not find the shortest path."""
    start, goal = maze.start, maze.goal
    stack: list[Cell] = [start]
    came_from: dict[Cell, Cell | None] = {start: None}

    while stack:
        current = stack.pop()
        yield ("explore", [current])

        if current == goal:
            path = _reconstruct_path(came_from, goal)
            yield ("path", path)
            return

        for neighbor in maze.neighbors(*current):
            if neighbor not in came_from:
                came_from[neighbor] = current
                stack.append(neighbor)

    yield ("path", [])


# ---------------------------------------------------------------------------
# Dijkstra — uniform cost (same as BFS for unit weights, but shows cost)
# ---------------------------------------------------------------------------

def dijkstra(maze: Maze) -> Generator[Step, None, None]:
    """Dijkstra's Algorithm — shortest path with cost tracking."""
    start, goal = maze.start, maze.goal
    dist: dict[Cell, float] = {start: 0}
    came_from: dict[Cell, Cell | None] = {start: None}
    heap: list[tuple[float, Cell]] = [(0, start)]

    while heap:
        cost, current = heapq.heappop(heap)
        yield ("explore", [current])

        if current == goal:
            path = _reconstruct_path(came_from, goal)
            yield ("path", path)
            return

        if cost > dist.get(current, float("inf")):
            continue  # stale entry

        for neighbor in maze.neighbors(*current):
            new_cost = cost + 1  # unit weight
            if new_cost < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_cost
                came_from[neighbor] = current
                heapq.heappush(heap, (new_cost, neighbor))

    yield ("path", [])


# ---------------------------------------------------------------------------
# A* — heuristic-guided, typically fastest to goal
# ---------------------------------------------------------------------------

def _manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(maze: Maze) -> Generator[Step, None, None]:
    """A* Search — uses Manhattan heuristic for informed pathfinding."""
    start, goal = maze.start, maze.goal
    g: dict[Cell, float] = {start: 0}
    f_score: dict[Cell, float] = {start: _manhattan(start, goal)}
    came_from: dict[Cell, Cell | None] = {start: None}
    # heap items: (f, g, cell)
    heap: list[tuple[float, float, Cell]] = [(f_score[start], 0, start)]
    closed: set[Cell] = set()

    while heap:
        _, g_cur, current = heapq.heappop(heap)
        if current in closed:
            continue
        closed.add(current)
        yield ("explore", [current])

        if current == goal:
            path = _reconstruct_path(came_from, goal)
            yield ("path", path)
            return

        for neighbor in maze.neighbors(*current):
            if neighbor in closed:
                continue
            tentative_g = g_cur + 1
            if tentative_g < g.get(neighbor, float("inf")):
                g[neighbor] = tentative_g
                came_from[neighbor] = current
                f = tentative_g + _manhattan(neighbor, goal)
                f_score[neighbor] = f
                heapq.heappush(heap, (f, tentative_g, neighbor))

    yield ("path", [])


# ---------------------------------------------------------------------------
# Registry — easy lookup by name
# ---------------------------------------------------------------------------

ALGORITHMS = {
    "BFS": bfs,
    "DFS": dfs,
    "Dijkstra": dijkstra,
    "A*": astar,
}
