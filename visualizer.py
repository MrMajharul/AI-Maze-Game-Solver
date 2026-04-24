"""
visualizer.py — Pygame-based visualiser for the AI Maze Solver.

Layout
------
┌──────────────────────────┬──────────────┐
│                          │  SIDEBAR     │
│       MAZE CANVAS        │  controls    │
│                          │  stats       │
└──────────────────────────┴──────────────┘
"""

import math
import time
from typing import List, Optional, Tuple

import pygame

from maze import Maze
from solver import ALGORITHMS

# ---------------------------------------------------------------------------
# Palette — deep dark theme with vibrant accents
# ---------------------------------------------------------------------------
BG          = (10,  12,  20)
PANEL_BG    = (18,  22,  36)
PANEL_BORDER= (40,  50,  80)

WALL        = (15,  18,  30)
PATH        = (28,  34,  55)
START_CLR   = (0,  220, 120)
GOAL_CLR    = (255, 80,  80)
EXPLORED    = (60,  90, 180)
FRONTIER    = (100, 140, 240)
FINAL_PATH  = (255, 210,  50)

TEXT_PRIMARY   = (230, 235, 255)
TEXT_SECONDARY = (120, 135, 175)
TEXT_SECTION   = (168, 188, 235)
ACCENT         = (100, 160, 255)
ACCENT2        = (160, 100, 255)

BTN_IDLE    = (30,  40,  70)
BTN_HOVER   = (50,  70, 120)
BTN_ACTIVE  = (80, 120, 200)
BTN_TEXT    = (220, 228, 255)
BTN_BORDER  = (60,  80, 140)

SLIDER_RAIL = (40,  50,  80)
SLIDER_KNOB = (100, 160, 255)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SIDEBAR_W   = 260
MIN_CELL    = 8
FPS         = 60

MAZE_SIZES  = [("Small  11×11", 11), ("Medium 21×21", 21),
               ("Large  31×31", 31), ("XLarge 41×41", 41)]
GEN_MODES   = ["Recursive BT", "Prim's"]
ALGO_NAMES  = list(ALGORITHMS.keys())   # BFS, DFS, Dijkstra, A*

SPEED_MIN, SPEED_MAX = 1, 200           # nodes animated per frame


# ---------------------------------------------------------------------------
# Small UI helpers
# ---------------------------------------------------------------------------

def lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_rounded_rect(surf, color, rect, radius=8, border=0, border_color=None):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)


def draw_text(surf, text, font, color, x, y, anchor="topleft"):
    img = font.render(text, True, color)
    r = img.get_rect(**{anchor: (x, y)})
    surf.blit(img, r)
    return r


# ---------------------------------------------------------------------------
# Button
# ---------------------------------------------------------------------------

class Button:
    def __init__(self, rect, label, tag=None, toggle=False, active=False):
        self.rect   = pygame.Rect(rect)
        self.label  = label
        self.tag    = tag
        self.toggle = toggle
        self.active = active
        self._hover = False
        self._t     = 0.0          # animation interpolant

    def handle_event(self, event):
        clicked = False
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.toggle:
                    self.active = not self.active
                clicked = True
        return clicked

    def draw(self, surf, font):
        target_t = 1.0 if (self._hover or self.active) else 0.0
        self._t  = self._t + (target_t - self._t) * 0.25
        base  = BTN_ACTIVE if self.active else BTN_IDLE
        hover = BTN_HOVER  if not self.active else BTN_ACTIVE
        color = lerp_color(base, hover, self._t)
        draw_rounded_rect(surf, color, self.rect, 7, 1, BTN_BORDER)
        cx, cy = self.rect.center
        draw_text(surf, self.label, font, BTN_TEXT, cx, cy, "center")


# ---------------------------------------------------------------------------
# Slider
# ---------------------------------------------------------------------------

class Slider:
    def __init__(self, x, y, w, lo, hi, value, label):
        self.rect  = pygame.Rect(x, y, w, 6)
        self.lo, self.hi = lo, hi
        self.value = value
        self.label = label
        self._drag = False

    @property
    def knob_x(self):
        t = (self.value - self.lo) / (self.hi - self.lo)
        return int(self.rect.x + t * self.rect.w)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            kx = self.knob_x
            ky = self.rect.centery
            if math.hypot(event.pos[0] - kx, event.pos[1] - ky) < 14:
                self._drag = True
        if event.type == pygame.MOUSEBUTTONUP:
            self._drag = False
        if event.type == pygame.MOUSEMOTION and self._drag:
            t = (event.pos[0] - self.rect.x) / self.rect.w
            self.value = int(self.lo + max(0, min(1, t)) * (self.hi - self.lo))

    def draw(self, surf, font_sm, font_xs):
        # Rail
        pygame.draw.rect(surf, SLIDER_RAIL, self.rect, border_radius=3)
        # Filled portion
        filled = pygame.Rect(self.rect.x, self.rect.y,
                             self.knob_x - self.rect.x, self.rect.h)
        pygame.draw.rect(surf, ACCENT, filled, border_radius=3)
        # Knob
        pygame.draw.circle(surf, SLIDER_KNOB, (self.knob_x, self.rect.centery), 9)
        pygame.draw.circle(surf, TEXT_PRIMARY, (self.knob_x, self.rect.centery), 4)
        # Labels
        draw_text(surf, self.label, font_sm, TEXT_SECONDARY,
                  self.rect.x, self.rect.y - 18)
        draw_text(surf, str(self.value), font_sm, ACCENT,
                  self.rect.right, self.rect.y - 18, "topright")


# ---------------------------------------------------------------------------
# Main Visualiser class
# ---------------------------------------------------------------------------

class Visualiser:
    # ── init ──────────────────────────────────────────────────────────────

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("AI Maze Solver")
        info = pygame.display.Info()
        self.screen_w = min(1280, info.current_w - 40)
        self.screen_h = min(780,  info.current_h - 60)
        self.screen   = pygame.display.set_mode(
            (self.screen_w, self.screen_h), pygame.RESIZABLE)

        self._init_fonts()
        self._init_state()
        self._build_ui()
        self._new_maze()

        self.clock = pygame.time.Clock()

    # ── fonts ─────────────────────────────────────────────────────────────

    def _init_fonts(self):
        pygame.font.init()
        # Try a nice font; fall back to system default
        names = ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans", None]
        def f(size, bold=False):
            for n in names:
                try:
                    return pygame.font.SysFont(n, size, bold=bold)
                except Exception:
                    pass
            return pygame.font.Font(None, size)

        self.font_title  = f(22, bold=True)
        self.font_label  = f(16, bold=True)
        self.font_body   = f(14)
        self.font_small  = f(13)
        self.font_xs     = f(11)
        self.font_stat   = f(18, bold=True)

    # ── app state ─────────────────────────────────────────────────────────

    def _init_state(self):
        self.maze:          Optional[Maze]       = None
        self.explored:      List[Tuple[int,int]] = []
        self.final_path:    List[Tuple[int,int]] = []
        self.generator                           = None
        self.solving        = False
        self.solved         = False
        self.paused         = False

        # Perf stats
        self.nodes_explored = 0
        self.path_length    = 0
        self.elapsed_ms     = 0.0
        self._solve_start   = 0.0

        # Selection state
        self.sel_size_idx   = 1      # Medium 21×21
        self.sel_gen_idx    = 0      # Recursive BT
        self.sel_algo_idx   = 3      # A*

        # Comparison results
        self.cmp_results: dict = {}

        # Placement mode: None | "start" | "goal"
        self.placement_mode: Optional[str] = None

    # ── UI widgets ────────────────────────────────────────────────────────

    def _build_ui(self):
        sx = self.screen_w - SIDEBAR_W + 16
        w  = SIDEBAR_W - 32

        # ── Maze size buttons
        self.btn_sizes = []
        for i, (label, _) in enumerate(MAZE_SIZES):
            r = pygame.Rect(sx, 76 + i * 36, w, 28)
            b = Button(r, label, tag=i)
            b.active = (i == self.sel_size_idx)
            self.btn_sizes.append(b)

        # ── Generation buttons
        self.btn_gens = []
        for i, label in enumerate(GEN_MODES):
            r = pygame.Rect(sx + i * (w // 2 + 2), 236, w // 2 - 2, 28)
            b = Button(r, label, tag=i)
            b.active = (i == self.sel_gen_idx)
            self.btn_gens.append(b)

        # ── Algorithm buttons
        self.btn_algos = []
        for i, name in enumerate(ALGO_NAMES):
            col = i % 2
            row = i // 2
            bw = w // 2 - 2
            r  = pygame.Rect(sx + col * (bw + 4), 306 + row * 36, bw, 28)
            b  = Button(r, name, tag=i)
            b.active = (i == self.sel_algo_idx)
            self.btn_algos.append(b)

        # ── Speed slider
        self.slider_speed = Slider(sx, 391, w, SPEED_MIN, SPEED_MAX, 30, "Speed (nodes/frame)")

        # ── Action buttons
        self.btn_generate = Button(pygame.Rect(sx, 416, w, 30), "⟳  New Maze")
        self.btn_solve    = Button(pygame.Rect(sx, 452, w, 30), "▶  Solve")
        self.btn_pause    = Button(pygame.Rect(sx, 488, w, 30), "⏸  Pause / Resume")
        self.btn_reset    = Button(pygame.Rect(sx, 524, w, 30), "↺  Reset View")

        # ── Placement buttons (half-width pair)
        hw = w // 2 - 2
        self.btn_set_start = Button(pygame.Rect(sx,       572, hw, 30), "📍 Set Start")
        self.btn_set_goal  = Button(pygame.Rect(sx + hw + 4, 572, hw, 30), "🎯 Set Goal")

        # Used to position section labels so they don't collide with nearby buttons.
        self.y_placement_label = self.btn_set_start.rect.y - (self.font_xs.get_height() + 4)

        self.btn_compare  = Button(pygame.Rect(sx, 608, w, 30), "⚖  Compare All")

    def _rebuild_ui_positions(self):
        """Rebuild UI after window resize."""
        self._build_ui()
        # Restore selections
        for i, b in enumerate(self.btn_sizes):
            b.active = (i == self.sel_size_idx)
        for i, b in enumerate(self.btn_gens):
            b.active = (i == self.sel_gen_idx)
        for i, b in enumerate(self.btn_algos):
            b.active = (i == self.sel_algo_idx)
        self.slider_speed.value = min(SPEED_MAX, max(SPEED_MIN,
                                       self.slider_speed.value))

    # ── Maze / solver control ─────────────────────────────────────────────

    def _new_maze(self):
        self._stop_solving()
        rows = cols = MAZE_SIZES[self.sel_size_idx][1]
        self.maze = Maze(rows, cols)
        if self.sel_gen_idx == 0:
            self.maze.generate_recursive_backtracking()
        else:
            self.maze.generate_prims()
        self.explored   = []
        self.final_path = []
        self.cmp_results = {}
        self._reset_stats()

    def _start_solve(self):
        if self.maze is None:
            return
        self._stop_solving()
        self.maze.reset_markers()
        self.explored   = []
        self.final_path = []
        self._reset_stats()
        algo_fn         = ALGORITHMS[ALGO_NAMES[self.sel_algo_idx]]
        self.generator  = algo_fn(self.maze)
        self.solving    = True
        self.solved     = False
        self.paused     = False
        self._solve_start = time.perf_counter()

    def _stop_solving(self):
        self.solving   = False
        self.generator = None

    def _reset_stats(self):
        self.nodes_explored = 0
        self.path_length    = 0
        self.elapsed_ms     = 0.0

    def _toggle_pause(self):
        if self.solving:
            self.paused = not self.paused

    def _reset_view(self):
        self._stop_solving()
        self.explored    = []
        self.final_path  = []
        self.cmp_results = {}
        self.placement_mode = None
        self.maze.reset_markers()
        self._reset_stats()

    def _pixel_to_cell(self, mx, my):
        """Convert screen pixel (mx, my) to maze (row, col), or None if outside."""
        if self.maze is None:
            return None
        cs     = self._cell_size()
        maze_w = self.screen_w - SIDEBAR_W
        off_x  = (maze_w - self.maze.cols * cs) // 2
        off_y  = (self.screen_h - self.maze.rows * cs) // 2
        c = (mx - off_x) // cs
        r = (my - off_y) // cs
        if 0 <= r < self.maze.rows and 0 <= c < self.maze.cols:
            return (r, c)
        return None

    # ── Step solver generator ─────────────────────────────────────────────

    def _tick_solver(self):
        if not self.solving or self.paused or self.generator is None:
            return
        steps = self.slider_speed.value
        for _ in range(steps):
            try:
                kind, cells = next(self.generator)
            except StopIteration:
                self.solving = False
                self.solved  = True
                self.elapsed_ms = (time.perf_counter() - self._solve_start) * 1000
                return

            if kind == "explore":
                for cell in cells:
                    if cell not in (self.maze.start, self.maze.goal):
                        self.explored.append(cell)
                self.nodes_explored = len(self.explored)
            elif kind == "path":
                self.final_path  = cells
                self.path_length = len(cells)
                self.solving     = False
                self.solved      = True
                self.elapsed_ms  = (time.perf_counter() - self._solve_start) * 1000
                return

    # ── Comparison (instant, no animation) ───────────────────────────────

    def _run_compare(self):
        if self.maze is None:
            return
        self._stop_solving()
        self.cmp_results = {}
        for name, fn in ALGORITHMS.items():
            self.maze.reset_markers()
            gen   = fn(self.maze)
            count = 0
            path  = []
            t0    = time.perf_counter()
            for kind, cells in gen:
                if kind == "explore":
                    count += len(cells)
                elif kind == "path":
                    path = cells
            elapsed = (time.perf_counter() - t0) * 1000
            self.cmp_results[name] = {
                "nodes":   count,
                "path":    len(path),
                "time_ms": elapsed,
            }
        self.explored   = []
        self.final_path = []
        self.maze.reset_markers()

    # ── Drawing ───────────────────────────────────────────────────────────

    def _cell_size(self):
        maze_w = self.screen_w - SIDEBAR_W
        maze_h = self.screen_h
        if self.maze is None:
            return MIN_CELL
        cs = min(maze_w // self.maze.cols, maze_h // self.maze.rows)
        return max(MIN_CELL, cs)

    def _draw_maze(self):
        if self.maze is None:
            return
        cs    = self._cell_size()
        maze_w = self.screen_w - SIDEBAR_W
        maze_h = self.screen_h
        off_x = (maze_w - self.maze.cols * cs) // 2
        off_y = (maze_h - self.maze.rows * cs) // 2

        explored_set   = set(self.explored)
        final_path_set = set(self.final_path)

        for r in range(self.maze.rows):
            for c in range(self.maze.cols):
                cell = (r, c)
                v    = self.maze.grid[r][c]
                rect = pygame.Rect(off_x + c * cs, off_y + r * cs, cs, cs)

                if v == 1:                      # wall
                    color = WALL
                elif v == 2:                    # start
                    color = START_CLR
                elif v == 3:                    # goal
                    color = GOAL_CLR
                elif cell in final_path_set:    # final path
                    color = FINAL_PATH
                elif cell in explored_set:      # explored
                    # gradient: darker early, brighter late
                    idx = self.explored.index(cell)
                    t   = idx / max(1, len(self.explored) - 1)
                    color = lerp_color(EXPLORED, FRONTIER, t)
                else:
                    color = PATH

                pygame.draw.rect(self.screen, color, rect)
                if cs >= 10:
                    pygame.draw.rect(self.screen, BG, rect, 1)

        # Glow on start / goal
        self._draw_glow(off_x + self.maze.start[1] * cs + cs // 2,
                        off_y + self.maze.start[0] * cs + cs // 2,
                        START_CLR, cs)
        self._draw_glow(off_x + self.maze.goal[1] * cs + cs // 2,
                        off_y + self.maze.goal[0] * cs + cs // 2,
                        GOAL_CLR, cs)

        # ── Placement mode overlay hint
        if self.placement_mode:
            clr  = START_CLR if self.placement_mode == "start" else GOAL_CLR
            icon = "📍" if self.placement_mode == "start" else "🎯"
            msg  = f"{icon}  Click any open cell to place {'START' if self.placement_mode == 'start' else 'GOAL'}   [Esc] to cancel"
            hint = self.font_label.render(msg, True, clr)
            hw, hh = hint.get_size()
            pad = 10
            bg_rect = pygame.Rect((maze_w - hw) // 2 - pad, 14, hw + pad * 2, hh + pad)
            s = pygame.Surface((bg_rect.w, bg_rect.h), pygame.SRCALPHA)
            s.fill((10, 12, 20, 200))
            self.screen.blit(s, bg_rect.topleft)
            pygame.draw.rect(self.screen, clr, bg_rect, 2, border_radius=8)
            self.screen.blit(hint, ((maze_w - hw) // 2, 14 + pad // 2))

    def _draw_glow(self, cx, cy, color, cs):
        radius = max(cs, 10)
        glow   = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        for i in range(6, 0, -1):
            alpha = int(18 * i)
            r     = radius + i * 4
            pygame.draw.circle(glow, (*color, alpha), (radius * 2, radius * 2), r)
        self.screen.blit(glow, (cx - radius * 2, cy - radius * 2),
                         special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_sidebar(self):
        sx = self.screen_w - SIDEBAR_W
        sidebar_rect = pygame.Rect(sx, 0, SIDEBAR_W, self.screen_h)
        draw_rounded_rect(self.screen, PANEL_BG, sidebar_rect, 0, 1, PANEL_BORDER)

        # ── Title
        draw_text(self.screen, "AI MAZE SOLVER",
                  self.font_title, ACCENT, sx + SIDEBAR_W // 2, 14, "midtop")
        draw_text(self.screen, "Pathfinding Visualiser",
                  self.font_small, TEXT_SECONDARY, sx + SIDEBAR_W // 2, 42, "midtop")

        # ── Section: Maze Size
        self._section_label("MAZE SIZE", sx + 16, 58)
        for b in self.btn_sizes:
            b.draw(self.screen, self.font_body)

        # ── Section: Generator
        self._section_label("GENERATOR", sx + 16, 218)
        for b in self.btn_gens:
            b.draw(self.screen, self.font_body)

        # ── Section: Algorithm
        self._section_label("ALGORITHM", sx + 16, 288)
        for b in self.btn_algos:
            b.draw(self.screen, self.font_body)

        # ── Speed slider
        self.slider_speed.draw(self.screen, self.font_small, self.font_xs)

        # ── Action buttons
        self.btn_generate.draw(self.screen, self.font_label)
        self.btn_solve.draw(self.screen, self.font_label)
        self.btn_pause.draw(self.screen, self.font_label)
        self.btn_reset.draw(self.screen, self.font_label)

        # ── Placement section
        self._section_label("PLACEMENT", sx + 16, self.y_placement_label)
        # Highlight active placement button
        self.btn_set_start.active = (self.placement_mode == "start")
        self.btn_set_goal.active  = (self.placement_mode == "goal")
        self.btn_set_start.draw(self.screen, self.font_body)
        self.btn_set_goal.draw(self.screen, self.font_body)

        self.btn_compare.draw(self.screen, self.font_label)

        # ── Stats panel
        self._draw_stats(sx + 16, 646)

    def _section_label(self, text, x, y):
        label_rect = draw_text(self.screen, text, self.font_xs, TEXT_SECTION, x, y)
        line_y = label_rect.centery
        line_start = label_rect.right + 8
        if line_start < self.screen_w - 16:
            pygame.draw.line(self.screen, PANEL_BORDER,
                             (line_start, line_y), (self.screen_w - 16, line_y), 1)

    def _draw_stats(self, x, y):
        self._section_label("STATS", x, y)
        y += 14

        algo_name = ALGO_NAMES[self.sel_algo_idx]
        items = [
            ("Algorithm",  algo_name,                ACCENT),
            ("Explored",   str(self.nodes_explored), TEXT_PRIMARY),
            ("Path len",   str(self.path_length),    FINAL_PATH if self.path_length else TEXT_PRIMARY),
            ("Time",       f"{self.elapsed_ms:.1f} ms", START_CLR),
        ]
        for label, value, clr in items:
            draw_text(self.screen, label, self.font_small, TEXT_SECONDARY, x, y + 4)
            draw_text(self.screen, value, self.font_stat, clr,
                      self.screen_w - 16, y + 4, "topright")
            y += 24

        # Status badge
        if self.solving:
            status, sc = ("SOLVING…", ACCENT)
        elif self.solved:
            status, sc = ("SOLVED ✓", START_CLR) if self.path_length else ("NO PATH ✗", GOAL_CLR)
        else:
            status, sc = ("READY", TEXT_SECONDARY)

        badge = pygame.Rect(x, y + 4, SIDEBAR_W - 32, 24)
        draw_rounded_rect(self.screen, (*sc[:3], 30), badge, 6)
        draw_text(self.screen, status, self.font_label, sc,
                  badge.centerx, badge.centery, "center")

    def _draw_comparison(self):
        if not self.cmp_results:
            return
        panel_w = 520
        panel_h = 260
        px = (self.screen_w - SIDEBAR_W - panel_w) // 2
        py = (self.screen_h - panel_h) // 2
        panel = pygame.Rect(px, py, panel_w, panel_h)
        draw_rounded_rect(self.screen, PANEL_BG, panel, 12, 2, PANEL_BORDER)

        draw_text(self.screen, "Algorithm Comparison", self.font_title, ACCENT,
                  panel.centerx, py + 14, "midtop")

        headers = ["Algorithm", "Nodes Explored", "Path Length", "Time (ms)"]
        col_xs  = [px + 16, px + 150, px + 300, px + 410]
        hy = py + 50
        for h, cx in zip(headers, col_xs):
            draw_text(self.screen, h, self.font_small, TEXT_SECONDARY, cx, hy)

        pygame.draw.line(self.screen, PANEL_BORDER,
                         (px + 16, hy + 18), (panel.right - 16, hy + 18), 1)

        ry = hy + 28
        colors = [ACCENT, ACCENT2, START_CLR, FINAL_PATH]
        best_nodes = min(v["nodes"] for v in self.cmp_results.values())
        best_path  = min((v["path"] for v in self.cmp_results.values() if v["path"] > 0), default=0)
        best_time  = min(v["time_ms"] for v in self.cmp_results.values())

        for i, (name, data) in enumerate(self.cmp_results.items()):
            clr  = colors[i % len(colors)]
            draw_text(self.screen, name, self.font_label, clr, col_xs[0], ry)

            nc = START_CLR if data["nodes"] == best_nodes else TEXT_PRIMARY
            draw_text(self.screen, str(data["nodes"]), self.font_body, nc, col_xs[1], ry)

            pl = data["path"]
            pc = START_CLR if (pl > 0 and pl == best_path) else (GOAL_CLR if pl == 0 else TEXT_PRIMARY)
            draw_text(self.screen, str(pl) if pl else "N/A", self.font_body, pc, col_xs[2], ry)

            tc = START_CLR if data["time_ms"] == best_time else TEXT_PRIMARY
            draw_text(self.screen, f"{data['time_ms']:.2f}", self.font_body, tc, col_xs[3], ry)
            ry += 30

        draw_text(self.screen, "★ = best  |  click anywhere to dismiss",
                  self.font_xs, TEXT_SECONDARY, panel.centerx, panel.bottom - 16, "midbottom")

    # ── Event handling ────────────────────────────────────────────────────

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.VIDEORESIZE:
                self.screen_w, self.screen_h = event.w, event.h
                self.screen = pygame.display.set_mode(
                    (self.screen_w, self.screen_h), pygame.RESIZABLE)
                self._rebuild_ui_positions()

            # Dismiss comparison panel
            if self.cmp_results and event.type == pygame.MOUSEBUTTONDOWN:
                self.cmp_results = {}
                continue

            # Cancel placement mode with Escape
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.placement_mode = None

            # Canvas click → place start or goal
            if (event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and self.placement_mode
                    and self.maze):
                mx, my = event.pos
                if mx < self.screen_w - SIDEBAR_W:   # clicked on canvas
                    cell = self._pixel_to_cell(mx, my)
                    if cell:
                        if self.placement_mode == "start":
                            if self.maze.set_start(*cell):
                                self._reset_view()
                                self.placement_mode = None
                        else:
                            if self.maze.set_goal(*cell):
                                self._reset_view()
                                self.placement_mode = None
                    continue   # don't let other handlers process this click

            # Size buttons
            for i, b in enumerate(self.btn_sizes):
                if b.handle_event(event):
                    self.sel_size_idx = i
                    for other in self.btn_sizes:
                        other.active = False
                    b.active = True
                    self._new_maze()

            # Generator buttons
            for i, b in enumerate(self.btn_gens):
                if b.handle_event(event):
                    self.sel_gen_idx = i
                    for other in self.btn_gens:
                        other.active = False
                    b.active = True

            # Algorithm buttons
            for i, b in enumerate(self.btn_algos):
                if b.handle_event(event):
                    self.sel_algo_idx = i
                    for other in self.btn_algos:
                        other.active = False
                    b.active = True

            # Slider
            self.slider_speed.handle_event(event)

            # Action buttons
            if self.btn_generate.handle_event(event):
                self._new_maze()
            if self.btn_solve.handle_event(event):
                self._start_solve()
            if self.btn_pause.handle_event(event):
                self._toggle_pause()
            if self.btn_reset.handle_event(event):
                self._reset_view()
            if self.btn_compare.handle_event(event):
                self._run_compare()

            # Placement mode toggle
            if self.btn_set_start.handle_event(event):
                self.placement_mode = None if self.placement_mode == "start" else "start"
            if self.btn_set_goal.handle_event(event):
                self.placement_mode = None if self.placement_mode == "goal" else "goal"

            # Keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self._toggle_pause()
                if event.key == pygame.K_RETURN:
                    self._start_solve()
                if event.key == pygame.K_n:
                    self._new_maze()
                if event.key == pygame.K_r:
                    self._reset_view()

        return True

    # ── Animated intro gradient title on canvas ───────────────────────────

    def _draw_canvas_bg(self):
        self.screen.fill(BG)

    # ── Main loop ─────────────────────────────────────────────────────────

    def run(self):
        running = True
        while running:
            running = self._handle_events()
            self._tick_solver()

            self._draw_canvas_bg()
            self._draw_maze()
            self._draw_sidebar()
            if self.cmp_results:
                self._draw_comparison()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
