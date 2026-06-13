from datetime import timedelta
import random

import faker

from generator.core.engine import SimulationEngine
from generator.core.models import (
    Alert,
    Deployment,
    GithubAuthor,
    GithubCommit,
    GithubCommitData,
    GithubPullRequest,
    GithubUser,
    Incident,
    JiraIssue,
    JiraIssueFields,
    JiraIssueType,
    JiraStatus,
    Log,
    Metric,
    Postmortem,
    Release,
)
from .story import _simulate_story

fake = faker.Faker()


def _simulate_deep_incident_story(engine: SimulationEngine, story_idx: int):
    """
    Creates a complex, deep cascading incident.
    Commit (Service N) -> PR -> Release -> Deployment ->
    Failures cascade up through Service N-1, N-2 ... -> Service 0 ->
    Alert (Service 0) -> Incident (Service 0).
    """
    if not engine.generator.services or len(engine.generator.services) < 3:
        return _simulate_story(engine, story_idx)

    deep_srv = engine.generator.services[-1]
    front_srv = engine.generator.services[0]

    owner = engine.get_random_employee()
    engine.advance_time(2)

    # 1. Ticket
    ticket = JiraIssue(
        id=f"1000{story_idx}",
        key=f"TICKET-{story_idx * 10}",
        fields=JiraIssueFields(
            summary=f"Fix: Memory leak in {deep_srv.name}",
            description="Addressing performance issues deep in the stack.",
            issuetype=JiraIssueType(name="Bug"),
            status=JiraStatus(name="Done"),
            created=engine.current_date,
            updated=engine.current_date,
            customfield_service_ids=[deep_srv.id],
        ),
    )
    engine.generator.tickets.append(ticket)

    # 2. Commit in Deep Service
    engine.advance_time(1)
    sha = fake.sha1()
    commit = GithubCommit(
        sha=sha,
        commit=GithubCommitData(
            author=GithubAuthor(
                name=owner.profile.get("firstName", "Bob")
                + " "
                + owner.profile.get("lastName", ""),
                email="bob@company.com",
                date=engine.current_date,
            ),
            message=f"Refactored cache logic to fix memory leak (fixes {ticket.key})",
            files_changed=["cache/manager.py"],
            diff_summary="Removed timeout limits, causing unbounded caching.",
        ),
        html_url=f"https://github.com/company/repo/commit/{sha}",
        repository=f"repo-{deep_srv.id.split('-')[-1]}",
    )
    engine.generator.commits.append(commit)

    # 3. Pull Request
    engine.advance_time(1)
    pr = GithubPullRequest(
        id=random.randint(100000, 999999),
        number=story_idx * 10 + 1,
        title="Fix cache memory leak",
        state="closed",
        user=GithubUser(login=owner.id),
        body=f"Fixes {ticket.key}",
        created_at=engine.current_date,
        merged_at=engine.current_date,
        commits=[sha],
    )
    engine.generator.pull_requests.append(pr)

    # 4. Release
    engine.advance_time(1)
    release = Release(
        id=f"REL-{story_idx}",
        version="v2.0.0",
        repository_id=commit.repository,
        pr_ids=[str(pr.id)],
        created_at=engine.current_date,
    )
    engine.generator.releases.append(release)

    # 5. Deployment
    engine.advance_time(1)
    deployment = Deployment(
        id=f"DEPLOY-{story_idx * 10}",
        service_id=deep_srv.id,
        release_id=release.id,
        deployed_at=engine.current_date,
        status="success",
        environment="production",
    )
    engine.generator.deployments.append(deployment)

    # Cascading failure: deep service breaks → frontend fails
    engine.advance_time(1)

    # 6. Metric Spike on Frontend
    engine.generator.metrics.append(
        Metric(
            id=f"METRIC-{story_idx}-FRONT",
            name="latency",
            service_id=front_srv.id,
            value=5000.0,
            unit="ms",
            timestamp=engine.current_date,
        )
    )

    # 7. Error Log on Frontend
    engine.generator.logs.append(
        Log(
            id=f"LOG-{story_idx}-FRONT",
            service_id=front_srv.id,
            level="error",
            message="Timeout waiting for upstream services",
            stack_trace="TimeoutError: Request to downstream service failed after 5000ms",
            timestamp=engine.current_date,
        )
    )

    # 8. Alert on Frontend
    engine.advance_time(1)
    alert = Alert(
        id=f"ALERT-{story_idx}-FRONT",
        summary=f"Critical Latency on {front_srv.name}",
        service={"id": front_srv.id, "summary": "Frontend gateway"},
        severity="critical",
        created_at=engine.current_date,
    )
    engine.generator.alerts.append(alert)

    # 9. Incident
    engine.advance_time(1)
    incident = Incident(
        id=f"INC-{story_idx}",
        title="Massive frontend outage",
        symptoms=f"Users cannot load the main page. PagerDuty fired alert {alert.id}.",
        observations="Frontend latency spiked to 5000ms.",
        impacted_service_ids=[front_srv.id],
        alert_ids=[alert.id],
        created_at=engine.current_date,
        resolved_at=engine.current_date + timedelta(hours=2),
    )
    engine.generator.incidents.append(incident)

    # 10. Postmortem
    engine.advance_time(1)
    engine.generator.postmortems.append(
        Postmortem(
            id=f"PM-{story_idx}",
            incident_id=incident.id,
            title="Postmortem: Massive frontend outage",
            content=f"On {incident.created_at}, frontend services failed.",
            root_cause_summary=f"The root cause was a cache memory exhaustion introduced in PR #{pr.number} which was deployed to {deep_srv.name} in {deployment.id}, causing a cascading timeout.",
            lessons_learned="Implement circuit breakers on the frontend.",
            created_at=engine.current_date,
        )
    )
