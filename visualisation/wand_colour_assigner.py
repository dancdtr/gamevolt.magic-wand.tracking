from __future__ import annotations

import re
import time
from dataclasses import dataclass

_HEX6_RE = re.compile(r"^[0-9a-fA-F]{6}$")


@dataclass(frozen=True)
class ColourAllocationError(Exception):
    message: str


class WandColourAssigner:
    """
    3-state palette allocator:
      1) AVAILABLE: not active, not reserved
      2) RESERVED: held for an id that disconnected (prefer not to reuse)
      3) ACTIVE: currently in use

    Policy:
      - If wand_id has a RESERVED colour, it always reclaims it on acquire()
      - Otherwise, acquire prefers AVAILABLE colours
      - Only if no AVAILABLE colours exist, it may steal a RESERVED colour
      - Never steals ACTIVE colours; if palette exhausted by ACTIVE usage -> error
    """

    def __init__(self, palette: list[str]) -> None:
        self._palette: list[str] = [self._normalise_hex(c) for c in palette]
        self._validate_palette(self._palette)

        # ACTIVE state
        self._active_by_id: dict[str, str] = {}  # id -> colour

        # RESERVED state
        self._reserved_by_id: dict[str, str] = {}  # id -> colour
        self._reserved_meta_by_colour: dict[str, tuple[str, float]] = {}  # colour -> (id, reserved_at_monotonic)

    # ── public API ──────────────────────────────────────────────────────────

    def acquire(self, wand_id: str) -> str:
        """Mark wand_id as ACTIVE and return its colour."""
        wand_id = wand_id.upper()

        # Already active
        existing = self._active_by_id.get(wand_id)
        if existing is not None:
            return existing

        # Reclaim reserved colour if any (strong preference)
        reserved = self._reserved_by_id.pop(wand_id, None)
        if reserved is not None:
            # remove meta entry for this colour if it matches
            meta = self._reserved_meta_by_colour.get(reserved)
            if meta is not None and meta[0] == wand_id:
                self._reserved_meta_by_colour.pop(reserved, None)

            self._active_by_id[wand_id] = reserved
            return reserved

        active_colours = set(self._active_by_id.values())
        reserved_colours = set(self._reserved_meta_by_colour.keys())

        # Prefer AVAILABLE colours
        for c in self._palette:
            if c not in active_colours and c not in reserved_colours:
                self._active_by_id[wand_id] = c
                return c

        # No AVAILABLE colours: steal a RESERVED colour (oldest reservation wins)
        candidate_reserved = [(c, meta[1]) for c, meta in self._reserved_meta_by_colour.items() if c not in active_colours]
        if candidate_reserved:
            stolen_colour, _t = min(candidate_reserved, key=lambda x: x[1])  # oldest reserved
            victim_id, _victim_t = self._reserved_meta_by_colour.pop(stolen_colour)

            # Victim no longer has a reservation (their colour was stolen)
            if self._reserved_by_id.get(victim_id) == stolen_colour:
                self._reserved_by_id.pop(victim_id, None)

            self._active_by_id[wand_id] = stolen_colour
            return stolen_colour

        # No AVAILABLE and no stealable RESERVED => palette fully ACTIVE
        raise ColourAllocationError("No colours available: palette fully in ACTIVE use.")

    def reserve(self, wand_id: str) -> None:
        """
        Move wand_id from ACTIVE -> RESERVED (keeps its colour associated with the ID).
        """
        wand_id = wand_id.upper()
        colour = self._active_by_id.pop(wand_id, None)
        if colour is None:
            return

        self._reserved_by_id[wand_id] = colour
        self._reserved_meta_by_colour[colour] = (wand_id, time.monotonic())

    def free(self, wand_id: str) -> None:
        """
        Remove any association (ACTIVE or RESERVED). Colour becomes AVAILABLE.
        """
        wand_id = wand_id.upper()

        colour = self._active_by_id.pop(wand_id, None)
        if colour is not None:
            return

        colour = self._reserved_by_id.pop(wand_id, None)
        if colour is not None:
            meta = self._reserved_meta_by_colour.get(colour)
            if meta is not None and meta[0] == wand_id:
                self._reserved_meta_by_colour.pop(colour, None)

    def reset(self) -> None:
        """Clear all state."""
        self._active_by_id.clear()
        self._reserved_by_id.clear()
        self._reserved_meta_by_colour.clear()

    # ── debug helpers (optional) ─────────────────────────────────────────────

    def active(self) -> dict[str, str]:
        return dict(self._active_by_id)

    def reserved(self) -> dict[str, str]:
        return dict(self._reserved_by_id)

    # ── validation ──────────────────────────────────────────────────────────

    @staticmethod
    def _normalise_hex(colour: str) -> str:
        c = colour.strip()
        if c.startswith("#"):
            c = c[1:]
        if not _HEX6_RE.match(c):
            raise ColourAllocationError(f"Invalid colour '{colour}'. Expected hex like '#RRGGBB'.")
        return f"#{c.lower()}"

    @staticmethod
    def _validate_palette(palette: list[str]) -> None:
        if not palette:
            raise ColourAllocationError("Palette is empty.")

        banned = {"#ffffff", "#000000"}
        for c in palette:
            if c in banned:
                raise ColourAllocationError(f"Palette contains banned colour '{c}' (white/black not allowed).")

        if len(set(palette)) != len(palette):
            raise ColourAllocationError("Palette contains duplicates.")
