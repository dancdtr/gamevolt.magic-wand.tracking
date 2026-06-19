"""Top-level QMainWindow tying tabs + wand-ID + Stop together."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from wand.streaming.eliko.pekio_client import PekioClient

from wand_tester.constants import WAND_TAGS
from wand_tester.haptic_tab import HapticTab
from wand_tester.led_tab import LedTab
from wand_tester.styles import action_button_style


class MainWindow(QMainWindow):
    def __init__(self, client: PekioClient) -> None:
        super().__init__()
        self._client = client
        self.setWindowTitle("✦ CONDUCTR v3 Wand Tester ✦")

        self._led_tab = LedTab(client)
        self._haptic_tab = HapticTab(client, restore_led=self._led_tab.reapply_last)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)

        outer.addLayout(self._build_tag_row())

        self._tabs = QTabWidget()
        # Tabs sit in scroll areas so every section is always reachable even
        # when the window is clamped to a small screen.
        self._tabs.addTab(self._wrap_scroll(self._led_tab), "LED")
        self._tabs.addTab(self._wrap_scroll(self._haptic_tab), "Haptic")
        outer.addWidget(self._tabs, 1)

        # Open large enough to show everything without a resize, but never
        # bigger than the screen — clamp the content hint to ~92% of available
        # desktop so the window can't open off-screen on a laptop or the Pi.
        self.resize(self._preferred_size())
        self.setMinimumSize(680, 460)

    def _wrap_scroll(self, widget: QWidget) -> QScrollArea:
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setWidget(widget)
        return area

    def _preferred_size(self):
        hint = self.sizeHint()
        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            width = min(max(hint.width(), 760), int(avail.width() * 0.92))
            height = min(max(hint.height(), 520), int(avail.height() * 0.92))
            return QSize(width, height)
        return QSize(max(hint.width(), 760), max(hint.height(), 520))

    @staticmethod
    def _short_tag(tag: str) -> str:
        """Drop the 0x prefix for display (full tag kept as combo item data)."""
        return tag[2:] if tag[:2].lower() == "0x" else tag

    def _build_tag_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel("Wand ID:"))
        combo = QComboBox()
        # Show the short 4-char tag (e.g. "1DAE") but carry the full "0x1DAE"
        # as item data — that's what the client needs.
        for tag in WAND_TAGS:
            combo.addItem(self._short_tag(tag), tag)
        current = self._client.target_tag
        idx = combo.findData(current)
        if idx < 0:
            combo.insertItem(0, self._short_tag(current), current)
            idx = 0
        combo.setCurrentIndex(idx)
        combo.currentIndexChanged.connect(lambda i: self._client.set_tag(combo.itemData(i)))
        combo.setMinimumWidth(90)
        row.addWidget(combo)
        enable_imu_btn = QPushButton("Enable IMU")
        enable_imu_btn.setStyleSheet(action_button_style("#2060a0"))
        enable_imu_btn.clicked.connect(self._client.enable_imu)
        row.addWidget(enable_imu_btn)
        row.addStretch(1)
        # Send/Stop live up here (not at the bottom of each tab) so they stay
        # reachable on short laptop screens. Send dispatches to the active tab.
        stop_btn = QPushButton("Stop")
        stop_btn.setStyleSheet(action_button_style("#a02020"))
        stop_btn.clicked.connect(self._on_stop_all)
        row.addWidget(stop_btn)
        send_btn = QPushButton("Send")
        send_btn.setStyleSheet(action_button_style("#208040"))
        send_btn.clicked.connect(self._on_send)
        row.addWidget(send_btn)
        return row

    def _on_send(self) -> None:
        # currentWidget() is the QScrollArea wrapper — dispatch to the tab inside.
        current = self._tabs.currentWidget()
        tab = current.widget() if isinstance(current, QScrollArea) else current
        tab.send()

    def _on_stop_all(self) -> None:
        # Cancel each tab's widget-local timers, then full firmware stop.
        self._led_tab.emergency_stop()
        self._haptic_tab.emergency_stop()
        self._client.stop_all()

    def closeEvent(self, event) -> None:  # noqa: N802 — Qt override
        # Deliberately send NO stop command on exit — leave whatever effect is
        # running on the wand in place. Only cancel local timers (Qt loop +
        # client-side threading.Timers) so nothing fires a stray write into the
        # serial port as it's being closed by the entry script's `finally`.
        self._led_tab.emergency_stop()
        self._haptic_tab.emergency_stop()
        self._client.cancel_timed()
        super().closeEvent(event)
