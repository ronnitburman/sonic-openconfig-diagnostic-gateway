#!/usr/bin/env python3
"""Capture interface state from a live Cisco IOS XE device via gNMI.

Usage:
    python scripts/capture_interface_fixtures.py --interface GigabitEthernet0/0
    python scripts/capture_interface_fixtures.py --interface GigabitEthernet1/0/1 --output fixtures/interfaces/my-fixture.json
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings


def build_gnmic_base_args() -> list[str]:
    host = settings.gnmi_host
    port = settings.gnmi_port
    args = [
        "gnmic",
        "-a", f"{host}:{port}",
        "-u", settings.gnmi_username,
        "-p", settings.gnmi_password,
        "--encoding", "JSON_IETF",
        "--format", "json",
    ]
    if settings.gnmi_insecure:
        args.append("--insecure")
    else:
        args.append("--skip-verify")
    return args


def run_gnmic_get(path: str) -> dict | None:
    """Run gNMI Get and return parsed JSON response."""
    args = build_gnmic_base_args() + ["get", "--path", path]
    result = subprocess.run(args, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        print(f"  ⚠ gNMI Get failed for path '{path}': {result.stderr.strip()}", file=sys.stderr)
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  ⚠ Could not parse gNMI response for path '{path}'", file=sys.stderr)
        return None


def extract_interface_data(response: dict) -> dict:
    """Extract the interface data from a gNMI response notification."""
    if not response:
        return {}
    try:
        updates = response[0]["updates"][0]
        values = updates["values"]
        # The key is typically "interfaces/interface" or "interfaces/interface[name=X]"
        for key in values:
            if "interface" in key.lower():
                return values[key]
        return values
    except (KeyError, IndexError, TypeError):
        return {}


def main():
    parser = argparse.ArgumentParser(description="Capture interface state via gNMI")
    parser.add_argument(
        "--interface", "-i",
        default="GigabitEthernet0/0",
        help="Interface name to capture",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output fixture file (default: fixtures/interfaces/raw-interface-state.json)",
    )
    args = parser.parse_args()

    output_path = args.output or "fixtures/interfaces/raw-interface-state.json"

    print(f"Capturing interface: {args.interface}")
    print(f"Device: {settings.gnmi_host}:{settings.gnmi_port}")
    print()

    # OpenConfig get
    oc_path = f"/interfaces/interface[name={args.interface}]"
    print(f"→ OpenConfig: {oc_path}")
    oc_response = run_gnmic_get(oc_path)

    if oc_response:
        oc_data = extract_interface_data(oc_response)
        print(f"  ✅ Got OpenConfig response ({len(json.dumps(oc_data))} bytes)")
    else:
        oc_data = None
        print("  ❌ No OpenConfig response")

    # Cisco-native get (may not work)
    cn_path = f"Cisco-IOS-XE-interfaces-oper:/interfaces/interface[name={args.interface}]"
    print(f"→ Cisco-native: {cn_path}")
    cn_response = run_gnmic_get(cn_path)

    if cn_response:
        cn_data = extract_interface_data(cn_response)
        print(f"  ✅ Got Cisco-native response ({len(json.dumps(cn_data))} bytes)")
    else:
        cn_data = None
        print("  ❌ Cisco-native not available (OpenConfig is primary)")

    # Build combined fixture
    fixture = {
        "interface_name": args.interface,
        "device_id": "iosxe-sandbox",
        "device_host": settings.gnmi_host,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "openconfig_response": oc_response,
        "cisco_native_response": cn_response,
        "notes": [
            "OpenConfig is the primary model family for this sandbox.",
            "Cisco-native path may fail if origin-based paths are not supported.",
        ],
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(fixture, f, indent=2)

    print(f"\n✅ Fixture saved: {output_path}")
    print(f"   Size: {Path(output_path).stat().st_size} bytes")


if __name__ == "__main__":
    main()
