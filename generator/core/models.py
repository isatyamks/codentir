from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class Alert(BaseModel):
    id: str # PagerDuty incident/alert ID
    summary: str
    service: dict = Field(default_factory=dict) # {"id": "...", "summary": "..."}
    severity: str
    created_at: datetime


class API(BaseModel):
    id: str
    name: str
    service_id: str
    method: str
    path: str
    description: str


class ArchitectureDecisionRecord(BaseModel):
    id: str
    title: str
    service_id: str
    status: str
    body: dict = Field(default_factory=dict) # Confluence format: {"storage": {"value": "<p>...</p>", "representation": "storage"}}
    created_at: datetime


class Deployment(BaseModel):
    id: str
    service_id: str
    release_id: str
    deployed_at: datetime
    status: str = "success"
    environment: str = "production"


class DesignDoc(BaseModel):
    id: str
    title: str
    author_id: str
    content: str
    related_service_ids: List[str] = Field(default_factory=list)
    created_at: datetime


class Employee(BaseModel):
    id: str
    profile: Dict[str, str] = Field(default_factory=dict)
    status: str = "ACTIVE"


class GithubAuthor(BaseModel):
    name: str
    email: str
    date: datetime


class GithubCommit(BaseModel):
    sha: str
    commit: GithubCommitData
    html_url: str
    repository: str


class GithubCommitData(BaseModel):
    author: GithubAuthor
    message: str
    files_changed: List[str] = Field(default_factory=list)
    diff_summary: str


class GithubPullRequest(BaseModel):
    id: int
    number: int
    title: str
    state: str
    user: GithubUser
    body: str
    created_at: datetime
    merged_at: Optional[datetime] = None
    commits: List[str] = Field(default_factory=list)


class GithubUser(BaseModel):
    login: str


class Incident(BaseModel):
    id: str
    title: str
    symptoms: str
    observations: str
    impacted_service_ids: List[str] = Field(default_factory=list)
    alert_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    resolved_at: Optional[datetime] = None


class JiraIssue(BaseModel):
    id: str
    key: str
    fields: JiraIssueFields


class JiraIssueFields(BaseModel):
    summary: str
    description: str
    issuetype: JiraIssueType
    status: JiraStatus
    assignee: Optional[JiraUser] = None
    created: datetime
    updated: datetime
    resolutiondate: Optional[datetime] = None
    # Custom fields mapping to our internal data
    customfield_requirement_id: Optional[str] = None
    customfield_service_ids: List[str] = Field(default_factory=list)


class JiraIssueType(BaseModel):
    name: str


class JiraStatus(BaseModel):
    name: str


class JiraUser(BaseModel):
    accountId: str
    displayName: str


class Log(BaseModel):
    id: str
    service_id: str
    level: str # warning, error, exception
    message: str
    stack_trace: Optional[str] = None
    timestamp: datetime


class MeetingNote(BaseModel):
    id: str
    title: str
    attendees: List[str] = Field(default_factory=list)
    content: str
    timestamp: datetime


class Metric(BaseModel):
    id: str
    name: str # e.g. latency, error_rate, cpu, memory
    service_id: str
    value: float
    unit: str
    timestamp: datetime


class Postmortem(BaseModel):
    id: str
    incident_id: str
    title: str
    content: str
    root_cause_summary: str
    lessons_learned: str
    created_at: datetime


class Release(BaseModel):
    id: str
    version: str
    repository_id: str
    pr_ids: List[str] = Field(default_factory=list)
    created_at: datetime


class Repository(BaseModel):
    id: str
    name: str
    service_id: str
    url: str


class Requirement(BaseModel):
    id: str
    title: str
    owner_id: str
    business_objective: str
    priority: str
    affected_service_ids: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    created_at: datetime


class Runbook(BaseModel):
    id: str
    title: str
    service_id: str
    content: str
    created_at: datetime


class Service(BaseModel):
    id: str
    name: str
    team_id: str
    description: str
    depends_on_ids: List[str] = Field(default_factory=list)


class SlackMessage(BaseModel):
    id: Optional[str] = None
    client_msg_id: Optional[str] = None
    text: str
    user_id: Optional[str] = None
    user: Optional[str] = None
    timestamp: Optional[datetime] = None
    ts: Optional[str] = None
    channel: str
    type: str = "message"
    team: str = "T12345"
    blocks: List[Dict[str, Any]] = Field(default_factory=list)


class Team(BaseModel):
    id: str
    name: str
    members: List[str] = Field(default_factory=list)


class TestCase(BaseModel):
    id: str
    title: str
    type: str # functional, integration
    requirement_id: str
    service_id: str
    created_at: datetime
