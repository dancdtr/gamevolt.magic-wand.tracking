import re

import matplotlib.pyplot as plt
import numpy as np

from wand_points import WAND_POINTS


def parse_triplets(data: str):
    """Return np.arrays: xs, ys, ms from lines like 'x=-6771, y=633, ms=2625'."""
    triplets = re.findall(r"x=(-?\d+),\s*y=(-?\d+),\s*ms=(-?\d+)", data)
    xs = np.array([int(x) for x, _, _ in triplets], dtype=int)
    ys = np.array([int(y) for _, y, _ in triplets], dtype=int)
    ms = np.array([int(m) for _, _, m in triplets], dtype=int)
    return xs, ys, ms


def main():
    xs, ys, ms = parse_triplets(WAND_POINTS)

    fig, ax = plt.subplots(figsize=(8, 6))

    if fig.canvas.manager:
        fig.canvas.manager.set_window_title("Wand Points")

    # Draw path in given order, then scatter coloured by ms
    ax.plot(xs, ys, linewidth=1, alpha=0.35, label="path")
    pts = ax.scatter(xs, ys, c=ms, s=12, cmap="viridis")

    # Mark start/end
    ax.scatter(xs[0], ys[0], s=80, marker="o", facecolors="none", edgecolors="black", label="start")
    ax.scatter(xs[-1], ys[-1], s=80, marker="X", edgecolors="black", label="end")

    ax.set_title("Recorded Wand Point Trail")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal", adjustable="datalim")

    cbar = plt.colorbar(pts, ax=ax, label="ms")
    ax.legend()

    # If these are screen coords (y down), uncomment to flip:
    # ax.invert_yaxis()

    plt.tight_layout()

    # Uncomment to save the image
    # plt.savefig("path.png", dpi=200)

    plt.show()


if __name__ == "__main__":
    main()

# Ctrl+ C in terminal to end
