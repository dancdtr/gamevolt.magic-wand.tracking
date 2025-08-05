import numpy as np

from vector_2 import Vector2


class FirstQuadrantClassifier:
    """
    Classifies 2D gesture point sequences in the first quadrant into:
      - horizontal lines
      - vertical lines
      - diagonal lines (slope ~1)
      - quarter-circle arcs (bottom→right or left→top)
      - unknown

    Methods allow for optional smoothing and jitter-tolerant monotonicity.
    """

    def __init__(self) -> None:
        pass

    def smooth(self, pts: list[Vector2], window: int = 5) -> np.ndarray:
        """
        Apply a moving-average smoothing to reduce high-frequency jitter.

        Args:
            pts: list of Vector2 points
            window: odd integer window size for the moving average

        Returns:
            Smoothed points as an (n,2) NumPy array
        """
        # Convert Vector2 list to array shape (n,2)
        P = np.array([[p.x, p.y] for p in pts], dtype=float)
        if window < 3:
            return P
        pad = window // 2
        Pp = np.pad(P, ((pad, pad), (0, 0)), mode="edge")
        kernel = np.ones(window) / window
        xs = np.convolve(Pp[:, 0], kernel, mode="valid")
        ys = np.convolve(Pp[:, 1], kernel, mode="valid")
        return np.vstack((xs, ys)).T

    def monotonic_with_jitter(self, values: np.ndarray, increasing: bool = True, max_bad_frac: float = 0.1, tol: float = 1e-6) -> bool:
        """
        Check if a sequence is mostly monotonic, allowing some jitter.

        Args:
            values: array of deltas (dx or dy)
            increasing: True for non-decreasing, False for non-increasing
            max_bad_frac: maximum fraction of "bad" steps allowed
            tol: tolerance for considering a step zero

        Returns:
            True if monotonic within allowed jitter
        """
        if increasing:
            bad = np.sum(values < -tol)
        else:
            bad = np.sum(values > tol)
        return bool((bad / len(values)) <= max_bad_frac)

    def line_fit_quality(self, pts: np.ndarray) -> tuple[float, float]:
        """
        Fit y = m*x + c to pts and compute R^2.

        Args:
            pts: (n,2) array of points

        Returns:
            (m, R2) slope and coefficient of determination
        """
        x, y = pts[:, 0], pts[:, 1]
        m, c = np.polyfit(x, y, 1)
        y_pred = m * x + c
        ss_tot = np.sum((y - y.mean()) ** 2)
        ss_res = np.sum((y - y_pred) ** 2)
        R2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        return m, R2

    def classify(
        self,
        pts: list[Vector2] | np.ndarray,
        smooth_win: int | None = None,
        max_bad_frac: float = 0.1,
        slope_tol: float = 0.2,
        R2_thresh: float = 0.95,
        tol_ratio: float = 0.1,
    ) -> str:
        """
        Classify a noisy gesture sequence.

        Args:
            pts: list of Vector2 or (n,2) array
            smooth_win: window size for optional smoothing
            max_bad_frac: allowed monotonicity jitter fraction
            slope_tol: tolerance on line slope
            R2_thresh: min R^2 for line fit
            tol_ratio: tolerance on path-vs-chord ratio

        Returns:
            One of 'horizontal', 'vertical', 'diagonal',
            'arc_bottom_to_right', 'arc_left_to_top', or 'unknown'.
        """
        # Convert to array
        if isinstance(pts, list):
            P = np.array([[p.x, p.y] for p in pts], dtype=float)
        else:
            P = np.asarray(pts, dtype=float)

        # Optional smoothing
        if smooth_win:
            P = self.smooth([Vector2(x, y) for x, y in P], window=smooth_win)

        # Path vs chord
        dP = np.diff(P, axis=0)
        L = np.linalg.norm(dP, axis=1).sum()
        D = np.linalg.norm(P[-1] - P[0])
        if D < tol_ratio:
            return "unknown"
        ratio = L / D
        straight_R = 1.0
        arc_R = np.pi / (2 * np.sqrt(2))

        # Monotonicity with jitter
        dx, dy = dP[:, 0], dP[:, 1]
        inc_x = self.monotonic_with_jitter(dx, increasing=True, max_bad_frac=max_bad_frac)
        dec_x = self.monotonic_with_jitter(dx, increasing=False, max_bad_frac=max_bad_frac)
        inc_y = self.monotonic_with_jitter(dy, increasing=True, max_bad_frac=max_bad_frac)
        dec_y = self.monotonic_with_jitter(dy, increasing=False, max_bad_frac=max_bad_frac)

        # Straight-ish
        if abs(ratio - straight_R) < tol_ratio:
            m, R2 = self.line_fit_quality(P)
            if inc_x and abs(m) < slope_tol and R2 > R2_thresh:
                return "horizontal"
            m2, R2v = self.line_fit_quality(np.column_stack((P[:, 1], P[:, 0])))
            if inc_y and abs(m2) < slope_tol and R2v > R2_thresh:
                return "vertical"
            if inc_x and inc_y and abs(m - 1) < slope_tol and R2 > R2_thresh:
                return "diagonal"

        # Quarter-circle-ish
        if abs(ratio - arc_R) < tol_ratio:
            if inc_x and dec_y:
                return "arc_bottom_to_right"
            if dec_x and inc_y:
                return "arc_left_to_top"

        return "unknown"
