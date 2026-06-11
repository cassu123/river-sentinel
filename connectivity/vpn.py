#!/usr/bin/env python3
"""WireGuard VPN tunnel manager.

Per design.md P10, the tunnel managed here must be confirmed up before
``connectivity.api_client.RiverSongAPIClient`` is used. All command/control
traffic to and from the River Song cloud flows over this tunnel.
"""

import logging
import re
import subprocess
from typing import Callable, List, Optional

from core.constants import VPN_MAX_RETRY_ATTEMPTS

logger = logging.getLogger(__name__)

CommandRunner = Callable[[List[str]], "subprocess.CompletedProcess"]

_TUNNEL_IP_RE = re.compile(r"inet (\d+\.\d+\.\d+\.\d+)")
_ENDPOINT_RE = re.compile(r"(\d+\.\d+\.\d+\.\d+):\d+")
_PING_TIME_RE = re.compile(r"time=([\d.]+)")


def _default_runner(args: List[str]) -> "subprocess.CompletedProcess":
    return subprocess.run(args, capture_output=True, text=True, timeout=5)


class VPNManager:
    """Manages a single WireGuard interface (default ``wg0``)."""

    def __init__(self, interface: str = "wg0", runner: Optional[CommandRunner] = None):
        self.interface = interface
        self._run = runner or _default_runner
        self._config_path: Optional[str] = None

    def initialize(self, config_path: str) -> bool:
        self._config_path = config_path
        result = self._run(["wg", "show", self.interface])
        return result.returncode == 0

    def is_tunnel_up(self) -> bool:
        result = self._run(["wg", "show", self.interface])
        if result.returncode != 0:
            return False
        return "latest handshake" in result.stdout.lower()

    def reconnect(self) -> bool:
        for attempt in range(1, VPN_MAX_RETRY_ATTEMPTS + 1):
            self._run(["wg-quick", "down", self.interface])
            up = self._run(["wg-quick", "up", self.interface])
            if up.returncode == 0 and self.is_tunnel_up():
                logger.info("VPN tunnel %s reconnected on attempt %d", self.interface, attempt)
                return True
            logger.warning(
                "VPN reconnect attempt %d/%d failed for %s",
                attempt, VPN_MAX_RETRY_ATTEMPTS, self.interface,
            )
        return False

    def get_tunnel_ip(self) -> Optional[str]:
        result = self._run(["ip", "-4", "addr", "show", self.interface])
        if result.returncode != 0:
            return None
        match = _TUNNEL_IP_RE.search(result.stdout)
        return match.group(1) if match else None

    def get_latency_ms(self) -> Optional[float]:
        endpoints = self._run(["wg", "show", self.interface, "endpoints"])
        if endpoints.returncode != 0:
            return None

        match = _ENDPOINT_RE.search(endpoints.stdout)
        if not match:
            return None
        peer_ip = match.group(1)

        ping = self._run(["ping", "-c", "1", "-W", "1", peer_ip])
        if ping.returncode != 0:
            return None

        time_match = _PING_TIME_RE.search(ping.stdout)
        return float(time_match.group(1)) if time_match else None
