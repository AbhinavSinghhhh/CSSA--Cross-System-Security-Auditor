"""Data normalization utilities for cross-platform security auditing."""

from __future__ import annotations

import ipaddress
from core.models import NetworkExposure, ServiceStatus, ServiceStartup


class Normalizer:
    """Normalizes raw data collected from different operating systems into unified models."""

    @staticmethod
    def classify_network_exposure(address: str) -> NetworkExposure:
        """Classify a network address as LOCAL_ONLY, NETWORK_EXPOSED, or UNKNOWN."""
        if not address:
            return NetworkExposure.UNKNOWN

        clean_addr = address.strip()
        # Handle wildcard / all interfaces
        if clean_addr in ("0.0.0.0", "::", "*", "0:0:0:0:0:0:0:0"):
            return NetworkExposure.NETWORK_EXPOSED

        try:
            ip = ipaddress.ip_address(clean_addr)
            if ip.is_loopback:
                return NetworkExposure.LOCAL_ONLY
            else:
                return NetworkExposure.NETWORK_EXPOSED
        except ValueError:
            # Check for domain-like localhost
            if clean_addr.lower() in ("localhost", "127.0.0.1", "::1"):
                return NetworkExposure.LOCAL_ONLY
            return NetworkExposure.UNKNOWN

    @staticmethod
    def normalize_service_status(status_str: str) -> ServiceStatus:
        """Normalize raw service status string to ServiceStatus enum."""
        if not status_str:
            return ServiceStatus.UNKNOWN
        s = status_str.lower().strip()
        # Check negative states first to avoid 'active' matching inside 'inactive'
        if any(w in s for w in ("stop", "inactive", "dead", "pause", "exited", "disabled")):
            return ServiceStatus.STOPPED
        elif any(w in s for w in ("running", "run", "start", "active")):
            return ServiceStatus.RUNNING
        return ServiceStatus.UNKNOWN

    @staticmethod
    def normalize_service_startup(startup_str: str) -> ServiceStartup:
        """Normalize raw service startup string to ServiceStartup enum."""
        if not startup_str:
            return ServiceStartup.UNKNOWN
        s = startup_str.lower().strip()
        if any(w in s for w in ("disable", "mask")):
            return ServiceStartup.DISABLED
        elif any(w in s for w in ("auto", "enable")):
            return ServiceStartup.AUTOMATIC
        elif any(w in s for w in ("manual", "demand")):
            return ServiceStartup.MANUAL
        return ServiceStartup.UNKNOWN
