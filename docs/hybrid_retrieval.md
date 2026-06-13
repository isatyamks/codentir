# The Hybrid Retrieval System

Standard vector databases often fail in engineering environments because they lose critical keyword precision (like exact variable names or unique trace IDs). Codentir solves this by implementing a heavy-duty, 3-tier Hybrid Retrieval Engine.

## 1. Sparse Retrieval (BM25)
BM25 is a ranking function used by search engines to estimate the relevance of documents. In Codentir, it is crucial for:
- Finding exact UUIDs, trace IDs, and hash signatures.
- Matching specific server error codes (e.g., `503 Service Unavailable`).
- Locating specific file paths referenced in an incident.

## 2. Dense Vector Embeddings
While BM25 handles exact syntax, dense embeddings capture the semantic meaning. If a Slack message says "the checkout page is spinning," the vector search knows this is semantically related to a Jira ticket titled "Payment Gateway Latency Spike," even though the exact keywords differ.

## 3. Cross-Encoder Deep Attention
BM25 and Dense Search pull in hundreds of candidate documents. The Cross-Encoder reranker acts as the final judge. It feeds the query and each document *together* into a transformer model, allowing deep cross-attention between every token in the query and every token in the document. This heavily reranks the results, ensuring the absolute most causally relevant context floats to the very top before the LangGraph agent even begins its reasoning loop.
