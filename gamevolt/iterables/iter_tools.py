from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator, Sequence
from itertools import cycle, islice, zip_longest
from typing import TypeVar

T = TypeVar("T")
_SENTINEL = object()

# --------- Cropping (lazy) ---------


def drop_first(it: Iterable[T], n: int) -> Iterator[T]:
    return islice(it, n, None)


def drop_last(it: Iterable[T], n: int) -> Iterator[T]:
    if n <= 0:
        yield from it
        return
    q: deque[T] = deque(maxlen=n)
    for x in it:
        if len(q) == q.maxlen:
            yield q.popleft()
        q.append(x)


def crop(it: Iterable[T], *, head: int = 0, tail: int = 0) -> Iterator[T]:
    return drop_last(drop_first(it, head), tail)


# --------- Exact equality (same length, same elements) ---------


def equals(it: Iterable[T], seq: Sequence[T]) -> bool:
    _S = object()
    for a, b in zip_longest(it, seq, fillvalue=_S):
        if a != b:
            return False
    return True


def equals_single(it: Iterable[T], value: T) -> bool:
    it = iter(it)
    first = next(it, _SENTINEL)
    if first is _SENTINEL or first != value:
        return False
    return next(it, _SENTINEL) is _SENTINEL


def matches(it: Iterable[T], *values: T) -> bool:
    """True iff iterable yields exactly the given values (== compare)."""
    return equals(it, values)


# --------- Bounded prefix matching (your strict tool) ---------
# - allow_tail_missing: permit the source to be up to N items SHORTER than pattern
# - allow_tail_extra:   permit the source to have up to N EXTRA items after a full match
#   (use None for unlimited extras)
# Defaults (0, 0) => EXACT match behavior.


def matches_prefix(
    it: Iterable[T],
    prefix: Sequence[T],
    *,
    allow_tail_missing: int = 0,
    allow_tail_extra: int | None = 0,
    allow_head_missing: int = 0,
    allow_head_extra: int | None = 0,
) -> bool:
    """
    Returns True if `prefix` matches a contiguous slice of `it` with allowances:
      - allow_head_missing: drop up to N items from the *start of prefix*.
      - allow_head_extra: skip up to N items at the *start of it* (None = anywhere).
      - allow_tail_missing: accept if it ends early by up to N missing suffix items of prefix.
      - allow_tail_extra: allow up to N extra items *after* the matched prefix in it (None = ignore extras).
    """
    src = tuple(it)  # materialize so we can try multiple alignments

    def match_from(start: int, wanted: Sequence[T]) -> bool:
        i = 0
        j = start
        wl = len(wanted)
        sl = len(src)

        while i < wl:
            if j >= sl:
                # source ended: accept only if remaining prefix fits tail-missing allowance
                return (wl - i) <= allow_tail_missing
            if src[j] != wanted[i]:
                return False
            i += 1
            j += 1

        # full wanted matched; enforce tail-extra policy
        if allow_tail_extra is None:
            return True
        return (len(src) - j) <= allow_tail_extra

    # decide which starting indices in src we’re allowed to try
    if allow_head_extra is None:
        start_indices = range(0, len(src) + 1)  # anywhere (including at the very end for empty matches)
    else:
        start_indices = range(0, min(allow_head_extra, len(src)) + 1)

    max_head_missing = min(allow_head_missing, len(prefix))
    for miss in range(0, max_head_missing + 1):
        trimmed = prefix[miss:]  # drop first `miss` items from prefix
        for start in start_indices:
            if match_from(start, trimmed):
                return True
    return False


# --------- Suffix (exact) ---------


def ends_with(it: Iterable[T], suffix: Sequence[T]) -> bool:
    m = len(suffix)
    if m == 0:
        return True
    dq: deque[T] = deque(maxlen=m)
    for x in it:
        dq.append(x)
    if len(dq) < m:
        return False
    for got, want in zip(dq, suffix):
        if got != want:
            return False
    return True


def matches_suffix(
    it: Iterable[T],
    suffix: Sequence[T],
    *,
    allow_head_missing: int = 0,
    allow_head_extra: int | None = 0,
) -> bool:
    m = len(suffix)
    if m == 0:
        return True
    dq: deque[T] = deque(maxlen=m)
    count = 0
    for x in it:
        dq.append(x)
        count += 1

    if count < m:
        # allow shortfall up to allow_head_missing
        if (m - count) > allow_head_missing:
            return False
        return all(g == w for g, w in zip(dq, suffix[-count:]))

    # enforce head extras allowance
    if allow_head_extra is not None and (count - m) > allow_head_extra:
        return False

    return all(g == w for g, w in zip(dq, suffix))


# --- Convenience: varargs wrapper around equals ---


# --- Starts-with (allow source to be longer) ---
def starts_with(it: Iterable[T], prefix: Sequence[T]) -> bool:
    it = iter(it)
    for want in prefix:
        got = next(it, _SENTINEL)
        if got is _SENTINEL or got != want:
            return False
    return True  # extras allowed


# Varargs sugar
def starts_with_values(it: Iterable[T], *values: T) -> bool:
    return starts_with(it, values)


# --- “Source is suffix of pattern” (mirror helper) ---
def is_suffix_of(it: Iterable[T], pattern: Sequence[T]) -> bool:
    suffix = tuple(it)  # buffer source once
    return ends_with(pattern, suffix)


def take_infinite(n: int, items: Iterable[T]) -> Iterator[T]:
    if n < 0:
        raise ValueError("n must be >= 0")
    return islice(cycle(items), n)
