#!/usr/bin/env python3

import socket
import time

import board
import neopixel

PORT = 8888

LED_COUNT = 24
DATA_PIN = board.D18  # GPIO18 / physical pin 12
PIXEL_ORDER = neopixel.GRBW
BRIGHTNESS = 1.0

FADE_ON_SECONDS = 0.75
FADE_OFF_SECONDS = 0.75
COLOUR_LERP_SECONDS = 1.25

TURN_ON_SPELL = "LUMOS"
TURN_OFF_SPELL = "NOX"
CHANGE_COLOUR_SPELL = "SILENCIO"

LERP_FPS = 60

# RGBW tuples: (red, green, blue, white)
COLOURS = [
    ("White", (0, 0, 0, 255)),
    ("Red", (255, 0, 0, 0)),
    ("Orange", (255, 80, 0, 0)),
    ("Yellow", (255, 180, 0, 0)),
    ("Green", (0, 255, 0, 0)),
    ("Cyan", (0, 255, 255, 0)),
    ("Blue", (0, 0, 255, 0)),
    ("Purple", (120, 0, 255, 0)),
    ("Pink", (255, 0, 120, 0)),
]

BLACK = (0, 0, 0, 0)

pixels = neopixel.NeoPixel(
    DATA_PIN,
    LED_COUNT,
    brightness=BRIGHTNESS,
    auto_write=False,
    pixel_order=PIXEL_ORDER,
)


def lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def lerp_colour(
    start: tuple[int, int, int, int], end: tuple[int, int, int, int], t: float
) -> tuple[int, int, int, int]:
    return (
        lerp(start[0], end[0], t),
        lerp(start[1], end[1], t),
        lerp(start[2], end[2], t),
        lerp(start[3], end[3], t),
    )


def show_colour(colour: tuple[int, int, int, int]) -> None:
    pixels.fill(colour)
    pixels.show()


def drain_pending_udp_messages(sock: socket.socket) -> None:
    ignored = 0

    sock.setblocking(False)

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            message = data.decode("utf-8", errors="replace")
            print(
                f"Ignored during transition from {addr[0]}:{addr[1]} -> {message!r}",
                flush=True,
            )
            ignored += 1

    except BlockingIOError:
        pass

    finally:
        sock.setblocking(True)

    if ignored:
        print(f"Ignored {ignored} queued command(s)", flush=True)


class Lamp:
    def __init__(self) -> None:
        self.is_on = False
        self.colour_index = 0
        self.displayed_colour = BLACK

    @property
    def current_colour_name(self) -> str:
        return COLOURS[self.colour_index][0]

    @property
    def current_colour(self) -> tuple[int, int, int, int]:
        return COLOURS[self.colour_index][1]

    def transition_to(
        self,
        sock: socket.socket,
        target_colour: tuple[int, int, int, int],
        duration_seconds: float,
        label: str,
    ) -> None:
        print(label, flush=True)

        start_colour = self.displayed_colour

        try:
            if duration_seconds <= 0:
                self.displayed_colour = target_colour
                show_colour(target_colour)
                return

            steps = max(1, int(duration_seconds * LERP_FPS))
            delay = duration_seconds / steps

            for step in range(1, steps + 1):
                t = step / steps
                colour = lerp_colour(start_colour, target_colour, t)

                self.displayed_colour = colour
                show_colour(colour)

                time.sleep(delay)

            self.displayed_colour = target_colour
            show_colour(target_colour)

        finally:
            drain_pending_udp_messages(sock)

    def turn_on(self, sock: socket.socket) -> None:
        if self.is_on:
            print(f"Already ON: {self.current_colour_name}")
            return

        self.is_on = True

        self.transition_to(
            sock=sock,
            target_colour=self.current_colour,
            duration_seconds=FADE_ON_SECONDS,
            label=f"Lamp ON: {self.current_colour_name}",
        )

    def turn_off(self, sock: socket.socket) -> None:
        if not self.is_on:
            print("Already OFF")
            return

        self.transition_to(
            sock=sock,
            target_colour=BLACK,
            duration_seconds=FADE_OFF_SECONDS,
            label="Lamp OFF",
        )

        self.is_on = False

    def cycle_colour(self, sock: socket.socket) -> None:
        if not self.is_on:
            print(f"Ignored {CHANGE_COLOUR_SPELL}: lamp is OFF")
            return

        next_index = (self.colour_index + 1) % len(COLOURS)
        next_name, next_colour = COLOURS[next_index]

        self.transition_to(
            sock=sock,
            target_colour=next_colour,
            duration_seconds=COLOUR_LERP_SECONDS,
            label=f"Colour change: {self.current_colour_name} -> {next_name}",
        )

        self.colour_index = next_index


def handle_message(sock: socket.socket, lamp: Lamp, message: str) -> None:
    text = message.strip().upper()

    if TURN_ON_SPELL in text:
        lamp.turn_on(sock)

    elif TURN_OFF_SPELL in text:
        lamp.turn_off(sock)

    elif CHANGE_COLOUR_SPELL in text:
        lamp.cycle_colour(sock)

    else:
        print(f"Ignored: {message!r}")


def main() -> None:
    lamp = Lamp()
    show_colour(BLACK)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))

    print(f"Listening on UDP {PORT}...")
    print("=========================")
    print(f"Turn on spell: {TURN_ON_SPELL}")
    print(f"Turn off spell: {TURN_OFF_SPELL}")
    print(f"Change colour spell: {CHANGE_COLOUR_SPELL}")
    print("=========================")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            message = data.decode("utf-8", errors="replace")

            print(f"From {addr[0]}:{addr[1]} -> {message!r}")
            handle_message(sock, lamp, message)

    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        show_colour(BLACK)
        sock.close()
        print("Stopped.")


if __name__ == "__main__":
    main()
