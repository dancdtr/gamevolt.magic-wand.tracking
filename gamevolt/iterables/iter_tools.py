from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator, Sequence
from itertools import islice, zip_longest
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


def matches_prefix(it: Iterable[T], prefix: Sequence[T], *, allow_tail_missing: int = 0, allow_tail_extra: int | None = 0) -> bool:
    it = iter(it)
    i = 0
    for want in prefix:
        got = next(it, _SENTINEL)
        if got is _SENTINEL:
            # source ended early → accept only if remaining fits the missing allowance
            return (len(prefix) - i) <= allow_tail_missing
        if got != want:
            return False
        i += 1

    # full prefix matched; enforce extras
    if allow_tail_extra is None:
        return True
    if allow_tail_extra <= 0:
        return next(it, _SENTINEL) is _SENTINEL
    for _ in range(allow_tail_extra):
        if next(it, _SENTINEL) is _SENTINEL:
            return True
    return next(it, _SENTINEL) is _SENTINEL


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
