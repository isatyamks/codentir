from src.core.llm import AgentMessage, llmProvider
from src.data.graph import GraphService
from src.engine.workflow.nodes.utils import print_phase
from src.engine.workflow.state import InvestigationState


def get_qa_node(llm: llmProvider, graph_svc: GraphService):
    def _qa_generation(state: InvestigationState):
        print_phase("General QA Generation")

        context_parts = []
        for a_id in state["expanded_artifacts"]:
            node_data = graph_svc.get_node(a_id)
            if node_data:
                obj = node_data.get("obj")
                if obj and hasattr(obj, "model_dump"):
                    context_parts.append(str(obj.model_dump()))
                else:
                    context_parts.append(str(node_data))

        context_str = "\n---\n".join(context_parts[:20])

        prompt = (
            f"You are codentir, an AI assistant answering a general knowledge question based on the provided graph context.\n"
            f"Question: {state['query']}\n\n"
            f"Graph Context:\n{context_str}\n\n"
            "Provide a direct, concise answer. Do not apologize or mention the context."
        )

        msg = llm.generate([AgentMessage(role="system", content=prompt)])
        print(f"  \033[92m{msg.content}\033[0m")

        report = f"Issue: {state['query']}\n\nAnswer:\n{msg.content}"
        return {
            "technical_explanation": msg.content,
            "report": report,
            "final_response": report,
        }

    return _qa_generation
