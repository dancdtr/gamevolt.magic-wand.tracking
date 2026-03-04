from dataclasses import dataclass


@dataclass(frozen=True)
class WebSocketClientMeta:
    id: str
    version: str
    host: str
    port: int

    def __str__(self) -> str:
        return f"ID: {self.id} | Version: {self.version} | Address: {self.host}:{self.port})"
