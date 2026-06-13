import argparse
import json
import time

from src.core.benchmark import BenchmarkResult, BenchmarkSuite
from src.engine.eval.metrics import calculate_mrr, calculate_ndcg, calculate_recall_at_k
from src.infra.impls import CrossEncoderReranker, FileSystemDatasetReader
from src.infra.retriever import BM25Retriever, DenseRetriever, HybridRetriever


def print_dashboard(results: list):
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    if not results:
        print("No results.")
        return

    avg_recall = sum(r.recall_at_k for r in results) / len(results)
    avg_mrr = sum(r.mrr for r in results) / len(results)
    avg_ndcg = sum(r.ndcg for r in results) / len(results)
    avg_latency = sum(r.latency_ms for r in results) / len(results)

    print(f"Queries:        {len(results)}")
    print(f"Avg Recall@10:  {avg_recall:.4f}")
    print(f"Avg MRR:        {avg_mrr:.4f}")
    print(f"Avg NDCG@10:    {avg_ndcg:.4f}")
    print(f"Avg Latency:    {avg_latency:.1f} ms")
    print("=" * 60)


def run_benchmark(suite: BenchmarkSuite, retriever, top_k: int = 10) -> list:
    results = []
    for query in suite.queries:
        start = time.time()
        retrieved = retriever.search(query.query_text, "tenant_default", top_k=top_k)
        latency = (time.time() - start) * 1000

        retrieved_ids = [r.artifact_id for r in retrieved]
        relevant = set(query.expected_documents)

        results.append(
            BenchmarkResult(
                query_id=query.query_id,
                recall_at_k=calculate_recall_at_k(retrieved_ids, relevant, top_k),
                mrr=calculate_mrr(retrieved_ids, relevant),
                ndcg=calculate_ndcg(retrieved_ids, relevant, top_k),
                latency_ms=latency,
            )
        )
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--benchmark", default="eval_dataset.json")
    args = parser.parse_args()

    print("1. Loading Evaluation Dataset...")
    with open(args.benchmark, "r") as f:
        raw_data = json.load(f)
        suite = BenchmarkSuite(**raw_data)

    print("2. Loading Enterprise Graph...")
    dataset = FileSystemDatasetReader().load(args.data_dir)

    print("3. Initializing Search Infrastructure...")
    bm25 = BM25Retriever()
    dense = DenseRetriever()
    reranker = CrossEncoderReranker()
    retriever = HybridRetriever(bm25, dense, reranker)

    print("4. Indexing Database...")
    retriever.index(dataset)

    print(f"5. Running Benchmark Suite ({len(suite.queries)} queries)...")
    results = run_benchmark(suite, retriever, top_k=10)

    print_dashboard(results)


if __name__ == "__main__":
    main()
