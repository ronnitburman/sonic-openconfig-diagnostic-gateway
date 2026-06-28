"""gNMI client — wraps the ``gnmic`` CLI for live device interaction.

Uses subprocess to call gnmic rather than native Python gRPC, which
avoids protobuf compilation issues across platforms.  Can be replaced
with a native gRPC client later without changing the public API.
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any


class GnmiClientError(Exception):
    """Raised when a gNMI operation fails at the transport layer."""


class GnmiClient:
    """Low-level gNMI client backed by the ``gnmic`` CLI."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        insecure: bool = False,
        skip_verify: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.insecure = insecure
        self.skip_verify = skip_verify

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def capabilities(self) -> dict:
        """Run gNMI Capabilities RPC and return parsed JSON."""
        args = self._base_args() + ["capabilities", "--format", "json"]
        raw = self._run(args)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise GnmiClientError(f"Non-JSON capabilities response: {raw[:200]}")

    def get(self, path: str, encoding: str = "JSON_IETF") -> list[dict]:
        """Run gNMI Get RPC for *path* and return the notification list."""
        args = self._base_args() + [
            "get",
            "--path", path,
            "--encoding", encoding,
            "--format", "json",
        ]
        raw = self._run(args)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise GnmiClientError(f"Non-JSON Get response for '{path}': {raw[:200]}")

    def set(self, updates: list[dict], encoding: str = "JSON_IETF") -> dict:
        """Run gNMI Set RPC with *updates* and return the parsed response.

        Each update dict should have ``path`` and ``value`` keys.
        The value is serialised as a JSON string for the gNMI Update.
        """
        args = self._base_args() + [
            "set",
            "--encoding", encoding,
            "--format", "json",
        ]
        for update in updates:
            # gnmic set uses separate --update-path / --update-value flags.
            # The inline --update "path:value" format chokes on paths with
            # brackets and slash-heavy values.
            path = update["path"].lstrip("/")
            args.extend(["--update-path", path])
            args.extend(["--update-value", str(update["value"])])
        raw = self._run(args)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise GnmiClientError(f"Non-JSON Set response: {raw[:200]}")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _base_args(self) -> list[str]:
        cmd = [
            "gnmic",
            "-a", f"{self.host}:{self.port}",
            "-u", self.username,
            "-p", self.password,
        ]
        if self.insecure:
            cmd.append("--insecure")
        else:
            cmd.append("--skip-verify")
        return cmd

    def _run(self, args: list[str], timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError:
            raise GnmiClientError(
                "gnmic not found on PATH. Install with: brew install gnmic"
            )
        except subprocess.TimeoutExpired:
            raise GnmiClientError(
                f"gnmic timed out after {timeout}s: {' '.join(args)}"
            )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise GnmiClientError(
                f"gnmic failed (exit {result.returncode}): {stderr}"
            )

        return result.stdout.strip()
