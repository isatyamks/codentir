import argparse
import random
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=False)

from generator.core.config.config import SimulationConfig
from generator.core.engine.engine import SimulationEngine
from generator.exporters.benchmark import generate_evaluation_benchmark
from generator.core.scenario import ScenarioPlanner
from generator.generators.topology import generate_topology
from generator.generators.identity import generate_identities
from generator.generators.knowledge import generate_knowledge_base
from generator.generators.workflows import generate_workflows
from generator.exporters.file import export_to_files
from generator.exporters.graph import export_to_graph


def setup_random_seed(seed: int):
    random.seed(seed)


def main():
    parser = argparse.ArgumentParser(
        description="codentir LLM-Driven Scenario Generator"
    )
    parser.add_argument(
        "--company", type=str, required=True, help="Company name (e.g. Zomato, Netflix)"
    )
    parser.add_argument(
        "--size",
        type=str,
        choices=["small", "medium", "large"],
        default="small",
        help="generator size",
    )
    parser.add_argument(
        "--output-dir", type=str, default=".", help="Output directory root"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    args = parser.parse_args()

    setup_random_seed(args.seed)

    print(f"\n==================================================")
    print(f"1. AI SCENARIO DESIGN: Dreaming up '{args.company}'")
    print(f"==================================================")

    planner = ScenarioPlanner()
    profile = planner.generate_profile(args.company, args.size)

    print(f"  Tenant ID: {profile.tenant_id}")
    print(f"  Domain: {profile.domain}")
    print(f"  Teams: {len(profile.teams)}")
    print(f"  Services: {len(profile.services)}")

    print(f"\n==================================================")
    print(f"2. SYNTHETIC DATA GENERATION")
    print(f"==================================================")

    config = SimulationConfig(
        seed=args.seed,
        size=args.size,
        start_date=datetime(2022, 1, 1),
        end_date=datetime(2024, 1, 1),
        scenario=profile,
    )

    engine = SimulationEngine(config)

    print(f"  -> Generating topology using {args.company}'s services...")
    generate_topology(engine)

    print(f"  -> Simulating Workday/Okta Identities...")
    generate_identities(engine)

    print(f"  -> Simulating Confluence Knowledge Base...")
    generate_knowledge_base(engine)

    print(f"  -> Simulating engineering workflows & incidents...")
    generate_workflows(engine)

    print(f"  -> Exporting JSON records for tenant: {profile.tenant_id}...")
    export_to_files(engine.generator, args.output_dir, profile.tenant_id)
    export_to_graph(engine.generator, args.output_dir, profile.tenant_id)
    real_queries = generate_evaluation_benchmark(
        engine.generator, args.output_dir, profile.tenant_id
    )

    print(
        f"\n\033[92m[DONE]\033[0m Hyper-realistic generator for '{args.company}' created successfully!"
    )
    print(f"Verified Test Queries based on ACTUAL generated data:")
    for q in real_queries:
        print(f"  - '{q['query']}'")

    if real_queries:
        print("\nRun this command to test your agent on this new tenant:")
        print(
            f'  python -m src.codentir.cmd.cli --data-dir data --tenant-id {profile.tenant_id} --query "{real_queries[0]["query"]}" --agent\n'
        )


if __name__ == "__main__":
    main()
