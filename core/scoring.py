"""Transparent security scoring system.

Base score: 100, with penalties for findings, capped per category.
"""

from __future__ import annotations

from collections import defaultdict
from core.models import (
    AuditScore,
    CategoryScore,
    Finding,
    FindingStatus,
    RiskLevel,
    Severity,
)


# Default penalty points per severity
DEFAULT_PENALTIES: dict[Severity, int] = {
    Severity.CRITICAL: 8,
    Severity.HIGH: 4,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
    Severity.INFO: 0,
}

# Maximum penalty per category (prevents one noisy category from dominating)
MAX_CATEGORY_PENALTY = 12


class ScoringSystem:
    """Calculate a transparent overall and per-category security score."""

    def __init__(
        self,
        base_score: int = 100,
        penalties: dict[Severity, int] | None = None,
        max_category_penalty: int = MAX_CATEGORY_PENALTY,
    ) -> None:
        self.base_score = base_score
        self.penalties = penalties or dict(DEFAULT_PENALTIES)
        self.max_category_penalty = max_category_penalty

    def calculate_score(self, findings: list[Finding]) -> AuditScore:
        """Calculate overall and per-category scores from findings."""

        # Group by category
        by_category: dict[str, list[Finding]] = defaultdict(list)
        for f in findings:
            by_category[f.category].append(f)

        category_scores: list[CategoryScore] = []
        overall_penalty = 0
        totals = {sev: 0 for sev in Severity}

        for category, cat_findings in sorted(by_category.items()):
            counts = {sev: 0 for sev in Severity}
            cat_penalty = 0

            for f in cat_findings:
                sev = f.severity if isinstance(f.severity, Severity) else Severity(f.severity)
                if f.status == FindingStatus.FAIL:
                    cat_penalty += self.penalties.get(sev, 0)
                    counts[sev] += 1
                    totals[sev] += 1
                elif f.status == FindingStatus.WARNING:
                    # Warnings count at half penalty
                    cat_penalty += max(1, self.penalties.get(sev, 0) // 2)
                    counts[sev] += 1
                    totals[sev] += 1
                # PASS / NOT_APPLICABLE / UNAVAILABLE don't penalise

            # Cap per category
            cat_penalty = min(cat_penalty, self.max_category_penalty)
            overall_penalty += cat_penalty

            category_scores.append(CategoryScore(
                category=category,
                score=max(0, 100 - cat_penalty),
                max_score=100,
                findings_count=len(cat_findings),
                critical_count=counts[Severity.CRITICAL],
                high_count=counts[Severity.HIGH],
                medium_count=counts[Severity.MEDIUM],
                low_count=counts[Severity.LOW],
                info_count=counts[Severity.INFO],
            ))

        final_score = max(0, min(100, self.base_score - overall_penalty))
        risk_level = self._risk_level(final_score)

        return AuditScore(
            overall_score=final_score,
            risk_level=risk_level,
            category_scores=category_scores,
            total_findings=sum(1 for f in findings
                               if f.status in (FindingStatus.FAIL, FindingStatus.WARNING)),
            critical_count=totals[Severity.CRITICAL],
            high_count=totals[Severity.HIGH],
            medium_count=totals[Severity.MEDIUM],
            low_count=totals[Severity.LOW],
            info_count=totals[Severity.INFO],
        )

    @staticmethod
    def _risk_level(score: int) -> RiskLevel:
        if score >= 90:
            return RiskLevel.EXCELLENT
        if score >= 75:
            return RiskLevel.GOOD
        if score >= 60:
            return RiskLevel.NEEDS_IMPROVEMENT
        if score >= 40:
            return RiskLevel.HIGH_RISK
        return RiskLevel.CRITICAL_RISK
