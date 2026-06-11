#!/usr/bin/env python3
"""4G LTE cellular modem manager (ModemManager / ``mmcli`` backend).

Monitors signal quality and connection state, and handles reconnection of
the modem identified by ``modem_index``. Failures here are surfaced to the
fault manager by the connectivity layer's tick, not by this module.
"""

import json
import logging
import subprocess
from typing import Callable, List, Optional

from core.constants import API_RETRY_COUNT

logger = logging.getLogger(__name__)

CommandRunner = Callable[[List[str]], "subprocess.CompletedProcess"]

_SIGNAL_TECHS = ("lte", "5g", "umts", "gsm")


def _default_runner(args: List[str]) -> "subprocess.CompletedProcess":
    return subprocess.run(args, capture_output=True, text=True, timeout=5)


class CellularManager:
    """Manages a single ModemManager-controlled modem."""

    def __init__(self, modem_index: int = 0, runner: Optional[CommandRunner] = None):
        self.modem_index = modem_index
        self._run = runner or _default_runner

    def _modem_info(self) -> dict:
        result = self._run(["mmcli", "-m", str(self.modem_index), "-J"])
        if result.returncode != 0:
            return {}
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.warning("Failed to parse mmcli output for modem %d", self.modem_index)
            return {}
        return data.get("modem", {})

    def initialize(self) -> bool:
        return bool(self._modem_info())

    def is_connected(self) -> bool:
        info = self._modem_info()
        return info.get("generic", {}).get("state") == "connected"

    def get_signal_strength(self) -> int:
        result = self._run(["mmcli", "-m", str(self.modem_index), "--signal-get", "-J"])
        if result.returncode != 0:
            return 0
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.warning("Failed to parse mmcli signal output for modem %d", self.modem_index)
            return 0

        signal = data.get("modem", {}).get("signal", {})
        for tech in _SIGNAL_TECHS:
            rssi = signal.get(tech, {}).get("rssi")
            if rssi in (None, "--"):
                continue
            try:
                return int(float(rssi))
            except (TypeError, ValueError):
                continue
        return 0

    def get_carrier(self) -> str:
        info = self._modem_info()
        return info.get("generic", {}).get("operator-name", "")

    def reconnect(self) -> bool:
        for attempt in range(1, API_RETRY_COUNT + 1):
            self._run(["mmcli", "-m", str(self.modem_index), "-e"])
            if self.is_connected():
                logger.info("Cellular modem %d reconnected on attempt %d", self.modem_index, attempt)
                return True
            logger.warning(
                "Cellular reconnect attempt %d/%d failed for modem %d",
                attempt, API_RETRY_COUNT, self.modem_index,
            )
        return False
