"""Portable remediation models and schemas."""
from dataclasses import dataclass, field
from typing import Any, Dict, List

REPAIR_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RepairStep:
    step_id: str
    summary: str
    reversible: bool
    disruptive: bool = False
    requires_privilege: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.step_id,
            "summary": self.summary,
            "reversible": self.reversible,
            "disruptive": self.disruptive,
            "requires_privilege": self.requires_privilege,
        }


@dataclass(frozen=True)
class RepairPlan:
    plan_id: str
    generated_at: str
    target_type: str
    target: str
    precondition_hash: str
    applicable: bool
    blockers: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    steps: List[RepairStep] = field(default_factory=list)
    schema_version: int = REPAIR_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "generated_at": self.generated_at,
            "target_type": self.target_type,
            "target": self.target,
            "precondition_hash": self.precondition_hash,
            "applicable": self.applicable,
            "blockers": self.blockers,
            "issues": self.issues,
            "requires_privilege": any(step.requires_privilege for step in self.steps),
            "disruptive": any(step.disruptive for step in self.steps),
            "steps": [step.to_dict() for step in self.steps],
        }


