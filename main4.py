from __future__ import annotations

import os
import random

from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from appsettings import AppSettings
from gamevolt.messaging.udp.udp_tx import UdpTx
from messaging.spell_cast_message import SpellCastMessage

application_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(application_dir, "appsettings.yml")
config_env_path = os.path.join(application_dir, "appsettings.env.yml")
settings = AppSettings.load(config_file_path=config_path, config_env_file_path=config_env_path)

logger = get_logger(LoggingSettings(file_path=settings.logging.file_path, minimum_level=settings.logging.minimum_level))

udp_tx = UdpTx(logger, settings.udp_peer.udp_transmitter)

accuracy = random.randrange(60, 99) / 100

# udp_tx.send(SpellCastMessage("INCENDIO", accuracy).to_dict())
# udp_tx.send(SpellCastMessage("WINGARDIUM_LEVIOSA", accuracy).to_dict())
# udp_tx.send(SpellCastMessage("ALOHOMORA", accuracy).to_dict())
