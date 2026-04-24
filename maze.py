"""
maze.py — Maze generation using Recursive Backtracking and Prim's Algorithm
"""

import random


class Maze:
    """
    Represents a grid-based maze.

    Cell values:
        0 = open path
        1 = wall
        2 = start
        3 = goal
    """

    def __init__(self, rows: int, cols: int):
        # Ensure odd dimensions so walls/paths alternate correctly
        self.rows = rows if rows % 2 == 1 else rows + 1
        self.cols = cols if cols % 2 == 1 else cols + 1
        self.grid = [[1] * self.cols for _ in range(self.rows)]
        self.start = (1, 1)
        self.goal = (self.rows - 2, self.cols - 2)

    # ------------------------------------------------------------------
    # Generation algorithms
    # ------------------------------------------------------------------

    def generate_recursive_backtracking(self):
        """Generate maze using Recursive Backtracking (DFS-based)."""
        self.grid = [[1] * self.cols for _ in range(self.rows)]
        visited = [[False] * self.cols for _ in range(self.rows)]

        def carve(r, c):
            visited[r][c] = True
            self.grid[r][c] = 0
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            random.shuffle(directions)
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if (0 < nr < self.rows - 1
                        and 0 < nc < self.cols - 1
                        and not visited[nr][nc]):
                    # carve through the wall between current and next cell
                    self.grid[r + dr // 2][c + dc // 2] = 0
                    carve(nr, nc)

        import sys
        sys.setrecursionlimit(10_000)
        carve(1, 1)
        self._place_markers()

    def generate_prims(self):
        """Generate maze using a randomised Prim's Algorithm."""
        self.grid = [[1] * self.cols for _ in range(self.rows)]

        # Start from (1, 1)
        self.grid[1][1] = 0
        frontier = []

        def add_frontiers(r, c):
            for dr, dc in [(0, 2), (2, 0), (0, -2), (-2, 0)]:
                nr, nc = r + dr, c + dc
                if (0 < nr < self.rows - 1
                        and 0 < nc < self.cols - 1
                        and self.grid[nr][nc] == 1):
                    frontier.append((nr, nc, r, c))  # candidate, its origin

        add_frontiers(1, 1)

        while frontier:
            idx = random.randrange(len(frontier))
            nr, nc, pr, pc = frontier[idx]
            frontier.pop(idx)

            if self.grid[nr][nc] == 1:
                # Open the frontier cell and the wall between it and origin
                self.grid[nr][nc] = 0
                self.grid[(nr + pr) // 2][(nc + pc) // 2] = 0
                add_frontiers(nr, nc)

        self._place_markers()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _place_markers(self):
        self.grid[self.start[0]][self.start[1]] = 2
        self.grid[self.goal[0]][self.goal[1]] = 3

    def is_walkable(self, r: int, c: int) -> bool:
        """Return True if cell (r, c) is not a wall."""
        return self.grid[r][c] != 1

    def neighbors(self, r: int, c: int):
        """Yield walkable 4-connected neighbors of (r, c)."""
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (0 <= nr < self.rows
                    and 0 <= nc < self.cols
                    and self.grid[nr][nc] != 1):
                yield nr, nc

    def reset_markers(self):
        """Remove start/goal markers (used before re-placing them)."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] in (2, 3):
                    self.grid[r][c] = 0
        self._place_markers()

    def set_start(self, r: int, c: int) -> bool:
        """Move the start marker to (r, c). Returns False if cell is a wall or goal."""
        if self.grid[r][c] == 1 or (r, c) == self.goal:
            return False
        # Clear old start
        self.grid[self.start[0]][self.start[1]] = 0
        self.start = (r, c)
        self.grid[r][c] = 2
        return True

    def set_goal(self, r: int, c: int) -> bool:
        """Move the goal marker to (r, c). Returns False if cell is a wall or start."""
        if self.grid[r][c] == 1 or (r, c) == self.start:
            return False
        # Clear old goal
        self.grid[self.goal[0]][self.goal[1]] = 0
        self.goal = (r, c)
        self.grid[r][c] = 3
        return True
