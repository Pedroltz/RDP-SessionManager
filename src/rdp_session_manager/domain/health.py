"""Portable health models and schemas."""
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

HEALTH_SCHEMA_VERSION = 1
VALID_STATUSES = ("healthy", "warning", "critical", "unknown")
STATUS_PRIORITY = {"healthy": 0, "unknown": 1, "warning": 2, "critical": 3}


@dataclass(frozen=True)
class HealthCheck:
    check_id: str
    scope: str
    target: str
    status: str
    summary: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    remediation_id: str = ""

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid health status: {self.status}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.check_id,
            "scope": self.scope,
            "target": self.target,
            "status": self.status,
            "summary": self.summary,
            "evidence": self.evidence,
            "remediation_id": self.remediation_id or None,
        }


@dataclass(frozen=True)
class HealthReport:
    captured_at: str
    checks: List[HealthCheck]
    schema_version: int = HEALTH_SCHEMA_VERSION

    @property
    def overall_status(self) -> str:
        if not self.checks:
            return "unknown"
        return max(self.checks, key=lambda item: STATUS_PRIORITY[item.status]).status

    @property
    def counts(self) -> Dict[str, int]:
        return {
            status: sum(1 for check in self.checks if check.status == status)
            for status in VALID_STATUSES
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "captured_at": self.captured_at,
            "overall_status": self.overall_status,
            "counts": self.counts,
            "checks": [check.to_dict() for check in self.checks],
        }

    def filter_checks(
        self,
        status: str = "",
        scope: str = "",
        query: str = "",
    ) -> List[HealthCheck]:
        """Return checks matching GTK/CLI-friendly filters."""
        if status and status not in VALID_STATUSES:
            raise ValueError(f"Invalid health status filter: {status}")
        normalized_query = query.strip().casefold()
        result = []
        for check in self.checks:
            if status and check.status != status:
                continue
            if scope and check.scope != scope:
                continue
            searchable = " ".join((
                check.check_id,
                check.scope,
                check.target,
                check.summary,
                json.dumps(check.evidence, sort_keys=True, default=str),
            )).casefold()
            if normalized_query and normalized_query not in searchable:
                continue
            result.append(check)
        return result


