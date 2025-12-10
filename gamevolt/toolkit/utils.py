import time


def now_ms() -> int:
    return int(time.time() * 1000)


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    s = hex_str.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) != 6:
        raise ValueError(f"Expected #RRGGBB, got '{hex_str}'")
    r = int(s[0:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:6], 16)
    return (r, g, b)
