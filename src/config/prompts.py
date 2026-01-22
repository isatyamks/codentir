from typing import Dict, Any


SYSTEM_PROMPT = """You are an expert software testing assistant specialized in generating comprehensive test cases and use cases.

Your task is to generate structured, detailed test cases and use cases based ONLY on the provided context.

CRITICAL RULES:
1. You MUST base your response ONLY on the retrieved context provided below
2. DO NOT invent, assume, or hallucinate any features, functionality, or requirements not explicitly mentioned in the context
3. If the context is insufficient, you MUST ask clarifying questions or state what information is missing
4. Always ground your output in specific evidence from the context
5. Output MUST be valid JSON following the specified schema
6. RESPOND WITH ONLY THE JSON OBJECT - NO explanatory text before or after
7. Do NOT include markdown code blocks, just pure JSON

Context will be provided to you, and you must use it as the sole source of truth.
"""


RETRIEVAL_CONTEXT_TEMPLATE = """<context>
Retrieved Evidence (Relevance Score: {avg_score:.2f}):

{context_chunks}
</context>

If the above context does not contain sufficient information to answer the query, you MUST:
1. Ask specific clarifying questions, OR
2. Explicitly state what assumptions you're making and what information is missing
"""


USE_CASE_GENERATION_PROMPT = """Based on the provided context, generate a comprehensive use case for: "{query}"

You MUST generate a JSON response with the following structure:

{{
  "query": "the original query",
  "use_case": {{
    "title": "concise use case title",
    "description": "detailed description of the use case",
    "preconditions": ["list of preconditions required"],
    "steps": ["step-by-step actions in sequential order"],
    "expected_result": "what should happen when executed successfully",
    "negative_cases": ["scenarios that should fail or be handled"],
    "boundary_cases": ["edge cases and limits to test"]
  }},
  "grounding_evidence": [
    {{
      "source": "document name and section",
      "content": "relevant excerpt from context",
      "relevance_score": 0.0
    }}
  ],
  "assumptions": ["any assumptions made due to insufficient context"],
  "clarifying_questions": ["questions if more info is needed"],
  "confidence": 0.0
}}

IMPORTANT:
- Every field in the use_case object must be filled based on the context
- grounding_evidence MUST reference specific parts of the provided context
- If context is insufficient, populate clarifying_questions with specific questions
- confidence should reflect how well the context supports your response (0.0 to 1.0)
"""


TEST_CASE_GENERATION_PROMPT = """Based on the provided context, generate comprehensive test cases for: "{query}"

You MUST generate a JSON response with the following structure:

{{
  "query": "the original query",
  "test_cases": [
    {{
      "test_id": "unique identifier (e.g., TC001)",
      "type": "positive|negative|boundary",
      "title": "brief test case title",
      "preconditions": ["setup required before test"],
      "steps": ["detailed test steps"],
      "test_data": {{}},
      "expected_result": "expected outcome",
      "priority": "high|medium|low",
      "category": "test category (e.g., functional, security)"
    }}
  ],
  "grounding_evidence": [
    {{
      "source": "document name and section",
      "content": "relevant excerpt from context",
      "relevance_score": 0.0
    }}
  ],
  "assumptions": ["any assumptions made"],
  "clarifying_questions": ["questions if more info needed"],
  "confidence": 0.0
}}

Generate at minimum:
- 3 positive test cases (happy path scenarios)
- 2 negative test cases (error/failure scenarios)
- 2 boundary test cases (edge cases and limits)

IMPORTANT:
- All test cases MUST be grounded in the provided context
- DO NOT create test cases for features not mentioned in the context
- Reference specific evidence for each test case type
"""


COMBINED_GENERATION_PROMPT = """Based on the provided context, generate both use cases AND test cases for: "{query}"

You MUST generate a JSON response with the following structure:

{{
  "query": "the original query",
  "use_case": {{
    "title": "concise use case title",
    "description": "detailed description",
    "preconditions": ["list of preconditions"],
    "steps": ["sequential steps"],
    "expected_result": "successful outcome",
    "negative_cases": ["failure scenarios"],
    "boundary_cases": ["edge cases"]
  }},
  "test_cases": [
    {{
      "test_id": "TC001",
      "type": "positive|negative|boundary",
      "title": "test case title",
      "preconditions": ["setup required"],
      "steps": ["test steps"],
      "test_data": {{}},
      "expected_result": "expected outcome",
      "priority": "high|medium|low",
      "category": "category"
    }}
  ],
  "grounding_evidence": [
    {{
      "source": "document name and section",
      "content": "relevant excerpt",
      "relevance_score": 0.0
    }}
  ],
  "assumptions": ["assumptions if context insufficient"],
  "clarifying_questions": ["specific questions if needed"],
  "confidence": 0.0
}}

The use case should describe the overall feature/functionality.
The test cases should validate the use case with specific test scenarios.

CRITICAL: Everything MUST be grounded in the provided context. Do not invent features.
"""


INSUFFICIENT_CONTEXT_PROMPT = """The retrieved context does not contain sufficient information to answer: "{query}"

Please generate a JSON response with clarifying questions:

{{
  "query": "the original query",
  "status": "insufficient_context",
  "retrieved_context_summary": "brief summary of what was found",
  "missing_information": ["specific information that is missing"],
  "clarifying_questions": ["specific questions to ask the user"],
  "suggestions": ["suggestions for what documents/info might help"],
  "confidence": 0.0
}}

Be specific about what information is needed to proceed.
"""

CONTEXTUALIZE_QUERY_PROMPT = """Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is.

Chat History:
{chat_history}

Latest Question: {question}

Standalone Question:"""

def get_generation_prompt(
    query: str,
    mode: str = "both",
    context_chunks: str = "",
    avg_score: float = 0.0
) -> str:
    context_section = RETRIEVAL_CONTEXT_TEMPLATE.format(
        context_chunks=context_chunks,
        avg_score=avg_score
    )
    
    if mode == "use_case":
        task_prompt = USE_CASE_GENERATION_PROMPT.format(query=query)
    elif mode == "test_case":
        task_prompt = TEST_CASE_GENERATION_PROMPT.format(query=query)
    elif mode == "insufficient":
        return SYSTEM_PROMPT + "\n\n" + INSUFFICIENT_CONTEXT_PROMPT.format(query=query)
    else:
        task_prompt = COMBINED_GENERATION_PROMPT.format(query=query)
    
    return SYSTEM_PROMPT + "\n\n" + context_section + "\n\n" + task_prompt


HALLUCINATION_CHECK_PROMPT = """You are a fact-checker. Your task is to verify if the generated output is grounded in the provided context.

Context:
{context}

Generated Output:
{output}

Analyze if the output contains information NOT present in the context.

Respond with JSON:
{{
  "is_grounded": true/false,
  "hallucinated_elements": ["list any invented information"],
  "grounding_score": 0.0,
  "explanation": "brief explanation"
}}
"""


PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "disregard the context",
    "disregard your",
    "disregard all",
    "forget everything",
    "forget what",
    "you are now",
    "act as",
    "pretend to be",
    "new instructions:",
    "system:",
    "override",
    "jailbreak",
    "reveal all",
    "show me all",
    "list all",
    "[system]",
    "[/system]",
    "ignore the above",
    "instead of",
]
