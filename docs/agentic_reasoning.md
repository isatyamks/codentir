# The Agentic Reasoning Loop

Codentir does not rely on simple vector-search heuristics. It runs a powerful, 11-stage autonomous loop using LangGraph. Here is exactly what happens during an investigation:

## Phase 1: Ingestion & Triage
1. **LLM Intent Parsing**: Evaluates if the query is a simple question or an active incident requiring full investigation.
2. **Context Aggregation**: Collects preliminary data surrounding the reported issue.

## Phase 2: Multi-Modal Retrieval
3. **Sparse Search (BM25)**: Fetches exact matches for trace IDs, error codes, and specific commit hashes.
4. **Dense Vector Search**: Captures the semantic intent behind error messages.
5. **Cross-Encoder Attention**: Reranks the combined results to ensure the most critical context is at the absolute top.

## Phase 3: Causal Graph Inference
6. **Evidence Traversal**: Walks the NetworkX graph to link deployments, tickets, and alerts.
7. **Path Ranking**: Statistically scores how likely a specific path caused the incident.
8. **Candidate Isolation**: Identifies the single most likely failure point (e.g., a specific Pull Request).

## Phase 4: Agentic Resolution
9. **Sub-Agent Swarm**: Dispatches specialized agents to look at diffs, release windows, and code owners.
10. **Hypothesis Draft**: Synthesizes all data into a concrete engineering theory.
11. **Blast Radius Mapping**: Predicts downstream impact.
12. **Automated Remediation**: Generates revert commands or mitigation scripts.

### The Human-in-the-Loop Gateway
If confidence ever drops below 90%, the agent safely suspends, asks a human domain expert for review, and uses their feedback to course-correct.
