#!/usr/bin/env python3
"""Test the adapter layer by fetching an InterfaceSnapshot.

Usage:
    # Fixture mode (default)
    python scripts/gnmi_get_interface.py -i GigabitEthernet0/0

    # Live mode
    DEVICE_MODE=live python scripts/gnmi_get_interface.py -i GigabitEthernet0/0

    # Different device
    python scripts/gnmi_get_interface.py -d iosxe-sandbox -i Vlan1
"""

import argparse
import json
import sys

from app.adapters import create_adapter
from app.config import settings
from app.models import DeviceTarget


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch an InterfaceSnapshot")
    parser.add_argument(
        "--device", "-d",
        default="iosxe-sandbox",
        help="Device ID (default: iosxe-sandbox)",
    )
    parser.add_argument(
        "--interface", "-i",
        default="GigabitEthernet0/0",
        help="Interface name",
    )
    args = parser.parse_args()

    print(f"Device:  {args.device}")
    print(f"Mode:    {settings.device_mode}")
    print(f"Interface: {args.interface}")
    print()

    device = DeviceTarget(
        device_id=args.device,
        host=settings.gnmi_host,
        port=settings.gnmi_port,
        username=settings.gnmi_username,
        password=settings.gnmi_password,
    )

    try:
        adapter = create_adapter(device)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        snapshot = adapter.get_interface_snapshot(args.interface)
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(snapshot.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
