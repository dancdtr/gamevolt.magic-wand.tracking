import argparse

from gamevolt.logging import get_logger
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from gamevolt.messaging.udp.udp_tx import UdpTx
from zones.zone_entered_message import ZoneEnteredMessage
from zones.zone_exited_message import ZoneExitedMessage


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="send_zone_event", description="Send a ZoneEntered/ZoneExited UDP message for a wand.")
    p.add_argument("--wand", required=False, default="E001", help="Wand ID, e.g. E001")
    p.add_argument("--zone", required=False, default="0", help="Zone ID, e.g. 0 or 1")
    p.add_argument(
        "--event",
        choices=["e", "x"],
        help="Event type: enter or exit",
    )
    return p


def main() -> int:
    a = build_parser().parse_args()

    logger = get_logger()
    settings = UdpTxSettings("0.0.0.0", 5005)
    # settings = UdpTxSettings("192.168.3.63", 5005)
    # settings = UdpTxSettings("172.30.1.135", 5005)
    udp = UdpTx(logger, settings)

    if a.event == "e":
        msg = ZoneEnteredMessage(ZoneId=str(a.zone), WandId=str(a.wand))
    elif a.event == "x":
        msg = ZoneExitedMessage(ZoneId=str(a.zone), WandId=str(a.wand))
    else:
        raise ValueError(f"Unknown event type: '{a.event}'.")

    udp.send(msg.to_dict())

    logger = get_logger()
    settings = UdpTxSettings("0.0.0.0", 5005)
    udp = UdpTx(logger, settings)

    logger.info(f"Sent zone event: zone_id={a.zone} wand_id={a.wand} event={a.event} -> '{settings.host}:{settings.port}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
