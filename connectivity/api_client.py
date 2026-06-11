#!/usr/bin/env python3
"""HTTP client for the River Song API.

Every River Song program (sentinel, vector, kova, ...) registers with the
central River Song brain and exchanges data through a per-program REST
namespace: ``/api/<program>/units/<unit_id>/...``. This client implements
that shared pattern: telemetry/alerts/status/events flow out via
``post_*``, and commands flow in via :meth:`poll_commands`.

Per design.md P10, the VPN tunnel must be confirmed up
(``connectivity.vpn.VPNManager.is_tunnel_up()``) before any method on this
client is called. This client does not manage the tunnel itself.
"""

import logging
import time
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import requests

from core.constants import API_RETRY_COUNT
from core.models import Alert, CommandType, TelemetrySnapshot, UnitCommand, UnitStatus

logger = logging.getLogger(__name__)


def _to_jsonable(value: Any) -> Any:
    """Recursively convert dataclasses and Enums into JSON-serializable values."""
    if is_dataclass(value) and not isinstance(value, type):
        return _to_jsonable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


class RiverSongAPIClient:
    """Client for a single unit's River Song API namespace."""

    def __init__(
        self,
        base_url: str,
        unit_id: str,
        api_key: str,
        program: str = "sentinel",
        session: Optional[requests.Session] = None,
        retry_count: int = API_RETRY_COUNT,
        timeout_s: float = 5.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.unit_id = unit_id
        self.api_key = api_key
        self.program = program
        self.session = session if session is not None else requests.Session()
        self.retry_count = retry_count
        self.timeout_s = timeout_s

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Unit-Id": self.unit_id,
        }

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/{self.program}/{path.lstrip('/')}"

    def _request(
        self,
        method: str,
        path: str,
        json_body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[requests.Response]:
        url = self._url(path)
        body = _to_jsonable(json_body) if json_body is not None else None

        for attempt in range(1, self.retry_count + 1):
            try:
                response = self.session.request(
                    method,
                    url,
                    json=body,
                    params=params,
                    headers=self._headers(),
                    timeout=self.timeout_s,
                )
            except requests.RequestException as exc:
                logger.warning(
                    "River Song API request failed (attempt %d/%d): %s %s -> %s",
                    attempt, self.retry_count, method, url, exc,
                )
                continue

            if response.status_code >= 500:
                logger.warning(
                    "River Song API server error (attempt %d/%d): %s %s -> %d",
                    attempt, self.retry_count, method, url, response.status_code,
                )
                continue

            return response

        logger.error("River Song API request exhausted retries: %s %s", method, url)
        return None

    def is_reachable(self) -> bool:
        response = self._request("GET", "health")
        return response is not None and response.ok

    def register(self, profile: Dict[str, Any]) -> bool:
        response = self._request("POST", f"units/{self.unit_id}/register", json_body=profile)
        return response is not None and response.ok

    def post_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        body = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": time.time(),
        }
        response = self._request("POST", f"units/{self.unit_id}/events", json_body=body)
        return response is not None and response.ok

    def post_telemetry(self, snapshot: TelemetrySnapshot) -> bool:
        response = self._request("POST", f"units/{self.unit_id}/telemetry", json_body=snapshot)
        return response is not None and response.ok

    def post_alert(self, alert: Alert) -> bool:
        response = self._request("POST", f"units/{self.unit_id}/alerts", json_body=alert)
        return response is not None and response.ok

    def post_status(self, status: UnitStatus) -> bool:
        response = self._request("POST", f"units/{self.unit_id}/status", json_body=status)
        return response is not None and response.ok

    def poll_commands(self) -> List[UnitCommand]:
        response = self._request("GET", f"units/{self.unit_id}/commands")
        if response is None or not response.ok:
            return []

        try:
            data = response.json()
        except ValueError:
            logger.warning("River Song API returned non-JSON command list")
            return []

        if isinstance(data, dict):
            data = data.get("commands", [])

        commands: List[UnitCommand] = []
        for entry in data:
            command = self._parse_command(entry)
            if command is not None:
                commands.append(command)
        return commands

    @staticmethod
    def _parse_command(data: Dict[str, Any]) -> Optional[UnitCommand]:
        try:
            return UnitCommand(
                command_id=data["command_id"],
                unit_id=data["unit_id"],
                command_type=CommandType(data["command_type"]),
                parameters=data.get("parameters", {}),
                issued_by=data.get("issued_by", "api"),
                timestamp=data["timestamp"],
                expiry=data.get("expiry"),
            )
        except (KeyError, ValueError) as exc:
            logger.warning("Skipping malformed command from River Song API: %r (%s)", data, exc)
            return None
