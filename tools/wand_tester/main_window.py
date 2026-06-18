"""Top-level QMainWindow tying tabs + wand-ID + Stop All together."""

from __future__ import annotations

import time

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from wand.streaming.eliko.pekio_client import STOP_ALL_CHAIN_DELAY_S, PekioClient

from wand_tester.constants import WAND_TAGS
from wand_tester.haptic_tab import HapticTab
from wand_tester.led_haptic_tab import LedHapticTab
from wand_tester.led_tab import LedTab
from wand_tester.styles import action_button_style


class MainWindow(QMainWindow):
    def __init__(self, client: PekioClient) -> None:
        super().__init__()
        self._client = client
        self.setWindowTitle("CONDUCTR v3 Wand Tester")
        self.resize(720, 470)

        self._led_tab = LedTab(client)
        self._haptic_tab = HapticTab(client, restore_led=self._led_tab.reapply_last)
        self._led_haptic_tab = LedHapticTab(client)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)

        outer.addLayout(self._build_tag_row())

        self._tabs = QTabWidget()
        self._tabs.addTab(self._led_tab, "LED")
        self._tabs.addTab(self._haptic_tab, "Haptic")
        self._tabs.addTab(self._led_haptic_tab, "LED + Haptic")
        outer.addWidget(self._tabs, 1)

    def _build_tag_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel("Wand ID:"))
        combo = QComboBox()
        combo.addItems(WAND_TAGS)
        current = self._client.target_tag
        if current in WAND_TAGS:
            combo.setCurrentText(current)
        else:
            combo.insertItem(0, current)
            combo.setCurrentIndex(0)
        combo.currentTextChanged.connect(self._client.set_tag)
        combo.setMinimumWidth(140)
        row.addWidget(combo)
        enable_imu_btn = QPushButton("Enable IMU")
        enable_imu_btn.setStyleSheet(action_button_style("#2060a0"))
        enable_imu_btn.clicked.connect(self._client.enable_imu)
        row.addWidget(enable_imu_btn)
        row.addStretch(1)
        # Send/Stop live up here (not at the bottom of each tab) so they stay
        # reachable on short laptop screens. Send dispatches to the active tab.
        stop_all_btn = QPushButton("Stop All")
        stop_all_btn.setStyleSheet(action_button_style("#a02020"))
        stop_all_btn.clicked.connect(self._on_stop_all)
        row.addWidget(stop_all_btn)
        stop_led_btn = QPushButton("Stop LED")
        stop_led_btn.setStyleSheet(action_button_style("#d97718"))
        stop_led_btn.clicked.connect(self._led_tab.stop)
        row.addWidget(stop_led_btn)
        send_btn = QPushButton("Send")
        send_btn.setStyleSheet(action_button_style("#208040"))
        send_btn.clicked.connect(self._on_send)
        row.addWidget(send_btn)
        return row

    def _on_send(self) -> None:
        self._tabs.currentWidget().send()

    def _on_stop_all(self) -> None:
        # Cancel each tab's widget-local timers, then full firmware stop.
        self._led_tab.emergency_stop()
        self._haptic_tab.emergency_stop()
        self._led_haptic_tab.emergency_stop()
        self._client.stop_all()

    def closeEvent(self, event) -> None:  # noqa: N802 — Qt override
        # client.stop_all() schedules a fade-hold Timer ~50ms after CMD1=0 so
        # the firmware doesn't latch its default green blink in the gap. Sleep
        # long enough for that Timer to fire before the entry script's
        # `finally: ser.close()` runs — otherwise the Timer-thread write
        # lands on a closed port (and the LED green-blink would be the final
        # wand state).
        self._on_stop_all()
        time.sleep(STOP_ALL_CHAIN_DELAY_S + 0.05)
        super().closeEvent(event)
