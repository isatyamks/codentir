from datetime import timedelta
import random
import uuid

from generator.core.engine import SimulationEngine
from generator.core.models import ArchitectureDecisionRecord


def generate_knowledge_base(engine: SimulationEngine):
    """
    Simulates Confluence/Notion pages by generating Architecture Decision Records
    and design docs mapped to services.
    """
    for service in engine.generator.services:
        if random.random() > 0.3:  # 70% of services have an ADR
            adr_id = str(uuid.uuid4())
            title = f"Architecture Decision: {service.name} database choice"
            html_body = f"""
            <h1>{title}</h1>
            <h2>Context</h2>
            <p>The {service.name} needs a highly available datastore.</p>
            <h2>Decision</h2>
            <p>We chose PostgreSQL for ACID compliance.</p>
            """
            adr = ArchitectureDecisionRecord(
                id=adr_id,
                title=title,
                service_id=service.id,
                status="Approved",
                body={"storage": {"value": html_body, "representation": "storage"}},
                created_at=engine.current_date
                - timedelta(days=random.randint(10, 100)),
            )
            engine.generator.adrs.append(adr)
