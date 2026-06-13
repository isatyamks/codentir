import random
import uuid

from generator.core.engine import SimulationEngine
from generator.core.models import Employee


def generate_identities(engine: SimulationEngine):
    """
    Simulates Okta/Workday employee syncing by generating rich profile JSONs.
    """
    for team in engine.generator.teams:
        for i in range(random.randint(3, 8)):
            emp_id = str(uuid.uuid4())

            first_name = random.choice(
                ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]
            )
            last_name = random.choice(["Smith", "Jones", "Taylor", "Brown", "Williams"])
            email = f"{first_name.lower()}.{last_name.lower()}@{engine.config.scenario.domain}"

            emp = Employee(
                id=emp_id,
                status="ACTIVE",
                profile={
                    "firstName": first_name,
                    "lastName": last_name,
                    "email": email,
                    "title": random.choice(
                        ["Software Engineer", "Senior Engineer", "Staff Engineer"]
                    ),
                    "department": team.name,
                },
            )

            team.members.append(emp_id)
            engine.generator.employees.append(emp)
