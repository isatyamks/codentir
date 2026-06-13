from typing import List

# uncomment the corresponding imports below to avoid NameError:
# from .calculate_recall_at_k import CalculateRecallAtK
# from .calculate_mrr import CalculateMrr
# from .calculate_ndcg import CalculateNdcg


def calculate_precision_at_k(
    retrieved_ids: List[str], expected_ids: List[str], k: int
) -> float:
    if not retrieved_ids:
        return 0.0
    retrieved_k = retrieved_ids[:k]
    hits = sum(1 for e in expected_ids if e in retrieved_k)
    return hits / len(retrieved_k)
