import numpy as np

from vector_2 import Vector2


class SimpleClassifier:

    def classify(self, points: list[Vector2], tol=0.05, mono_tol=1e-6):
        # print(points)
        pts = [(p.x, p.y) for p in points]
        P = np.asarray(pts, float)
        # 1) compute deltas
        dP = np.diff(P, axis=0)
        dx, dy = dP[:, 0], dP[:, 1]

        # 2) path-vs-chord ratio
        seg_lengths = np.linalg.norm(dP, axis=1)
        L = seg_lengths.sum()
        D = np.linalg.norm(P[-1] - P[0])
        ratio = L / D if D > 0 else np.inf

        print(f"L : {L}, D: {D}, ratio: {ratio}")

        # 3) straightish if monotonic +x and almost no y-motion, and ratio≈1
        if dx.min() >= -mono_tol and np.max(np.abs(dy)) / max(np.abs(dx).max(), 1) < tol and abs(ratio - 1) < tol:
            return "straightish"

        # 4) quarter-circle if monotonic x↓, y↑ and ratio≈π/(2√2)
        q_ratio = np.pi / (2 * np.sqrt(2))
        if dx.max() <= mono_tol and dy.min() >= -mono_tol and abs(ratio - q_ratio) < tol:
            return "quarter-circle"

        return "unknown"
