from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class ActiveWandChanged(Message):
    """RTLS presence event: a wand became ACTIVE/INACTIVE in a zone.

    Replaces the `ZoneEnteredMessage` / `ZoneExitedMessage` pair on the RTLS
    path — the RTLS system decides which wand is the active caster in a zone
    and the `state` field carries enter (`ACTIVE`) vs exit (`INACTIVE`).

    Field names mirror the RTLS wire schema (snake_case) verbatim:
        {"MessageType": "ActiveWandChanged", "wand_id": "0x1DB1",
         "state": "ACTIVE", "zone_id": "Z001", "zone_name": "CANTIS", "txrx": 10}

    `wand_id` arrives with the `0x` prefix; it is normalised to bare upper hex
    internally (see `ActiveWandZoneManager`).
    """

    wand_id: str
    state: str
    zone_id: str
    zone_name: str
    txrx: int
