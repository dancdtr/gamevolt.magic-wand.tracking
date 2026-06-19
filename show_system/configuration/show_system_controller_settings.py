from dataclasses import field

from gamevolt.configuration.appsetting import appsetting
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from spells.spell_type import SpellType


@appsetting
class ShowControlDestinationSettings:
    """A single show-control endpoint and the spells routed to it over UDP."""

    name: str
    udp_tx: UdpTxSettings
    spells: list[SpellType]


@appsetting
class ShowSystemControllerSettings:
    """Show-system routing. When disabled, a no-op controller is built and no UDP is sent.

    Each destination lists the spells routed to it; a spell may target several destinations.
    Spells absent from every destination raise a warning when they fire (see ShowSystemController).
    """

    enabled: bool = True
    destinations: list[ShowControlDestinationSettings] = field(default_factory=list)
