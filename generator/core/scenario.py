import json

from generator.core.config.profile import ScenarioProfile
from generator.core.groq_provider import GroqProvider


class ScenarioPlanner:
    def __init__(self):
        self.llm = GroqProvider()

    def generate_profile(self, company_name: str, size: str) -> ScenarioProfile:
        num_services = 5 if size == "small" else (15 if size == "medium" else 40)
        num_teams = 2 if size == "small" else (5 if size == "medium" else 15)
        num_incidents = 3 if size == "small" else (8 if size == "medium" else 20)

        prompt = f"""
You are an expert enterprise systems architect and site reliability engineer.
The user wants to generate a hyper-realistic synthetic software engineering generator for a company named '{company_name}'.
The scale of this generator is '{size}'.

Generate a realistic topology and incident scenarios for this specific company.
For example, if the company is an AI startup, the services should be 'gpu-scheduler', 'inference-engine', etc. If it's a food delivery app, they should be 'rider-matching', 'checkout', etc.

Return the response EXACTLY as a raw JSON object with no markdown formatting and no other text.
The JSON must strictly follow this schema:
{{
    "tenant_id": "A lowercase, snake_case version of the company name",
    "domain": "A brief description of what the company does",
    "services": ["service-1", "service-2", ... (exactly {num_services} items)],
    "teams": ["Team A", "Team B", ... (exactly {num_teams} items)],
    "requirements": ["Feature requirement 1", "Feature requirement 2", ... (exactly {num_incidents} items)],
    "bugs": ["Bug title 1", "Bug title 2", ... (exactly {num_incidents} items)],
    "incident_themes": ["Incident theme 1", "Incident theme 2", ... (exactly {num_incidents} items)],
    "eval_queries": ["Question 1", "Question 2", ... (generate 5 realistic search queries a developer might ask about these incidents)]
}}
"""
        from generator.core.contracts import AgentMessage

        message = AgentMessage(role="user", content=prompt)
        response_msg = self.llm.generate([message])

        clean_json = response_msg.content.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]

        import re
        import json_repair

        data = json_repair.loads(clean_json)
        profile = ScenarioProfile(**data)
        # Always derive tenant_id deterministically — never trust the LLM for this.
        profile.tenant_id = re.sub(r"[^a-z0-9]+", "_", company_name.lower()).strip("_")
        return profile
