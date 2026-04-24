# 🧠 AI Maze Game Solver

A fully interactive, animated maze pathfinding visualiser built in **Python + Pygame**.  
Watch BFS, DFS, Dijkstra, and A* explore and solve mazes in real time — step by step.

---

## 📸 Preview

```
┌──────────────────────────┬──────────────┐
│                          │  SIDEBAR     │
│       MAZE CANVAS        │  controls    │
│   (animated solving)     │  stats       │
└──────────────────────────┴──────────────┘
```

### Screenshots

| Example 1 | Example 2 |
|---|---|
| ![Maze solver UI screenshot 1](assets/screenshots/ui-1.png) | ![Maze solver UI screenshot 2](assets/screenshots/ui-2.png) |

> Save the two screenshots into `assets/screenshots/` as `ui-1.png` and `ui-2.png` for them to render here.

- 🟢 **Green** = Start cell  
- 🔴 **Red** = Goal cell  
- 🔵 **Blue gradient** = Explored nodes (dark → bright = early → late)  
- 🟡 **Gold** = Final shortest path  

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.8 or later
- pip

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
python main.py
```

---

## 📁 Project Structure

```
AI Maze Game Solver/
│
├── maze.py          # Maze grid + generation algorithms
├── solver.py        # Pathfinding algorithms (BFS, DFS, Dijkstra, A*)
├── visualizer.py    # Pygame UI, animation engine, sidebar controls
├── main.py          # Entry point
├── requirements.txt # Dependencies
└── README.md        # This file
```

---

## 🗺️ Maze Generation

Two procedural generation algorithms are available:

| Algorithm | Description |
|-----------|-------------|
| **Recursive Backtracking** | DFS-based carving. Produces long winding corridors with fewer dead ends. |
| **Prim's Algorithm** | Randomly grows a spanning tree. Produces more branchy, organic mazes. |

Generated mazes always have:
- **Odd dimensions** (required for correct wall/path grid layout)
- A **Start** at top-left area and **Goal** at bottom-right area by default

---

## 🤖 Pathfinding Algorithms

| Algorithm | Type | Shortest Path? | Notes |
|-----------|------|:--------------:|-------|
| **BFS** | Uninformed | ✅ Yes | Explores layer by layer; guaranteed shortest path in unweighted grids |
| **DFS** | Uninformed | ❌ No | Fast and dramatic; may find a very long path |
| **Dijkstra** | Cost-based | ✅ Yes | Same as BFS for unit weights; tracks cumulative cost |
| **A\*** | Heuristic | ✅ Yes | Uses Manhattan distance; focuses search toward the goal — most "AI-like" |

All algorithms are **generators** — they yield each explored cell one at a time so the visualiser can animate them step by step.

---

## 🎮 Controls

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Solve maze with the selected algorithm |
| `Space` | Pause / Resume animation |
| `N` | Generate a new maze |
| `R` | Reset view (clear paths, keep maze) |
| `Esc` | Cancel placement mode |

### Sidebar Controls

| Control | Description |
|---------|-------------|
| **Maze Size** | Choose 11×11, 21×21, 31×31, or 41×41 |
| **Generator** | Recursive Backtracking or Prim's Algorithm |
| **Algorithm** | BFS, DFS, Dijkstra, A* |
| **Speed slider** | 1–200 nodes animated per frame |
| **⟳ New Maze** | Generate a fresh random maze |
| **▶ Solve** | Start solving animation |
| **⏸ Pause / Resume** | Freeze/unfreeze the animation |
| **↺ Reset View** | Clear explored cells and path |
| **📍 Set Start** | Click to activate, then click any open cell to move the start |
| **🎯 Set Goal** | Click to activate, then click any open cell to move the goal |
| **⚖ Compare All** | Instantly runs all 4 algorithms and shows a comparison table |

---

## 📊 Performance Comparison

Click **⚖ Compare All** to run all four algorithms on the current maze simultaneously and display:

- **Nodes Explored** — how many cells each algorithm visited
- **Path Length** — number of steps in the found path
- **Time (ms)** — wall-clock time to solve

The best result in each column is highlighted in **green**.

---

## 🖱️ Custom Start & Goal Placement

1. Click **📍 Set Start** or **🎯 Set Goal** in the sidebar  
2. A banner appears at the top of the maze canvas showing the active mode  
3. Click **any open (non-wall) cell** in the maze to move the marker  
4. The view resets automatically so you can re-solve from the new positions  
5. Press `Esc` to cancel without changing anything

**Rules:**
- Start cannot be placed on a wall or on the Goal cell
- Goal cannot be placed on a wall or on the Start cell

---

## 🧩 How It Works (AI Concepts)

### Why BFS finds the shortest path
BFS explores all cells at distance *d* before any cell at distance *d+1*. In an unweighted grid (all moves cost 1), the first time it reaches the goal is guaranteed to be via the shortest route.

### Why A* is considered "AI"
A* uses a **heuristic function** h(n) = Manhattan distance to the goal. This is an *informed* estimate that biases the search toward the goal, exploring far fewer cells than BFS in most mazes. A* is optimal when the heuristic is *admissible* (never overestimates) — Manhattan distance satisfies this for grid mazes.

### Generator pattern
Each algorithm is implemented as a Python **generator** (`yield`). This allows the visualiser to request one step at a time (`next(generator)`) and render it, without blocking the UI — making smooth frame-by-frame animation possible without threads.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pygame` | ≥ 2.0.0 | Window, rendering, events |

No other external libraries required — all algorithms use Python's standard library (`collections.deque`, `heapq`).

---

## 💡 Ideas for Extension

- [ ] **Q-Learning agent** — let an AI *learn* to solve the maze through rewards
- [ ] **Multiple checkpoints** — visit waypoints before reaching the goal
- [ ] **Weighted cells** — mud/water tiles with higher movement cost
- [ ] **Moving obstacles** — dynamic walls that shift every N steps
- [ ] **Maze editor** — draw/erase walls with the mouse
- [ ] **Export** — save maze + solution as an image

---

## 📝 License

MIT — free to use, modify, and share.
