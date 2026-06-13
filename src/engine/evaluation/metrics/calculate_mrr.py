from typing import List

# uncomment the corresponding imports below to avoid NameError:
# from .calculate_recall_at_k import CalculateRecallAtK
# from .calculate_precision_at_k import CalculatePrecisionAtK
# from .calculate_ndcg import CalculateNdcg


def calculate_mrr(retrieved_ids: List[str], expected_ids: List[str]) -> float:
    for rank, r_id in enumerate(retrieved_ids):
        if r_id in expected_ids:
            return 1.0 / (rank + 1)
    return 0.0
