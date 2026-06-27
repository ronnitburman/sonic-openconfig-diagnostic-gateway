"""Unit tests for the shared parser functions."""

import pytest
from app.adapters.parsers import (
    parse_speed,
    parse_openconfig_response,
    parse_cisco_native_response,
)


# ── parse_speed ──────────────────────────────────────────────────────

def test_parse_speed_enum_without_prefix():
    assert parse_speed("SPEED_1GB") == 1000

def test_parse_speed_enum_with_prefix():
    assert parse_speed("openconfig-if-ethernet:SPEED_10GB") == 10000

def test_parse_speed_int():
    assert parse_speed(1000) == 1000

def test_parse_speed_string_int():
    assert parse_speed("1000") == 1000

def test_parse_speed_none():
    assert parse_speed(None) is None

def test_parse_speed_unknown():
    assert parse_speed("SPEED_UNKNOWN") is None

def test_parse_speed_all_known():
    assert parse_speed("SPEED_10MB") == 10
    assert parse_speed("SPEED_100MB") == 100
    assert parse_speed("SPEED_25GB") == 25000
    assert parse_speed("SPEED_40GB") == 40000
    assert parse_speed("SPEED_400GB") == 400000


# ── parse_openconfig_response ────────────────────────────────────────

def test_openconfig_healthy_interface():
    raw = {
        "state": {
            "admin-status": "UP",
            "oper-status": "UP",
            "description": "test-iface",
            "enabled": True,
            "mtu": 1500,
            "counters": {
                "in-errors": "0",
                "out-errors": "0",
                "in-discards": "0",
                "out-discards": "0",
            },
        },
        "openconfig-if-ethernet:ethernet": {
            "state": {
                "port-speed": "SPEED_1GB",
            }
        },
    }
    snap = parse_openconfig_response(raw, "Gi1")
    assert snap.name == "Gi1"
    assert snap.admin_status == "UP"
    assert snap.oper_status == "UP"
    assert snap.enabled is True
    assert snap.speed_mbps == 1000
    assert snap.mtu == 1500
    assert snap.in_errors == 0
    assert snap.out_errors == 0
    assert snap.description == "test-iface"
    assert snap.source_model == "openconfig-interfaces"


def test_openconfig_counter_strings_become_ints():
    raw = {
        "state": {
            "counters": {
                "in-errors": "42",
                "out-errors": "7",
                "in-discards": "1",
            }
        }
    }
    snap = parse_openconfig_response(raw, "Gi1")
    assert snap.in_errors == 42
    assert snap.out_errors == 7
    assert snap.in_discards == 1
    assert isinstance(snap.in_errors, int)


def test_openconfig_missing_fields_become_none():
    raw = {}
    snap = parse_openconfig_response(raw, "Gi1")
    assert snap.admin_status is None
    assert snap.oper_status is None
    assert snap.speed_mbps is None
    assert snap.in_errors is None


def test_openconfig_speed_from_negotiated():
    raw = {
        "openconfig-if-ethernet:ethernet": {
            "state": {
                "negotiated-port-speed": "SPEED_100GB",
            }
        }
    }
    snap = parse_openconfig_response(raw, "Gi1")
    assert snap.speed_mbps == 100000


# ── parse_cisco_native_response ──────────────────────────────────────

def test_cisco_native_healthy():
    raw = {
        "state": {
            "admin-status": "if-state-up",
            "oper-status": "if-oper-up",
            "description": "cisco-iface",
            "speed": "1000",
            "in-errors": "0",
            "out-errors": "0",
        }
    }
    snap = parse_cisco_native_response(raw, "Gi1")
    assert snap.name == "Gi1"
    assert snap.admin_status == "if-state-up"
    assert snap.enabled is True  # if-state-up → True
    assert snap.oper_status == "if-oper-up"
    assert snap.speed_mbps == 1000
    assert snap.source_model == "cisco-native-interfaces"


def test_cisco_native_admin_down():
    raw = {"state": {"admin-status": "if-state-down"}}
    snap = parse_cisco_native_response(raw, "Gi1")
    assert snap.enabled is False
