# The Causal Knowledge Graph

Codentir maps your entire engineering reality into a directional `NetworkX` Knowledge Graph. 

By default, engineering systems are highly fragmented. A Jira ticket is not natively linked to a specific PagerDuty alert, which is not natively linked to a specific Git commit hash. Codentir solves this.

## How it works

1. **Ingestion & Validation**: Raw events stream in from Git, Jira, Slack, and Datadog. An ironclad Validation Orchestrator drops orphaned or malformed data to prevent the LLM from hallucinating on garbage inputs.
2. **Node Creation**: Validated entities become nodes in the graph (e.g., Node A = Commit Hash, Node B = PagerDuty Alert).
3. **Causal Edges**: The system draws directional edges connecting these nodes based on temporal data and parsed relationships. 

When an incident occurs, the LangGraph agent traverses these edges. Instead of guessing, it literally walks the path from the broken service -> back to the specific deployment -> back to the specific PR -> back to the author, calculating the mathematical probability of causality at each step.
