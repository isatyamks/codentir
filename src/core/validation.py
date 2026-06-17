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

class ValidationOrchestrator:
    def __init__(self, dataset):
        self.dataset = dataset

    def run_all_validations(self) -> ValidationReport:
        # Mock implementation returning a valid report
        report = ValidationReport(is_valid=True)
        
        # Calculate total entities as a placeholder
        total = 0
        if hasattr(self.dataset, 'tickets'): total += len(self.dataset.tickets)
        if hasattr(self.dataset, 'commits'): total += len(self.dataset.commits)
        if hasattr(self.dataset, 'incidents'): total += len(self.dataset.incidents)
        if hasattr(self.dataset, 'slack_messages'): total += len(self.dataset.slack_messages)
        
        report.total_entities_checked = total
        return report
