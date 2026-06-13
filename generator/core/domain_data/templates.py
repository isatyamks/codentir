import random

ECOMMERCE_DOMAINS = {
    "teams": [
        "Payments",
        "Cart & Checkout",
        "Catalog",
        "Search",
        "User Identity",
        "Order Fulfilment",
        "Inventory",
        "Fraud Prevention",
    ],
    "services": {
        "Payments": ["stripe-gateway", "paypal-integration", "refund-processor"],
        "Cart & Checkout": ["cart-service", "checkout-api", "tax-calculator"],
        "Catalog": ["product-catalog-service", "pricing-engine", "category-manager"],
        "Search": ["elasticsearch-indexer", "search-api", "recommendations-engine"],
        "User Identity": ["auth-service", "user-profile-api", "session-manager"],
        "Order Fulfilment": [
            "order-orchestrator",
            "shipping-calculator",
            "tracking-service",
        ],
        "Inventory": ["stock-manager", "warehouse-sync", "supplier-api"],
        "Fraud Prevention": ["fraud-detector", "risk-analyzer"],
    },
    "requirements": [
        "Implement one-click checkout",
        "Add support for Apple Pay",
        "Improve Elasticsearch query performance by 20%",
        "Build a realtime inventory sync with warehouses",
        "Create an ML model for fraud detection during checkout",
        "Add multi-currency support for European markets",
        "Implement bulk product upload API for vendors",
        "Migrate user sessions to Redis cluster",
    ],
    "bugs": [
        "Users are unable to complete checkout with Visa cards",
        "Search results are returning deleted products",
        "Inventory counts mismatch after bulk purchase",
        "High latency in pricing engine during peak hours",
        "Session token expires too early causing logouts",
        "Tax calculator returning wrong amount for California",
        "Order confirmation emails are delayed",
        "NullPointerException in refund-processor when amount is 0",
    ],
    "incidents": [
        "Checkout completely down in EU region",
        "Stripe integration failing with 500 errors",
        "Search cluster out of memory, degraded performance",
        "Database deadlock in order-orchestrator",
        "Fraud detection falsely blocking legitimate transactions",
    ],
}


def generate_commit_message(
    title: str, ticket_key: str, service_name: str, is_bug: bool
) -> str:
    type_prefix = "fix" if is_bug else "feat"
    scope = service_name.split("-")[0] if service_name else "core"
    return f"{type_prefix}({scope}): {title.lower()}\n\nResolves {ticket_key}"


def generate_jira_description(title: str, is_bug: bool, service_name: str) -> str:
    if is_bug:
        stack_traces = [
            f'Exception in thread "main" java.lang.NullPointerException\n\tat com.company.{service_name}.handlers.Process(Process.java:42)\n\tat com.company.{service_name}.Application.main(Application.java:12)',
            f"TypeError: Cannot read properties of undefined (reading 'id')\n    at mapProducts (/app/src/{service_name}/controllers/product.js:105:22)\n    at processTicksAndRejections (node:internal/process/task_queues:95:5)",
            "psycopg2.errors.DeadlockDetected: deadlock detected\nDETAIL: Process 123 waits for ShareLock on transaction 456; blocked by process 789.",
        ]
        return (
            f"h3. Description\n"
            f"We are seeing an elevated error rate in `{service_name}` related to: *{title}*.\n\n"
            f"h3. Steps to Reproduce\n"
            f"1. Navigate to the affected flow.\n"
            f"2. Trigger the endpoint.\n"
            f"3. Observe 500 Internal Server Error.\n\n"
            f"h3. Stack Trace\n"
            f"{{code}}\n{random.choice(stack_traces)}\n{{code}}\n\n"
            f"h3. Impact\n"
            f"Affecting ~{random.randint(5, 15)}% of traffic. Needs immediate triage."
        )
    else:
        return (
            f"h3. Background\n"
            f"As part of our OKRs, we need to: *{title}* within the `{service_name}` ecosystem.\n\n"
            f"h3. Acceptance Criteria\n"
            f"* [ ] API endpoints are designed and documented in Swagger.\n"
            f"* [ ] Implementation matches the attached Figma designs (if applicable).\n"
            f"* [ ] Unit test coverage is >= 80%.\n"
            f"* [ ] Load testing shows no degradation under 5k RPS.\n\n"
            f"h3. Technical Notes\n"
            f"Please ensure backward compatibility. Reach out to the Platform team if you need to modify DB schemas."
        )


def get_random_business_objective() -> str:
    objectives = [
        "This will increase our conversion rate by reducing friction.",
        "Crucial for entering the European market.",
        "Expected to reduce support tickets regarding payment failures.",
        "Aims to scale our infrastructure for the upcoming Black Friday event.",
        "Ensures compliance with new GDPR regulations.",
    ]
    return random.choice(objectives)


def generate_pr_body(ticket_key: str, title: str, is_bug: bool) -> str:
    return (
        f"### Description\n"
        f"This PR {'fixes the bug' if is_bug else 'implements the feature'}: {title}.\n\n"
        f"### Related Ticket\n"
        f"Resolves [{ticket_key}](https://jira.company.com/browse/{ticket_key})\n\n"
        f"### Checklist\n"
        f"- [x] Tests added/updated\n"
        f"- [x] Documentation updated\n"
        f"- [x] Verified locally"
    )


def generate_slack_message(
    scenario: str, author_id: str, ticket_key: str, context: dict
) -> str:
    greetings = [
        "Hey team ‍♂️",
        "Hi everyone 👋",
        "Yo 🚀",
    ]
    if scenario == "start_work":
        return f"{random.choice(greetings)}, I'm picking up <https://jira.company.com/browse/{ticket_key}|{ticket_key}> for `{context.get('service', 'backend')}`. I'll drop a PR link here soon."
    elif scenario == "pr_ready":
        return f"PR is up for {ticket_key}! 👀 Could someone please review? Link: {context.get('pr_url', 'github.com')}"
    elif scenario == "incident_start":
        return f"🚨 *INCIDENT ALERT* 🚨\nWe are seeing massive spikes in `{context.get('service', 'backend')}`. Looks related to the recent deployment of {ticket_key}. I'm jumping on a bridge now. CC <@{author_id}>"
    elif scenario == "incident_update":
        return f"Update on {context.get('incident_id')}: We've identified the root cause as a bad commit in PR #{context.get('pr_number')}. Reverting now. 🤞"
    return "Checking the logs now."
