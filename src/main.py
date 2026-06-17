import argparse
import time
from pathlib import Path
from dotenv import load_dotenv

from src.infra.retriever import BM25Retriever, DenseRetriever, HybridRetriever
from src.infra.impls import CrossEncoderReranker, FileSystemDatasetReader, NetworkXExporter
from src.infra.groq import GroqProvider
from src.infra.telemetry import setup_telemetry

from src.data.graph import GraphService
from src.data.retrieval import RetrievalService
from src.engine.analysis.impact import ImpactService
from src.engine.workflow.engine import InvestigationWorkflowEngine
from src.core.validation import ValidationOrchestrator


def main():
    parser = argparse.ArgumentParser(description="codentir Investigation Engine Runner")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Path to the generated data directory",
    )
    parser.add_argument(
        "--query",
        type=str,
        default="payment failing stripe",
        help="Test query for the retrieval engine",
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        default="tenant_default",
        help="Tenant ID for multi-tenant isolation",
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Run the query through the Agentic ReAct loop",
    )
    args = parser.parse_args()

    data_path = Path(args.data_dir)
    if not data_path.exists():
        print(f"Error: Data directory '{args.data_dir}' not found.")
        return

    print("=" * 50)
    print("1. DATA INGESTION")
    print("=" * 50)
    reader = FileSystemDatasetReader()
    start = time.time()
    dataset = reader.load(str(data_path))
    print(f"Loaded dataset in {time.time() - start:.2f} seconds.")
    print(f"  - Tickets: {len(dataset.tickets)}")
    print(f"  - Commits: {len(dataset.commits)}")
    print(f"  - Incidents: {len(dataset.incidents)}")
    print(f"  - Slack Messages: {len(dataset.slack_messages)}")

    print("\n" + "=" * 50)
    print("2. VALIDATION PIPELINE")
    print("=" * 50)
    validator = ValidationOrchestrator(dataset)
    report = validator.run_all_validations()
    print(f"Total Entities Checked: {report.total_entities_checked}")
    if report.is_valid:
        print("Status: \033[92mPASSED\033[0m")
    else:
        print("Status: \033[91mFAILED\033[0m")
        print(f"Found {len(report.issues)} issues:")
        for issue in report.issues[:5]:
            print(
                f"  - [{issue.issue_type.upper()}] {issue.entity_type} {issue.entity_id}: {issue.description}"
            )
        if len(report.issues) > 5:
            print(f"  ... and {len(report.issues) - 5} more issues.")

    print("\n" + "=" * 50)
    print("3. RETRIEVAL ENGINE (HYBRID + RERANK)")
    print("=" * 50)
    print("Initializing Dense, Sparse, and Cross-Encoder models...")
    bm25 = BM25Retriever()
    dense = DenseRetriever()
    reranker = CrossEncoderReranker()
    retriever = HybridRetriever(bm25, dense, reranker)

    print("Indexing documents into Hybrid Engine...")
    start = time.time()
    retriever.index(dataset)
    print(f"Indexed in {time.time() - start:.2f} seconds.\n")

    print(f"Running search for tenant '{args.tenant_id}' on query: '{args.query}'\n")
    results = retriever.search(args.query, args.tenant_id, top_k=3)
    for i, r in enumerate(results):
        print(
            f"[Rank {i + 1}] Score: {r.score:.2f} | ID: {r.artifact_id} ({r.artifact_type})"
        )
        print(f"         {r.content[:100].replace(chr(10), ' ')}...")

    print("\n" + "=" * 50)
    print("4. GRAPH EXPORT")
    print("=" * 50)
    exporter = NetworkXExporter()
    out_dir = Path("graph")
    exporter.export(dataset, str(out_dir), args.tenant_id)
    print(f"Successfully exported NetworkX graph to {out_dir}/{args.tenant_id}.graphml")

    if args.agent:
        print("\n" + "=" * 50)
        print("5. AGENT REASONING (ENTERPRISE RAG)")
        print("=" * 50)

        setup_telemetry()

        load_dotenv()
        try:
            llm = GroqProvider()
        except ValueError as e:
            print(f"\n\033[91mError initializing Groq: {e}\033[0m")
            print(
                "Please add your GROQ_API_KEY to the .env file to run the Enterprise Agent."
            )
            return

        retrieval_svc = RetrievalService(retriever)
        graph_svc = GraphService(dataset)
        impact_svc = ImpactService(graph_svc)

        engine = InvestigationWorkflowEngine(
            llm=llm,
            retrieval_svc=retrieval_svc,
            graph_svc=graph_svc,
            impact_svc=impact_svc,
        )

        final_answer = engine.run(args.query, args.tenant_id)

        print("\n" + "=" * 50)
        print(f"\033[1m[FINAL OUTPUT]:\033[0m \033[96m{final_answer}\033[0m")
        print("=" * 50)


if __name__ == "__main__":
    main()
