from pydantic import BaseModel

# uncomment the corresponding imports below to avoid NameError:
# from .validation_report import ValidationReport

class ValidationIssue(BaseModel):
    issue_type: str  # orphan, temporal, schema, missing_ref
    entity_type: str
    entity_id: str
    description: str
