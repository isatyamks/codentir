from src.core.llm import llmProvider
from src.data.graph import GraphService
from src.data.retrieval import RetrievalService
from src.engine.analysis.impact import ImpactService
from src.engine.causal.extractor import CauseCandidateExtractor
from src.engine.causal.builder import EvidenceChainBuilder
from src.engine.causal.generator import HypothesisGenerator
from src.engine.causal.ranker import PathRanker
from src.engine.change.ranker import ChangeRanker
from src.engine.change.owners import CodeOwnerService
from src.engine.change.commits import CommitAnalyzer
from src.engine.change.deployments import DeploymentAnalyzer
from src.engine.change.diffs import DiffAnalyzer
from src.engine.change.releases import ReleaseAnalyzer
from src.engine.workflow.builder import build_workflow


class InvestigationWorkflowEngine:
    def __init__(
        self,
        llm: llmProvider,
        retrieval_svc: RetrievalService,
        graph_svc: GraphService,
        impact_svc: ImpactService,
    ):
        self.llm = llm
        self.retrieval_svc = retrieval_svc
        self.graph_svc = graph_svc
        self.impact_svc = impact_svc
        self.ev_chain = EvidenceChainBuilder(graph_svc)
        self.path_ranker = PathRanker(graph_svc)
        self.candidate_extractor = CauseCandidateExtractor(graph_svc)
        self.hyp_gen = HypothesisGenerator(llm)
        self.change_ranker = ChangeRanker()
        self.deploy_analyzer = DeploymentAnalyzer(graph_svc)
        self.release_analyzer = ReleaseAnalyzer(graph_svc)
        self.commit_analyzer = CommitAnalyzer(graph_svc)
        self.diff_analyzer = DiffAnalyzer(graph_svc)
        self.code_owner_svc = CodeOwnerService(graph_svc)
        self.graph = build_workflow(self)

    def run(self, query: str, tenant_id: str = "tenant_default") -> str:
        print(
            f"\n\033[1mStarting Investigation Engine for tenant '{tenant_id}' on query:\033[0m '{query}'\n"
        )
        st = {
            "query": query,
            "tenant_id": tenant_id,
            "intent": "",
            "understanding": "",
            "initial_artifacts": [],
            "expanded_artifacts": [],
            "evidence_paths": [],
            "cause_candidates": [],
            "scored_candidates": [],
            "diff_data": {},
            "owners": {},
            "associated_changes": {},
            "technical_explanation": "",
            "blast_radius": {},
            "action_items": [],
            "human_feedback": [],
            "report": "",
            "final_response": "",
            "loop_count": 0,
            "expert_consulted": False,
            "consulted_targets": [],
            "next_action": "",
        }
        return self.graph.invoke(st)["final_response"]
