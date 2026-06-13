import argparse
import json

from src.core.benchmark import BenchmarkQuery, BenchmarkSuite
from src.infra.impls import FileSystemDatasetReader


def generate_gold_dataset(data_dir: str, output_path: str):
    print("Loading dataset to generate Gold Benchmark...")
    reader = FileSystemDatasetReader()
    dataset = reader.load(data_dir)

    queries = []

    # Generate Root Cause Analysis Queries from incidents
    for i, (i_id, inc) in enumerate(dataset.incidents.items()):
        if getattr(inc, "related_ticket_id", None) and getattr(inc, "related_commit_id", None):
            queries.append(
                BenchmarkQuery(
                    query_id=f"Q-RCA-{i}",
                    query_text=f"Why is {inc.title} happening? Provide the root cause and related fix.",
                    category="Root Cause Analysis",
                    expected_documents=[
                        i_id,
                        inc.related_ticket_id,
                        inc.related_commit_id,
                    ],
                )
            )

    # Generate Impact Analysis Queries from tickets
    for i, (t_id, ticket) in enumerate(dataset.tickets.items()):
        if len(queries) >= 500:
            break
        if ticket.service_ids:
            queries.append(
                BenchmarkQuery(
                    query_id=f"Q-IMP-{i}",
                    query_text=f"What services are impacted by the bug described in {ticket.summary}?",
                    category="Impact Analysis",
                    expected_documents=[t_id] + ticket.service_ids,
                )
            )

    # Generate Dependency Queries from requirements
    for i, (r_id, req) in enumerate(dataset.requirements.items()):
        if len(queries) >= 500:
            break
        if req.affected_service_ids:
            queries.append(
                BenchmarkQuery(
                    query_id=f"Q-DEP-{i}",
                    query_text=f"Find the implementation details for {req.title}",
                    category="Requirement Traceability",
                    expected_documents=[r_id] + req.affected_service_ids,
                )
            )

    suite = BenchmarkSuite(
        name="Enterprise RCA Benchmark 500",
        description="Gold dataset to prove Hybrid Retrieval accuracy",
        queries=queries,
    )

    with open(output_path, "w") as f:
        json.dump(suite.model_dump(), f, indent=2)

    print(f"Generated {len(queries)} gold queries at {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--output", default="eval_dataset.json")
    args = parser.parse_args()
    generate_gold_dataset(args.data_dir, args.output)
