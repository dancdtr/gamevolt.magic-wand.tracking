import argparse

from gamevolt.logging import get_logger
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from gamevolt.messaging.udp.udp_tx import UdpTx
from messaging.active_wand_changed import ActiveWandChanged


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="send_active_wand_changed",
        description="Send an ActiveWandChanged UDP message (RTLS presence) for a wand.",
    )
    p.add_argument("--wand", default="0x1DB1", help="Wand ID on the wire, e.g. 0x1DB1")
    p.add_argument("--zone", default="Z001", help="Zone ID, e.g. Z001")
    p.add_argument("--zone-name", default="REVELIO", help="Zone name (informational)")
    p.add_argument("--state", choices=["ACTIVE", "INACTIVE"], default="ACTIVE")
    p.add_argument("--txrx", type=int, default=10)
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=5006)
    return p


def main() -> int:
    a = build_parser().parse_args()

    logger = get_logger()
    udp = UdpTx(logger, UdpTxSettings(a.host, a.port))

    msg = ActiveWandChanged(
        wand_id=a.wand,
        state=a.state,
        zone_id=a.zone,
        zone_name=a.zone_name,
        txrx=a.txrx,
    )
    udp.send(msg.to_dict())

    logger.info(
        f"Sent ActiveWandChanged: wand={a.wand} state={a.state} zone={a.zone} "
        f"-> 'udp://{a.host}:{a.port}'."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
