from src.core.llm import AgentMessage, llmProvider
from src.engine.workflow.nodes.utils import print_phase
from src.engine.workflow.state import InvestigationState


def get_understand_node(llm: llmProvider):
    def _understand(state: InvestigationState):
        print_phase("Query Understanding")
        prompt = (
            f"Analyze the intent behind this query: '{state['query']}'.\n"
            "First, output EXACTLY ONE of the following tags on its own line: [INVESTIGATION] or [GENERAL_QA].\n"
            "- Use [INVESTIGATION] if the user is asking for the root cause of an incident, outage, or alert.\n"
            "- Use [GENERAL_QA] if the user is asking for general information, such as who owns a service, what a service does, etc.\n"
            "Then, provide a brief explanation of the query's intent."
        )
        msg = llm.generate([AgentMessage(role="system", content=prompt)])

        intent = "INVESTIGATION"
        if "[GENERAL_QA]" in msg.content:
            intent = "GENERAL_QA"

        print(f"  \033[93mIntent: {intent}\033[0m")
        print(f"  \033[90m{msg.content}\033[0m")
        return {"intent": intent, "understanding": msg.content}

    return _understand
