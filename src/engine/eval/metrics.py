"""
Evaluation metrics — flattened from engine/evaluation/metrics/*.py.
"""


def calculate_precision_at_k(retrieved: list, relevant: set, k: int) -> float:
    top_k = retrieved[:k]
    hits = sum(1 for doc in top_k if doc in relevant)
    return hits / k if k > 0 else 0.0


def calculate_recall_at_k(retrieved: list, relevant: set, k: int) -> float:
    top_k = retrieved[:k]
    hits = sum(1 for doc in top_k if doc in relevant)
    return hits / len(relevant) if relevant else 0.0


def calculate_mrr(retrieved: list, relevant: set) -> float:
    for rank, doc in enumerate(retrieved, start=1):
        if doc in relevant:
            return 1.0 / rank
    return 0.0


def calculate_ndcg(retrieved: list, relevant: set, k: int) -> float:
    import math

    def dcg(results, k):
        return sum(
            (1.0 / math.log2(i + 2)) for i, doc in enumerate(results[:k]) if doc in relevant
        )

    ideal = sorted(
        [1 if doc in relevant else 0 for doc in retrieved],
        reverse=True,
    )
    ideal_dcg = sum(
        (1.0 / math.log2(i + 2)) for i, rel in enumerate(ideal[:k]) if rel
    )
    return dcg(retrieved, k) / ideal_dcg if ideal_dcg > 0 else 0.0
