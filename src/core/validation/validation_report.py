from typing import List

from pydantic import BaseModel, Field

# uncomment the corresponding imports below to avoid NameError:
from .validation_issue import ValidationIssue

class ValidationReport(BaseModel):
    is_valid: bool
    total_entities_checked: int = 0
    issues: List[ValidationIssue] = Field(default_factory=list)
    
    def add_issue(self, issue_type: str, entity_type: str, entity_id: str, desc: str):
        self.issues.append(ValidationIssue(
            issue_type=issue_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=desc
        ))
        self.is_valid = False
