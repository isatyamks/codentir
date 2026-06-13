import random
import faker

from generator.core.domain_data import ECOMMERCE_DOMAINS
from generator.core.engine import SimulationEngine
from generator.core.models import (
    API,
    ArchitectureDecisionRecord,
    Employee,
    Repository,
    Runbook,
    Service,
    Team,
)

fake = faker.Faker()


def generate_topology(engine: SimulationEngine):
    config = engine.config
    num_employees = 20 * config.scale_factor
    num_teams = 5 * config.scale_factor
    num_services = 10 * config.scale_factor
    num_apis = 30 * config.scale_factor

    # 1. Employees
    roles = ["engineer", "qa engineer", "product manager", "architect", "team lead"]
    for i in range(num_employees):
        emp = Employee(
            id=f"emp-{i}",
            profile={
                "firstName": fake.first_name(),
                "lastName": fake.last_name(),
                "title": random.choice(roles),
                "email": fake.email(),
            },
            status="ACTIVE",
        )
        engine.generator.employees.append(emp)

    # 2. Teams
    team_names = (
        config.scenario.teams if config.scenario else ECOMMERCE_DOMAINS["teams"]
    )
    for i in range(min(num_teams, len(team_names))):
        team_name = team_names[i]
        team_members = random.sample(
            [e.id for e in engine.generator.employees],
            k=max(3, num_employees // len(team_names)),
        )
        team = Team(id=f"team-{i}", name=team_name, members=team_members)
        engine.generator.teams.append(team)

    # 3. Services, Repositories, ADRs, Runbooks
    s_idx = 0
    services_to_distribute = list(config.scenario.services) if config.scenario else None

    for team in engine.generator.teams:
        if config.scenario:
            num_srv = max(1, len(services_to_distribute) // len(engine.generator.teams))
            svc_names = [
                services_to_distribute.pop()
                for _ in range(min(num_srv, len(services_to_distribute)))
            ]
        else:
            svc_names = ECOMMERCE_DOMAINS["services"].get(
                team.name, [f"{team.name.lower()}-service"]
            )

        for srv_name in svc_names:
            srv = Service(
                id=f"srv-{s_idx}",
                name=srv_name,
                team_id=team.id,
                description=f"Core microservice for {srv_name.replace('-', ' ')}",
                depends_on_ids=[f"srv-{s_idx + 1}"] if s_idx < num_services - 1 else [],
            )
            engine.generator.services.append(srv)

            repo = Repository(
                id=f"repo-{s_idx}",
                name=f"{srv_name}-repo",
                service_id=srv.id,
                url=f"https://github.com/company/{srv_name}-repo",
            )
            engine.generator.repositories.append(repo)

            adr = ArchitectureDecisionRecord(
                id=f"adr-{s_idx}",
                title=f"Initial Architecture for {srv_name}",
                service_id=srv.id,
                status="accepted",
                body={
                    "storage": {
                        "value": f"<p>Decision: Use Golang and gRPC for {srv_name}. Reason: Performance requirements.</p>",
                        "representation": "storage",
                    }
                },
                created_at=engine.current_date,
            )
            engine.generator.adrs.append(adr)

            runbook = Runbook(
                id=f"runbook-{s_idx}",
                title=f"Incident Response for {srv_name}",
                service_id=srv.id,
                content=f"If {srv_name} goes down, check the database connection limits and restart the pods.",
                created_at=engine.current_date,
            )
            engine.generator.runbooks.append(runbook)

            s_idx += 1

    # 4. APIs
    methods = ["GET", "POST", "PUT", "DELETE"]
    for i in range(num_apis):
        srv = random.choice(engine.generator.services)
        resource = fake.word()
        api = API(
            id=f"api-{i}",
            name=f"{resource}-api",
            service_id=srv.id,
            method=random.choice(methods),
            path=f"/api/v1/{srv.name.replace('-service', '')}/{resource}",
            description=f"API for {resource}",
        )
        engine.generator.apis.append(api)
