"""
Validation models — flattened from core/validation/validation_issue.py + validation_report.py.
"""

from typing import List

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    issue_type: str  # orphan, temporal, schema, missing_ref
    entity_type: str
    entity_id: str
    description: str


class ValidationReport(BaseModel):
    is_valid: bool
    total_entities_checked: int = 0
    issues: List[ValidationIssue] = Field(default_factory=list)

    def add_issue(
        self, issue_type: str, entity_type: str, entity_id: str, desc: str
    ) -> None:
        self.issues.append(
            ValidationIssue(
                issue_type=issue_type,
                entity_type=entity_type,
                entity_id=entity_id,
                description=desc,
            )
        )
        self.is_valid = False
