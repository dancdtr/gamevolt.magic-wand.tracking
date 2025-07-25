from dataclasses import dataclass


@dataclass
class SerialReceiverSettings:
    port: str
    baud: int
    timeout: int
    retry_interval: float
