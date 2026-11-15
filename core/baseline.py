"""Baseline creation and comparison manager."""

from __future__ import annotations

from typing import List, Tuple
from core.models import AuditResult, BaselineItem, BaselineDiff, ServiceStartup


class BaselineManager:
    """Manages baseline snapshots and calculates configuration drift."""

    @staticmethod
    def create_baseline(audit: AuditResult) -> List[BaselineItem]:
        items: List[BaselineItem] = []

        if audit.firewall:
            items.append(
                BaselineItem(
                    category="Firewall",
                    key="status",
                    value="ACTIVE" if audit.firewall.enabled else "INACTIVE",
                    details=f"Provider: {audit.firewall.provider}; Details: {audit.firewall.details}"
                )
            )

        for u in audit.users:
            if u.is_admin:
                items.append(
                    BaselineItem(
                        category="AdminUsers",
                        key=u.username,
                        value="admin",
                        details=u.description or "Administrator Account"
                    )
                )

        for s in audit.services:
            st = s.startup_type.value if hasattr(s.startup_type, 'value') else str(s.startup_type)
            if "auto" in st.lower():
                items.append(
                    BaselineItem(
                        category="AutoServices",
                        key=s.name,
                        value=s.status.value if hasattr(s.status, 'value') else str(s.status),
                        details=s.display_name or s.name
                    )
                )

        for c in audit.network_connections:
            if c.state == "LISTEN":
                exp = c.exposure.value if hasattr(c.exposure, 'value') else str(c.exposure)
                items.append(
                    BaselineItem(
                        category="ListeningPorts",
                        key=f"{c.protocol}/{c.local_port}",
                        value=exp,
                        details=f"{c.local_address}:{c.local_port} (PID: {c.pid}, Process: {c.process_name})"
                    )
                )

        for policy in audit.security_policies:
            items.append(
                BaselineItem(
                    category="SecurityPolicy",
                    key=policy.name,
                    value=str(policy.current_value),
                    details=policy.description or ""
                )
            )

        return items

    @staticmethod
    def compare_baseline(baseline: List[BaselineItem], current: List[BaselineItem]) -> BaselineDiff:
        base_dict = {(item.category, item.key): item for item in baseline}
        curr_dict = {(item.category, item.key): item for item in current}

        added: List[BaselineItem] = []
        removed: List[BaselineItem] = []
        changed: List[Tuple[BaselineItem, BaselineItem]] = []

        for k, v in curr_dict.items():
            if k not in base_dict:
                added.append(v)
            elif base_dict[k].value != v.value:
                changed.append((base_dict[k], v))

        for k, v in base_dict.items():
            if k not in curr_dict:
                removed.append(v)

        return BaselineDiff(added=added, removed=removed, changed=changed)
