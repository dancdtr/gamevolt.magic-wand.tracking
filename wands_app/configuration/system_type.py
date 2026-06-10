from enum import Enum


class SystemType(Enum):
    """Selects the full set of sensor / command / zone-app implementations.

    A single flag drives stream impl, command sink, and zone-application
    build path so deployment shape doesn't need to be reassembled from
    multiple sub-flags.
    """

    ELIKO_RTLS = "eliko_rtls"
    ELIKO_SINGLE_ANCHOR = "eliko_single_anchor"
