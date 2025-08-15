from collections import deque
from collections.abc import Iterator
from itertools import islice, zip_longest
from typing import Iterable, Sequence, TypeVar

T = TypeVar("T")
_SENTINEL = object()

# ---------- Primitive comparisons ----------


def matches(iterable: Iterable[T], *values: T) -> bool:
    return iter_is(iterable, values)


def iter_equal(a: Iterable[T], b: Iterable[T]) -> bool:
    return all(x == y for x, y in zip_longest(a, b, fillvalue=_SENTINEL))


def iter_is(a: Iterable[T], b: Iterable[T]) -> bool:
    for x, y in zip_longest(a, b, fillvalue=_SENTINEL):
        if x is not y:
            return False
    return True


# ---------- Lazy cropping helpers ----------


def drop_first(it: Iterable[T], n: int) -> Iterator[T]:
    """Yield all but the first n items (lazy, no extra memory)."""
    return islice(it, n, None)


def drop_last(it: Iterable[T], n: int) -> Iterator[T]:
    """Yield all but the last n items (lazy, O(n) buffer)."""
    if n <= 0:
        yield from it
        return
    q: deque[T] = deque(maxlen=n)
    for x in it:
        if len(q) == q.maxlen:
            yield q.popleft()
        q.append(x)


# ---------- Prefix match with controlled tail slack ----------


def matches_prefix(
    it: Iterable[T],
    prefix: Sequence[T],  # pattern is small; materialize ok
    *,
    skip_head: int = 0,  # drop N leading items first
    max_tail_extra: int | None = 0,  # None = unlimited, 0 = exact, N = allow up to N extras
) -> bool:
    it = iter(it)
    if skip_head:
        it = islice(it, skip_head, None)

    # compare against prefix
    for want in prefix:
        got = next(it, _SENTINEL)
        if got is _SENTINEL or got is not want:
            return False

    # enforce tail allowance
    if max_tail_extra is None:
        return True  # unlimited extras allowed
    if max_tail_extra <= 0:
        return next(it, _SENTINEL) is _SENTINEL  # must end here

    # allow up to N extras, but not more
    for _ in range(max_tail_extra):
        if next(it, _SENTINEL) is _SENTINEL:
            return True  # ended within allowance
    return next(it, _SENTINEL) is _SENTINEL  # no (N+1)th extra


def matches_suffix(
    it: Iterable[T],
    suffix: Sequence[T],
    *,
    skip_head: int = 0,  # drop first K items
    drop_tail: int = 0,  # ignore last K items
    max_head_extra: int | None = 0,  # None = unlimited extras before suffix
) -> bool:
    """
    True iff, after skipping 'skip_head' items and dropping 'drop_tail' items
    from the end, the iterable ends with 'suffix'. Uses identity ('is') semantics
    if T are enums; change to '==' if you want equality.
    """
    # Fast path for empty suffix
    m = len(suffix)
    if m == 0:
        # After cropping, anything ends with empty suffix. Enforce head-extra limit if provided.
        if max_head_extra is None:
            return True
        # Need the cropped length to check extras; count lazily:
        cnt = 0
        for _ in islice(it, skip_head, None):
            cnt += 1
        cnt = max(0, cnt - drop_tail)
        return cnt <= max_head_extra

    # Skip the head lazily
    it = islice(it, skip_head, None)

    # Maintain a bounded deque of the last (m + drop_tail) items
    deq = deque(maxlen=m + max(drop_tail, 0))
    cnt = 0
    for x in it:
        deq.append(x)
        cnt += 1

    # Drop the tail items (if any)
    for _ in range(min(drop_tail, len(deq))):
        deq.pop()

    # Now deq holds the effective tail to check
    if len(deq) < m:
        return False

    # Check head-extras allowance
    effective_len = min(cnt, cnt - drop_tail)  # total after drop_tail (bounded at 0)
    extras_before_suffix = effective_len - m
    if extras_before_suffix < 0:
        return False
    if max_head_extra is not None and extras_before_suffix > max_head_extra:
        return False

    # Compare the last m items to the suffix (identity check for enums)
    # islice over deque avoids materializing a list
    start = len(deq) - m
    for got, want in zip(islice(deq, start, None), suffix):
        if got is not want:  # use '!=' if you want equality semantics
            return False
    return True
