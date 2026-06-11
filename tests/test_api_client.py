#!/usr/bin/env python3
import time

import pytest
import requests

from connectivity.api_client import RiverSongAPIClient
from core.models import (
    Alert,
    CommandType,
    FaultSeverity,
    GPSCoordinate,
    LocomotionMode,
    TelemetrySnapshot,
    UnitStatus,
)


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        return self._json_data


class FakeSession:
    def __init__(self, responses=None, exception=None):
        self.calls = []
        self._responses = list(responses) if responses is not None else None
        self._exception = exception

    def request(self, method, url, json=None, params=None, headers=None, timeout=None):
        self.calls.append({
            "method": method,
            "url": url,
            "json": json,
            "params": params,
            "headers": headers,
            "timeout": timeout,
        })
        if self._exception is not None:
            raise self._exception
        if self._responses is not None:
            return self._responses.pop(0)
        return FakeResponse()


def _client(session):
    return RiverSongAPIClient(
        base_url="https://riversongai.com",
        unit_id="RS-001",
        api_key="secret-token",
        program="sentinel",
        session=session,
    )


def test_post_telemetry_sends_expected_shape():
    session = FakeSession()
    client = _client(session)

    snapshot = TelemetrySnapshot(
        unit_id="RS-001",
        timestamp=time.time(),
        position=GPSCoordinate(latitude=1.0, longitude=2.0),
        battery_pct=80.0,
        battery_voltage=12.4,
        locomotion_mode=LocomotionMode.WALK,
    )

    assert client.post_telemetry(snapshot) is True
    assert len(session.calls) == 1

    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == "https://riversongai.com/api/sentinel/units/RS-001/telemetry"
    assert call["json"]["unit_id"] == "RS-001"
    assert call["json"]["locomotion_mode"] == "WALK"
    assert call["json"]["position"]["latitude"] == 1.0
    assert call["headers"]["Authorization"] == "Bearer secret-token"
    assert call["headers"]["X-Unit-Id"] == "RS-001"


def test_register_post_alert_post_status_success():
    session = FakeSession()
    client = _client(session)

    assert client.register({"unit_id": "RS-001", "platform_type": "QUADRUPED"}) is True

    alert = Alert(
        alert_id="a-1",
        fault_id="f-1",
        severity=FaultSeverity.WARNING,
        message="VPN tunnel down",
        timestamp=time.time(),
    )
    assert client.post_alert(alert) is True

    status = UnitStatus(unit_id="RS-001", state="DOCKED", timestamp=time.time(), reason="LOW_BATTERY")
    assert client.post_status(status) is True

    urls = [call["url"] for call in session.calls]
    assert urls == [
        "https://riversongai.com/api/sentinel/units/RS-001/register",
        "https://riversongai.com/api/sentinel/units/RS-001/alerts",
        "https://riversongai.com/api/sentinel/units/RS-001/status",
    ]
    assert session.calls[1]["json"]["severity"] == "WARNING"


def test_post_event_includes_type_payload_and_timestamp():
    session = FakeSession()
    client = _client(session)

    assert client.post_event("boot", {"firmware": "1.2.3"}) is True

    call = session.calls[0]
    assert call["json"]["event_type"] == "boot"
    assert call["json"]["payload"] == {"firmware": "1.2.3"}
    assert "timestamp" in call["json"]


def test_is_reachable_true_and_false():
    session_ok = FakeSession(responses=[FakeResponse(status_code=200)])
    assert _client(session_ok).is_reachable() is True

    session_down = FakeSession(responses=[FakeResponse(status_code=503)] * 3)
    assert _client(session_down).is_reachable() is False


def test_poll_commands_parses_valid_and_skips_malformed():
    payload = [
        {
            "command_id": "c-1",
            "unit_id": "RS-001",
            "command_type": "PATROL",
            "parameters": {"pattern": "PERIMETER"},
            "issued_by": "dashboard",
            "timestamp": 100.0,
            "expiry": 200.0,
        },
        {
            "command_id": "c-2",
            "unit_id": "RS-001",
            "command_type": "NOT_A_REAL_COMMAND",
            "timestamp": 100.0,
        },
        {
            "command_id": "c-3",
            "unit_id": "RS-001",
            # missing command_type entirely
            "timestamp": 100.0,
        },
    ]
    session = FakeSession(responses=[FakeResponse(json_data=payload)])
    client = _client(session)

    commands = client.poll_commands()

    assert len(commands) == 1
    assert commands[0].command_id == "c-1"
    assert commands[0].command_type == CommandType.PATROL
    assert commands[0].is_expired(now=300.0) is True
    assert commands[0].is_expired(now=150.0) is False


def test_poll_commands_returns_empty_on_error_response():
    session = FakeSession(responses=[FakeResponse(status_code=500)] * 3)
    client = _client(session)

    assert client.poll_commands() == []


def test_retry_on_5xx_then_success():
    session = FakeSession(responses=[FakeResponse(status_code=503), FakeResponse(status_code=200)])
    client = _client(session)

    assert client.is_reachable() is True
    assert len(session.calls) == 2


def test_retry_exhausted_on_request_exception_returns_false():
    session = FakeSession(exception=requests.ConnectionError("network unreachable"))
    client = RiverSongAPIClient(
        base_url="https://riversongai.com",
        unit_id="RS-001",
        api_key="secret-token",
        session=session,
        retry_count=2,
    )

    snapshot = TelemetrySnapshot(
        unit_id="RS-001",
        timestamp=time.time(),
        position=None,
        battery_pct=80.0,
        battery_voltage=12.4,
        locomotion_mode=LocomotionMode.IDLE,
    )

    assert client.post_telemetry(snapshot) is False
    assert len(session.calls) == 2
