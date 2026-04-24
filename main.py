"""
main.py — Entry point for the AI Maze Solver.

Usage:
    python main.py

Keyboard Shortcuts:
    Enter      → Solve maze with selected algorithm
    Space      → Pause / Resume solving
    N          → Generate new maze
    R          → Reset view (clear paths)
"""

from visualizer import Visualiser


def main():
    app = Visualiser()
    app.run()


if __name__ == "__main__":
    main()
