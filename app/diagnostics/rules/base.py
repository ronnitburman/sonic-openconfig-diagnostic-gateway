"""Base class for all diagnostic rules."""

from abc import ABC, abstractmethod

from app.models import InterfaceSnapshot, InterfaceExpectation, DiagnosticFinding


class DiagnosticRule(ABC):
    """Every diagnostic rule evaluates a snapshot + expectations → Finding | None.

    ``None`` means the rule passed — no problem detected.
    """

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier, e.g. 'LINK-001'."""
        ...

    @property
    @abstractmethod
    def severity(self) -> str:
        """Default severity: HIGH, MEDIUM, LOW, or INFO."""
        ...

    @property
    @abstractmethod
    def title(self) -> str:
        """Human-readable one-line description of the problem."""
        ...

    @abstractmethod
    def evaluate(
        self,
        snapshot: InterfaceSnapshot,
        expected: InterfaceExpectation,
    ) -> DiagnosticFinding | None:
        """Evaluate rule.  Returns a Finding when triggered, None when healthy."""
        ...

    @abstractmethod
    def recommendation(self) -> str:
        """Actionable recommendation when this rule triggers."""
        ...

    # ------------------------------------------------------------------
    # helper
    # ------------------------------------------------------------------

    def _finding(self, evidence: dict, severity: str | None = None) -> DiagnosticFinding:
        return DiagnosticFinding(
            rule_id=self.rule_id,
            severity=severity or self.severity,
            title=self.title,
            evidence=evidence,
            recommendation=self.recommendation(),
        )
