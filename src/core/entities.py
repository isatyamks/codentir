from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Entity(BaseModel):
    id: str
    tenant_id: str = "tenant_default"


class API(Entity):
    name: str
    service_id: str
    method: str
    path: str
    description: str


class Alert(Entity):
    summary: str
    service: dict = Field(default_factory=dict)
    severity: str
    created_at: str


class ArchitectureDecisionRecord(Entity):
    title: str
    service_id: str
    status: str
    body: dict = Field(default_factory=dict)
    created_at: str


class Commit(Entity):
    sha: str
    message: str
    author_name: str
    date: datetime
    repository: str
    files_changed: List[str] = Field(default_factory=list)
    diff_summary: Optional[str] = None


class Deployment(Entity):
    service_id: str
    release_id: str
    deployed_at: datetime
    status: str = "success"
    environment: str = "production"


class Employee(Entity):
    profile: Dict[str, str] = Field(default_factory=dict)
    status: str = "ACTIVE"


class Incident(Entity):
    title: str
    symptoms: str
    observations: str
    impacted_service_ids: List[str] = Field(default_factory=list)
    alert_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    resolved_at: Optional[datetime] = None


class Log(Entity):
    service_id: str
    level: str
    message: str
    stack_trace: Optional[str] = None
    timestamp: str


class Metric(Entity):
    name: str
    service_id: str
    value: float
    unit: str
    timestamp: str


class Postmortem(Entity):
    incident_id: str
    title: str
    content: str
    root_cause_summary: str
    lessons_learned: str
    created_at: str


class PullRequest(Entity):
    number: int
    title: str
    state: str
    author_id: str
    body: str
    created_at: datetime
    merged_at: Optional[datetime] = None
    commit_shas: List[str] = Field(default_factory=list)


class Release(Entity):
    version: str
    repository_id: str
    pr_ids: List[str]
    created_at: str


class Repository(Entity):
    name: str
    service_id: str
    url: str


class Requirement(Entity):
    title: str
    owner_id: str
    business_objective: str
    priority: str
    affected_service_ids: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    created_at: datetime


class Runbook(Entity):
    title: str
    service_id: str
    content: str
    created_at: str


class Service(Entity):
    name: str
    team_id: str
    description: str
    depends_on_ids: List[str] = Field(default_factory=list)


class SlackMessage(Entity):
    channel: str
    text: str
    user_id: str
    timestamp: datetime


class Team(Entity):
    name: str
    members: List[str] = Field(default_factory=list)


class TestCase(Entity):
    title: str
    type: str
    requirement_id: str
    service_id: str
    created_at: datetime


class Ticket(Entity):
    key: str
    summary: str
    description: str
    issuetype: str
    status: str
    assignee_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    requirement_id: Optional[str] = None
    service_ids: List[str] = Field(default_factory=list)


class Dataset(BaseModel):
    """Top-level aggregate holding all generated domain entities."""

    employees: Dict[str, Employee] = Field(default_factory=dict)
    teams: Dict[str, Team] = Field(default_factory=dict)
    services: Dict[str, Service] = Field(default_factory=dict)
    repositories: Dict[str, Repository] = Field(default_factory=dict)
    apis: Dict[str, API] = Field(default_factory=dict)
    adrs: Dict[str, ArchitectureDecisionRecord] = Field(default_factory=dict)
    runbooks: Dict[str, Runbook] = Field(default_factory=dict)
    requirements: Dict[str, Requirement] = Field(default_factory=dict)
    tickets: Dict[str, Ticket] = Field(default_factory=dict)
    commits: Dict[str, Commit] = Field(default_factory=dict)
    pull_requests: Dict[str, PullRequest] = Field(default_factory=dict)
    releases: Dict[str, Release] = Field(default_factory=dict)
    deployments: Dict[str, Deployment] = Field(default_factory=dict)
    metrics: Dict[str, Metric] = Field(default_factory=dict)
    logs: Dict[str, Log] = Field(default_factory=dict)
    alerts: Dict[str, Alert] = Field(default_factory=dict)
    incidents: Dict[str, Incident] = Field(default_factory=dict)
    postmortems: Dict[str, Postmortem] = Field(default_factory=dict)
    slack_messages: Dict[str, SlackMessage] = Field(default_factory=dict)
    test_cases: Dict[str, TestCase] = Field(default_factory=dict)
