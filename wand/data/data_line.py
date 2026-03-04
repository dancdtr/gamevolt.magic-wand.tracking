from dataclasses import dataclass


@dataclass(frozen=True)
class DataLine:
    seq: int
    data_str: str
