from typing import Dict, Any, Optional, Callable
from src.generation.llm_client import LLMClient
from src.generation.use_case_generator import UseCaseGenerator
from src.generation.test_case_generator import TestCaseGenerator
from src.generation.output_formatter import OutputFormatter
from src.retrieval import Retriever
from src.guards import GuardOrchestrator
from src.config import get_generation_prompt, SYSTEM_PROMPT, CONTEXTUALIZE_QUERY_PROMPT
from src.utils import timer, metrics_collector
from src.utils.session_manager import SessionManager


class Generator:
    def __init__(self):
        self.llm_client = LLMClient()
        self.use_case_generator = UseCaseGenerator(self.llm_client)
        self.test_case_generator = TestCaseGenerator(self.llm_client)
        self.formatter = OutputFormatter()
        self.retriever = Retriever()
        self.guards = GuardOrchestrator()
        self.session_manager = SessionManager()

    def _contextualize_query(self, query: str, session_id: str) -> str:
        if not session_id:
            return query
        history = self.session_manager.format_history_for_llm(session_id)
        if not history:
            return query
        try:
            prompt = CONTEXTUALIZE_QUERY_PROMPT.format(chat_history=history, question=query)
            response = self.llm_client.generate(prompt=prompt, temperature=0.3, max_tokens=200)
            rewritten_query = response["content"].strip()
            return rewritten_query if rewritten_query != query else query
        except Exception:
            return query

    def _run_pipeline(
        self,
        query: str,
        top_k: int,
        search_mode: str,
        session_id: str,
        generation_func: Callable[[str, list, float], Dict[str, Any]],
        metric_name: str,
        summary_func: Callable[[Dict[str, Any]], str],
        timer_name: str
    ) -> Dict[str, Any]:
        try:
            with timer(timer_name):
                processing_query = self._contextualize_query(query, session_id)
                query_validation = self.guards.validate_query(processing_query)
                if not query_validation["is_safe"]:
                    return self.formatter.create_error_response(query, "unsafe_query", "Malicious content detected", query_validation)
                
                context_result = self.retriever.retrieve_with_context(query=processing_query, top_k=top_k, search_mode=search_mode)
                retrieval_validation = self.guards.validate_retrieval(context_result["chunks"], processing_query)
                
                if not retrieval_validation["is_sufficient"]:
                    return {
                        "query": query, "status": "insufficient_context",
                        "clarification": retrieval_validation.get("clarification_prompt"),
                        "retrieved_chunks": len(context_result["chunks"]),
                        "avg_score": context_result["avg_score"], "success": False
                    }
                
                result = generation_func(processing_query, context_result["chunks"], context_result["avg_score"])
                if not result.get("success", False):
                    return result
                
                output_validation = self.guards.validate_output(self.formatter.to_json_string(result), context_result["chunks"], processing_query)
                result["validation"] = {
                    "query_safe": query_validation["is_safe"],
                    "evidence_sufficient": retrieval_validation["is_sufficient"],
                    "output_grounded": output_validation["is_valid"]
                }
                
                if not output_validation["is_valid"]:
                    result["warning"] = output_validation.get("warning")
                
                result["retrieval_context"] = {
                    "num_chunks": context_result["num_chunks"],
                    "avg_score": context_result["avg_score"],
                    "search_mode": search_mode
                }
                
                metrics_collector.increment_counter(metric_name)
                
                if session_id:
                    self.session_manager.add_turn(session_id, query, summary_func(result), raw_json=result)
                
                return result
        except Exception as e:
            return self.formatter.create_error_response(query, "pipeline_error", str(e))

    def generate_use_case(self, query: str, top_k: int = None, search_mode: str = "hybrid", session_id: str = None) -> Dict[str, Any]:
        return self._run_pipeline(
            query, top_k, search_mode, session_id,
            generation_func=self.use_case_generator.generate,
            metric_name="use_cases_generated",
            summary_func=lambda res: f"Generated use case: {res.get('use_case', {}).get('title', 'Untitled')}",
            timer_name="full_use_case_pipeline"
        )

    def generate_test_cases(self, query: str, top_k: int = None, search_mode: str = "hybrid", session_id: str = None) -> Dict[str, Any]:
        return self._run_pipeline(
            query, top_k, search_mode, session_id,
            generation_func=self.test_case_generator.generate,
            metric_name="test_cases_generated",
            summary_func=lambda res: f"Generated {len(res.get('test_cases', []))} test cases",
            timer_name="full_test_case_pipeline"
        )

    def _generate_combined_logic(self, query: str, chunks: list, avg_score: float) -> Dict[str, Any]:
        context_text = "\n---\n".join([c["content"] for c in chunks])
        prompt = get_generation_prompt(query=query, mode="both", context_chunks=context_text, avg_score=avg_score)
        response = self.llm_client.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT, temperature=0.7)
        parsed = self.formatter.parse_json_response(response["content"])
        if not parsed:
            return self.formatter.create_error_response(query, "parse_error", "Failed to parse response")
        formatted = self.formatter.format_combined(parsed)
        formatted["tokens"] = response.get("tokens", {})
        formatted["model"] = response.get("model", "")
        formatted["success"] = True
        return formatted

    def generate_combined(self, query: str, top_k: int = None, search_mode: str = "hybrid", session_id: str = None) -> Dict[str, Any]:
        return self._run_pipeline(
            query, top_k, search_mode, session_id,
            generation_func=self._generate_combined_logic,
            metric_name="combined_generated",
            summary_func=lambda res: f"Generated combined use case and {len(res.get('test_cases', []))} test cases",
            timer_name="full_combined_pipeline"
        )

    def get_generator_stats(self) -> Dict[str, Any]:
        return {
            "llm_client": self.llm_client.get_client_info(),
            "retriever_stats": self.retriever.get_retriever_stats(),
            "guard_stats": self.guards.get_guard_stats(),
            "metrics": {
                "use_cases_generated": metrics_collector.get_counter("use_cases_generated"),
                "test_cases_generated": metrics_collector.get_counter("test_cases_generated"),
                "combined_generated": metrics_collector.get_counter("combined_generated")
            }
        }
