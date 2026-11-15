"""Scanner — orchestrates data collection from a platform adapter.

Each collection method is called independently with its own error handling
so that a failure in one module does not prevent others from running.
"""

from __future__ import annotations

import logging
from typing import Any

from platforms.base import SecurityPlatformAdapter
from core.models import FirewallStatus, PacketCaptureAudit, SystemInfo

logger = logging.getLogger(__name__)


class Scanner:
    """Runs each platform adapter method and returns aggregated results."""

    def __init__(self, adapter: SecurityPlatformAdapter) -> None:
        self.adapter = adapter

    def scan(self) -> dict[str, Any]:
        """Collect all data categories and return a dict keyed by category."""
        results: dict[str, Any] = {}

        # Each tuple: (result_key, adapter_method, default_on_failure)
        methods: list[tuple[str, str, Any]] = [
            ("system_info", "get_system_info", SystemInfo()),
            ("users", "get_users", []),
            ("groups", "get_groups", []),
            ("processes", "get_processes", []),
            ("services", "get_services", []),
            ("firewall", "get_firewall_status", FirewallStatus()),
            ("network_connections", "get_network_connections", []),
            ("file_permissions", "get_file_permissions", []),
            ("startup_entries", "get_startup_items", []),
            ("security_policies", "get_security_policies", []),
            ("packet_capture", "get_packet_capture_audit", PacketCaptureAudit()),
        ]

        for key, method_name, default in methods:
            try:
                method = getattr(self.adapter, method_name, None)
                if method is None:
                    logger.warning("Adapter has no method: %s", method_name)
                    results[key] = default
                    continue
                results[key] = method()
                logger.debug("Scanned %s — %s items",
                             key,
                             len(results[key]) if isinstance(results[key], list) else "1")
            except NotImplementedError:
                logger.info("Method %s not implemented for this adapter", method_name)
                results[key] = default
            except Exception as exc:
                logger.error("Error scanning %s: %s", key, exc, exc_info=True)
                results[key] = default

        return results
