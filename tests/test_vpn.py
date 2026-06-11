#!/usr/bin/env python3
import subprocess

from connectivity.vpn import VPNManager


def _proc(args, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args, returncode, stdout, stderr)


def test_initialize_true_when_interface_exists():
    def runner(args):
        assert args == ["wg", "show", "wg0"]
        return _proc(args, 0, stdout="interface: wg0\nlatest handshake: 30 seconds ago\n")

    vpn = VPNManager(interface="wg0", runner=runner)
    assert vpn.initialize("/etc/wireguard/wg0.conf") is True


def test_initialize_false_when_interface_missing():
    def runner(args):
        return _proc(args, 1, stderr="No such device\n")

    vpn = VPNManager(interface="wg0", runner=runner)
    assert vpn.initialize("/etc/wireguard/wg0.conf") is False


def test_is_tunnel_up_requires_handshake():
    def runner(args):
        return _proc(args, 0, stdout="interface: wg0\nlatest handshake: 5 seconds ago\n")

    vpn = VPNManager(runner=runner)
    assert vpn.is_tunnel_up() is True


def test_is_tunnel_up_false_without_handshake_line():
    def runner(args):
        return _proc(args, 0, stdout="interface: wg0\n")

    vpn = VPNManager(runner=runner)
    assert vpn.is_tunnel_up() is False


def test_is_tunnel_up_false_when_command_fails():
    def runner(args):
        return _proc(args, 1, stderr="No such device\n")

    vpn = VPNManager(runner=runner)
    assert vpn.is_tunnel_up() is False


def test_get_tunnel_ip_parses_inet_address():
    def runner(args):
        if args[:3] == ["ip", "-4", "addr"]:
            return _proc(args, 0, stdout="inet 10.8.0.5/24 scope global wg0\n")
        return _proc(args, 1)

    vpn = VPNManager(runner=runner)
    assert vpn.get_tunnel_ip() == "10.8.0.5"


def test_get_tunnel_ip_none_when_no_match():
    def runner(args):
        return _proc(args, 0, stdout="no inet line here\n")

    vpn = VPNManager(runner=runner)
    assert vpn.get_tunnel_ip() is None


def test_get_latency_ms_parses_ping_time():
    def runner(args):
        if args[:2] == ["wg", "show"] and "endpoints" in args:
            return _proc(args, 0, stdout="abc123=\t10.8.0.1:51820\n")
        if args[0] == "ping":
            return _proc(args, 0, stdout="64 bytes from 10.8.0.1: icmp_seq=1 ttl=64 time=23.4 ms\n")
        return _proc(args, 1)

    vpn = VPNManager(runner=runner)
    assert vpn.get_latency_ms() == 23.4


def test_get_latency_ms_none_when_no_endpoint():
    def runner(args):
        return _proc(args, 0, stdout="(none)\n")

    vpn = VPNManager(runner=runner)
    assert vpn.get_latency_ms() is None


def test_reconnect_succeeds_when_tunnel_comes_up():
    def runner(args):
        if args[:2] == ["wg-quick", "down"]:
            return _proc(args, 0)
        if args[:2] == ["wg-quick", "up"]:
            return _proc(args, 0)
        if args[:2] == ["wg", "show"]:
            return _proc(args, 0, stdout="latest handshake: now\n")
        return _proc(args, 1)

    vpn = VPNManager(runner=runner)
    assert vpn.reconnect() is True


def test_reconnect_fails_after_max_attempts():
    def runner(args):
        return _proc(args, 1)

    vpn = VPNManager(runner=runner)
    assert vpn.reconnect() is False
