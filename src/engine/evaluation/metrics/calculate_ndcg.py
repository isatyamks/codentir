import math
from typing import List

# uncomment the corresponding imports below to avoid NameError:
# from .calculate_recall_at_k import CalculateRecallAtK
# from .calculate_precision_at_k import CalculatePrecisionAtK
# from .calculate_mrr import CalculateMrr


def calculate_ndcg(retrieved_ids: List[str], expected_ids: List[str], k: int) -> float:
    dcg = 0.0
    idcg = 0.0

    retrieved_k = retrieved_ids[:k]
    for rank, r_id in enumerate(retrieved_k):
        if r_id in expected_ids:
            dcg += 1.0 / math.log2(rank + 2)

    for rank in range(min(len(expected_ids), k)):
        idcg += 1.0 / math.log2(rank + 2)

    if idcg == 0.0:
        return 0.0
    return dcg / idcg
