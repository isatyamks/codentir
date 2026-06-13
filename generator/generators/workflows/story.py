from datetime import datetime, timedelta
import random

import faker

from generator.core.domain_data import (
    ECOMMERCE_DOMAINS,
    generate_commit_message,
    generate_jira_description,
    generate_pr_body,
    generate_slack_message,
    get_random_business_objective,
)
from generator.core.engine import SimulationEngine
from generator.core.models import (
    Alert,
    Deployment,
    DesignDoc,
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
    JiraUser,
    Log,
    MeetingNote,
    Metric,
    Postmortem,
    Release,
    Requirement,
    SlackMessage,
    TestCase,
)

fake = faker.Faker()


def _simulate_story(engine: SimulationEngine, story_idx: int):
    # Requirement
    owner = engine.get_random_employee()
    affected_services = (
        random.sample(
            [s.id for s in engine.generator.services],
            k=min(2, len(engine.generator.services)),
        )
        if engine.generator.services
        else []
    )

    engine.advance_time(random.randint(1, 5))
    is_bug = random.random() > 0.7
    if is_bug:
        req_title = (
            random.choice(engine.config.scenario.bugs)
            if engine.config.scenario
            else random.choice(ECOMMERCE_DOMAINS["bugs"])
        )
    else:
        req_title = (
            random.choice(engine.config.scenario.requirements)
            if engine.config.scenario
            else random.choice(ECOMMERCE_DOMAINS["requirements"])
        )

    req = Requirement(
        id=f"REQ-{story_idx}",
        title=req_title,
        owner_id=owner.id if owner else "unknown",
        business_objective=get_random_business_objective(),
        priority=random.choice(
            ["High", "Medium", "Low"] if not is_bug else ["Critical", "High"]
        ),
        affected_service_ids=affected_services,
        acceptance_criteria=[fake.sentence() for _ in range(2)],
        created_at=engine.current_date,
    )
    engine.generator.requirements.append(req)

    # Design Doc (50% chance)
    if random.random() > 0.5:
        engine.advance_time(random.randint(1, 3))
        doc = DesignDoc(
            id=f"DOC-{story_idx}",
            title=f"Design for {req.title}",
            author_id=req.owner_id,
            content=fake.text(),
            related_service_ids=req.affected_service_ids,
            created_at=engine.current_date,
        )
        engine.generator.design_docs.append(doc)

    # Meeting Note (30% chance)
    if random.random() > 0.7:
        engine.advance_time(1)
        note = MeetingNote(
            id=f"MTG-{story_idx}",
            title=f"Planning for {req.id}",
            attendees=(
                [req.owner_id]
                + [
                    e.id
                    for e in random.sample(
                        engine.generator.employees,
                        k=min(3, len(engine.generator.employees)),
                    )
                ]
                if engine.generator.employees
                else []
            ),
            content=fake.paragraph(),
            timestamp=engine.current_date,
        )
        engine.generator.meeting_notes.append(note)

    # Jira Ticket
    engine.advance_time(random.randint(1, 3))
    jira_user = (
        JiraUser(accountId=req.owner_id, displayName=fake.name()) if owner else None
    )
    ticket = JiraIssue(
        id=f"{random.randint(10000, 99999)}",
        key=f"TICKET-{story_idx * 10}",
        fields=JiraIssueFields(
            summary=f"Implement: {req.title}" if not is_bug else f"Fix: {req.title}",
            description=generate_jira_description(
                req.title,
                is_bug,
                req.affected_service_ids[0]
                if req.affected_service_ids
                else "core-service",
            ),
            issuetype=JiraIssueType(
                name="Bug" if is_bug else random.choice(["Story", "Task"])
            ),
            status=JiraStatus(name="Done"),
            assignee=jira_user,
            created=engine.current_date,
            updated=engine.current_date + timedelta(days=random.randint(5, 10)),
            resolutiondate=engine.current_date + timedelta(days=random.randint(5, 10)),
            customfield_requirement_id=req.id,
            customfield_service_ids=req.affected_service_ids,
        ),
    )
    engine.generator.tickets.append(ticket)

    # Slack: start work
    engine.advance_time(1)
    engine.generator.slack_messages.append(
        SlackMessage(
            client_msg_id=str(fake.uuid4()),
            text=generate_slack_message(
                "start_work",
                req.owner_id,
                ticket.key,
                {
                    "service": req.affected_service_ids[0]
                    if req.affected_service_ids
                    else "backend"
                },
            ),
            user=req.owner_id,
            ts=str(int(engine.current_date.timestamp())),
            channel="#engineering",
        )
    )

    # Commits
    engine.advance_time(random.randint(1, 3))
    commit_shas = []
    for c_idx in range(random.randint(2, 5)):
        sha = fake.sha1()
        commit_date = engine.current_date + timedelta(hours=c_idx * 5)
        service_name = (
            req.affected_service_ids[0] if req.affected_service_ids else "core-service"
        )
        files_changed = [
            f"{service_name}/{random.choice(['cache', 'client', 'handler', 'service', 'repository', 'controller'])}.py"
        ]
        diff_summary = f"Refactored logic in {files_changed[0]}"
        if is_bug and c_idx == 0:
            diff_summary = "Removed Redis fallback and updated retry configuration."

        commit = GithubCommit(
            sha=sha,
            commit=GithubCommitData(
                author=GithubAuthor(
                    name=fake.name(), email=fake.email(), date=commit_date
                ),
                message=generate_commit_message(
                    req.title, ticket.key, service_name, is_bug
                ),
                files_changed=files_changed,
                diff_summary=diff_summary,
            ),
            html_url=f"https://github.com/company/repo/commit/{sha}",
            repository=f"{service_name}-repo",
        )
        engine.generator.commits.append(commit)
        commit_shas.append(sha)

    # Pull Request
    engine.advance_time(2)
    pr = GithubPullRequest(
        id=random.randint(100000, 999999),
        number=story_idx * 10,
        title=f"Feature {req.title}" if not is_bug else f"Fix {req.title}",
        state="closed",
        user=GithubUser(login=req.owner_id),
        body=generate_pr_body(ticket.key, req.title, is_bug),
        created_at=engine.current_date,
        merged_at=engine.current_date,
        commits=commit_shas,
    )
    engine.generator.pull_requests.append(pr)

    # Slack: PR ready
    engine.generator.slack_messages.append(
        SlackMessage(
            client_msg_id=str(fake.uuid4()),
            text=generate_slack_message(
                "pr_ready",
                req.owner_id,
                ticket.key,
                {"pr_url": f"https://github.com/company/repo/pull/{pr.number}"},
            ),
            user=req.owner_id,
            ts=str(int(engine.current_date.timestamp())),
            channel="#engineering",
        )
    )

    # Release
    engine.advance_time(1)
    repo_id = (
        f"repo-{req.affected_service_ids[0].split('-')[1]}"
        if req.affected_service_ids
        else "repo-0"
    )
    release = Release(
        id=f"REL-{story_idx}",
        version=f"v1.{story_idx}.0",
        repository_id=repo_id,
        pr_ids=[str(pr.id)],
        created_at=engine.current_date,
    )
    engine.generator.releases.append(release)

    # Deployment
    engine.advance_time(1)
    deploy_id = f"DEPLOY-{story_idx * 10 + random.randint(1, 9)}"
    deployment = Deployment(
        id=deploy_id,
        service_id=req.affected_service_ids[0] if req.affected_service_ids else "srv-0",
        release_id=release.id,
        deployed_at=engine.current_date,
        status="success",
        environment="production",
    )
    engine.generator.deployments.append(deployment)

    # Test Case
    engine.advance_time(1)
    engine.generator.test_cases.append(
        TestCase(
            id=f"TC-{story_idx}",
            title=f"Verify {req.title}",
            type=random.choice(["functional", "integration"]),
            requirement_id=req.id,
            service_id=req.affected_service_ids[0]
            if req.affected_service_ids
            else "none",
            created_at=engine.current_date,
        )
    )

    # 15% chance of triggering incident causal chain
    if random.random() < 0.15:
        engine.advance_time(1)
        metric = Metric(
            id=f"METRIC-{story_idx}",
            name=random.choice(["latency", "error_rate", "memory_usage"]),
            service_id=deployment.service_id,
            value=random.uniform(5.0, 99.9),
            unit="ms",
            timestamp=engine.current_date,
        )
        engine.generator.metrics.append(metric)

        log = Log(
            id=f"LOG-{story_idx}",
            service_id=deployment.service_id,
            level="error",
            message=f"Database deadlock detected in {deployment.service_id}",
            stack_trace=f"java.sql.SQLException: Deadlock found when trying to get lock\n\tat com.company.{deployment.service_id}.DBHandler",
            timestamp=engine.current_date,
        )
        engine.generator.logs.append(log)

        engine.advance_time(1)
        alert = Alert(
            id=f"ALERT-{story_idx}",
            summary=f"High {metric.name} on {deployment.service_id}",
            service={"id": deployment.service_id, "summary": "Impacted service"},
            severity="critical",
            created_at=engine.current_date,
        )
        engine.generator.alerts.append(alert)

        engine.advance_time(1)
        incident_title = (
            random.choice(engine.config.scenario.incident_themes)
            if engine.config.scenario
            else random.choice(ECOMMERCE_DOMAINS["incidents"])
        )
        incident = Incident(
            id=f"INC-{story_idx}",
            title=incident_title,
            symptoms=f"Users are experiencing massive slowdowns. PagerDuty fired alert {alert.id}.",
            observations=f"We see a spike in {metric.name} up to {metric.value} {metric.unit}.",
            impacted_service_ids=req.affected_service_ids,
            alert_ids=[alert.id],
            created_at=engine.current_date,
            resolved_at=engine.current_date + timedelta(hours=random.randint(1, 10)),
        )
        engine.generator.incidents.append(incident)

        engine.generator.slack_messages.append(
            SlackMessage(
                client_msg_id=str(fake.uuid4()),
                text=generate_slack_message(
                    "incident_start",
                    req.owner_id,
                    ticket.key,
                    {
                        "service": req.affected_service_ids[0]
                        if req.affected_service_ids
                        else "backend"
                    },
                ),
                user="oncall-bot",
                ts=str(int((incident.created_at + timedelta(minutes=5)).timestamp())),
                channel="#incidents",
            )
        )
        engine.generator.slack_messages.append(
            SlackMessage(
                client_msg_id=str(fake.uuid4()),
                text=f"I'm looking into {incident.id}. I see {alert.id} firing. Could it be related to a recent deploy?",
                user=req.owner_id,
                ts=str(int((incident.created_at + timedelta(minutes=25)).timestamp())),
                channel="#incidents",
            )
        )

        engine.advance_time(random.randint(2, 5))
        engine.generator.postmortems.append(
            Postmortem(
                id=f"PM-{story_idx}",
                incident_id=incident.id,
                title=f"Postmortem: {incident.title}",
                content=f"On {incident.created_at}, we experienced an outage.",
                root_cause_summary=f"The root cause was a lock contention introduced in PR #{pr.number} which went out in {deployment.id}.",
                lessons_learned="Add deadlock detection to CI pipeline.",
                created_at=engine.current_date,
            )
        )
