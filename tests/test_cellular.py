#!/usr/bin/env python3
import json
import subprocess

from connectivity.cellular import CellularManager


def _proc(args, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args, returncode, stdout, stderr)


def _modem_json(state="connected", operator="Test Telecom"):
    return json.dumps({
        "modem": {
            "generic": {
                "state": state,
                "operator-name": operator,
            }
        }
    })


def test_initialize_true_when_modem_present():
    def runner(args):
        return _proc(args, 0, stdout=_modem_json())

    cm = CellularManager(runner=runner)
    assert cm.initialize() is True


def test_initialize_false_when_no_modem():
    def runner(args):
        return _proc(args, 1, stderr="error: no modems found\n")

    cm = CellularManager(runner=runner)
    assert cm.initialize() is False


def test_is_connected_reflects_modem_state():
    def runner_connected(args):
        return _proc(args, 0, stdout=_modem_json(state="connected"))

    assert CellularManager(runner=runner_connected).is_connected() is True

    def runner_searching(args):
        return _proc(args, 0, stdout=_modem_json(state="searching"))

    assert CellularManager(runner=runner_searching).is_connected() is False


def test_get_signal_strength_parses_lte_rssi():
    def runner(args):
        if "--signal-get" in args:
            return _proc(args, 0, stdout=json.dumps({"modem": {"signal": {"lte": {"rssi": "-67"}}}}))
        return _proc(args, 0, stdout=_modem_json())

    cm = CellularManager(runner=runner)
    assert cm.get_signal_strength() == -67


def test_get_signal_strength_zero_when_unavailable():
    def runner(args):
        if "--signal-get" in args:
            return _proc(args, 0, stdout=json.dumps({"modem": {"signal": {"lte": {"rssi": "--"}}}}))
        return _proc(args, 0, stdout=_modem_json())

    cm = CellularManager(runner=runner)
    assert cm.get_signal_strength() == 0


def test_get_signal_strength_zero_when_command_fails():
    def runner(args):
        return _proc(args, 1)

    cm = CellularManager(runner=runner)
    assert cm.get_signal_strength() == 0


def test_get_carrier_returns_operator_name():
    def runner(args):
        return _proc(args, 0, stdout=_modem_json(operator="Acme Mobile"))

    cm = CellularManager(runner=runner)
    assert cm.get_carrier() == "Acme Mobile"


def test_reconnect_succeeds_once_connected():
    state = {"connected": False}

    def runner(args):
        if "-e" in args:
            state["connected"] = True
            return _proc(args, 0)
        return _proc(args, 0, stdout=_modem_json(state="connected" if state["connected"] else "searching"))

    cm = CellularManager(runner=runner)
    assert cm.reconnect() is True


def test_reconnect_fails_when_never_connects():
    def runner(args):
        return _proc(args, 0, stdout=_modem_json(state="searching"))

    cm = CellularManager(runner=runner)
    assert cm.reconnect() is False
