from typing import Dict, Any, Optional
from pathlib import Path

from src.generation.llm_client import LLMClient
from src.generation.use_case_generator import UseCaseGenerator
from src.generation.test_case_generator import TestCaseGenerator
from src.generation.output_formatter import OutputFormatter
from src.retrieval import Retriever
from src.guards import GuardOrchestrator
from src.config import settings, get_generation_prompt, SYSTEM_PROMPT, CONTEXTUALIZE_QUERY_PROMPT
from src.utils import get_logger, timer, metrics_collector
from src.utils.session_manager import SessionManager

logger = get_logger(__name__)


class Generator:
    
    def __init__(self):
        logger.info("Initializing Generator...")
        
        self.llm_client = LLMClient()
        self.use_case_generator = UseCaseGenerator(self.llm_client)
        self.test_case_generator = TestCaseGenerator(self.llm_client)
        self.formatter = OutputFormatter()
        
        self.retriever = Retriever()
        self.guards = GuardOrchestrator()
        self.session_manager = SessionManager()
        
        logger.info("Generator initialized successfully")
    
    def _contextualize_query(self, query: str, session_id: str) -> str:
        """
        Rewrites the query to be standalone based on session history.
        """
        if not session_id:
            return query
            
        history = self.session_manager.format_history_for_llm(session_id)
        if not history:
            return query
            
        try:
            prompt = CONTEXTUALIZE_QUERY_PROMPT.format(
                chat_history=history,
                question=query
            )
            
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.3, # Low temp for faithful rewriting
                max_tokens=200
            )
            
            rewritten_query = response["content"].strip()
            if rewritten_query != query:
                logger.info(f"Query contextualized: '{query}' -> '{rewritten_query}'")
            return rewritten_query
            
        except Exception as e:
            logger.warning(f"Failed to contextualize query: {e}")
            return query

    def generate_use_case(
        self,
        query: str,
        top_k: int = None,
        search_mode: str = "hybrid",
        session_id: str = None
    ) -> Dict[str, Any]:
 
        logger.info(f"Starting use case generation for: '{query}' (Session: {session_id})")
        
        try:
            with timer("full_use_case_pipeline"):
                # 1. Contextualize Query
                processing_query = self._contextualize_query(query, session_id)
                
                query_validation = self.guards.validate_query(processing_query)
                
                if not query_validation["is_safe"]:
                    logger.warning("Query failed safety check")
                    return self.formatter.create_error_response(
                        query=query,
                        error_type="unsafe_query",
                        message="Query contains potentially malicious content",
                        details=query_validation
                    )
                
                context_result = self.retriever.retrieve_with_context(
                    query=processing_query,
                    top_k=top_k,
                    search_mode=search_mode
                )
                
                retrieval_validation = self.guards.validate_retrieval(
                    context_result["chunks"],
                    processing_query
                )
                
                if not retrieval_validation["is_sufficient"]:
                    logger.warning("Insufficient evidence for generation")
                    return {
                        "query": query,
                        "status": "insufficient_context",
                        "message": "Not enough evidence to generate use case",
                        "clarification": retrieval_validation.get("clarification_prompt"),
                        "retrieved_chunks": len(context_result["chunks"]),
                        "avg_score": context_result["avg_score"],
                        "success": False
                    }
                
                chat_history = self.session_manager.format_history_for_llm(session_id) if session_id else ""
                
                use_case = self.use_case_generator.generate(
                    query=processing_query,
                    context_chunks=context_result["chunks"],
                    avg_score=context_result["avg_score"],
                    chat_history=chat_history
                )
                
                if not use_case.get("success", False):
                    return use_case
                
                output_validation = self.guards.validate_output(
                    generated_output=self.formatter.to_json_string(use_case["use_case"]),
                    context_chunks=context_result["chunks"],
                    query=processing_query
                )
                
                use_case["validation"] = {
                    "query_safe": query_validation["is_safe"],
                    "evidence_sufficient": retrieval_validation["is_sufficient"],
                    "output_grounded": output_validation["is_valid"]
                }
                
                if not output_validation["is_valid"]:
                    use_case["warning"] = output_validation.get("warning")
                    logger.warning("Output validation flagged potential issues")
                
                use_case["retrieval_context"] = {
                    "num_chunks": context_result["num_chunks"],
                    "avg_score": context_result["avg_score"],
                    "search_mode": search_mode
                }
                
                metrics_collector.increment_counter("use_cases_generated")
                
                # Save to session
                if session_id:
                     self.session_manager.add_turn(
                        session_id, 
                        query, 
                        f"Generated use case: {use_case.get('use_case', {}).get('title', 'Untitled')}"
                    )
                
                logger.info("Use case generated successfully")
                return use_case
        
        except Exception as e:
            logger.error(f"Use case generation failed: {e}")
            return self.formatter.create_error_response(
                query=query,
                error_type="pipeline_error",
                message=str(e)
            )
    
    def generate_test_cases(
        self,
        query: str,
        top_k: int = None,
        search_mode: str = "hybrid",
        session_id: str = None
    ) -> Dict[str, Any]:
        
        logger.info(f"Starting test case generation for: '{query}' (Session: {session_id})")
        
        try:
            with timer("full_test_case_pipeline"):
                # 1. Contextualize Query
                processing_query = self._contextualize_query(query, session_id)

                query_validation = self.guards.validate_query(processing_query)
                
                if not query_validation["is_safe"]:
                    logger.warning("Query failed safety check")
                    return self.formatter.create_error_response(
                        query=query,
                        error_type="unsafe_query",
                        message="Query contains potentially malicious content",
                        details=query_validation
                    )
                
                context_result = self.retriever.retrieve_with_context(
                    query=processing_query,
                    top_k=top_k,
                    search_mode=search_mode
                )
                
                retrieval_validation = self.guards.validate_retrieval(
                    context_result["chunks"],
                    processing_query
                )
                
                if not retrieval_validation["is_sufficient"]:
                    logger.warning("Insufficient evidence for generation")
                    return {
                        "query": query,
                        "status": "insufficient_context",
                        "message": "Not enough evidence to generate test cases",
                        "clarification": retrieval_validation.get("clarification_prompt"),
                        "retrieved_chunks": len(context_result["chunks"]),
                        "avg_score": context_result["avg_score"],
                        "success": False
                    }
                
                chat_history = self.session_manager.format_history_for_llm(session_id) if session_id else ""
                
                test_cases = self.test_case_generator.generate(
                    query=processing_query,
                    context_chunks=context_result["chunks"],
                    avg_score=context_result["avg_score"],
                    chat_history=chat_history
                )
                
                if not test_cases.get("success", False):
                    return test_cases
                
                output_validation = self.guards.validate_output(
                    generated_output=self.formatter.to_json_string(test_cases["test_cases"]),
                    context_chunks=context_result["chunks"],
                    query=processing_query
                )
                
                test_cases["validation"] = {
                    "query_safe": query_validation["is_safe"],
                    "evidence_sufficient": retrieval_validation["is_sufficient"],
                    "output_grounded": output_validation["is_valid"]
                }
                
                if not output_validation["is_valid"]:
                    test_cases["warning"] = output_validation.get("warning")
                    logger.warning("Output validation flagged potential issues")
                
                test_cases["retrieval_context"] = {
                    "num_chunks": context_result["num_chunks"],
                    "avg_score": context_result["avg_score"],
                    "search_mode": search_mode
                }
                
                metrics_collector.increment_counter("test_cases_generated")
                
                # Save to session
                if session_id:
                     titles = [tc.get("title", "Untitled") for tc in test_cases.get("test_cases", [])]
                     summary = f"Generated {len(titles)} test cases: {', '.join(titles)}"
                     self.session_manager.add_turn(
                        session_id, 
                        query, 
                        summary
                    )

                logger.info(f"Generated {len(test_cases['test_cases'])} test cases")
                return test_cases
        
        except Exception as e:
            logger.error(f"Test case generation failed: {e}")
            return self.formatter.create_error_response(
                query=query,
                error_type="pipeline_error",
                message=str(e)
            )
    
    def generate_combined(
        self,
        query: str,
        top_k: int = None,
        search_mode: str = "hybrid",
        session_id: str = None
    ) -> Dict[str, Any]:
        
        logger.info(f"Starting combined generation for: '{query}' (Session: {session_id})")
        
        try:
            with timer("full_combined_pipeline"):
                # 1. Contextualize Query
                processing_query = self._contextualize_query(query, session_id)

                query_validation = self.guards.validate_query(processing_query)
                
                if not query_validation["is_safe"]:
                    return self.formatter.create_error_response(
                        query=query,
                        error_type="unsafe_query",
                        message="Query contains potentially malicious content"
                    )
                
                context_result = self.retriever.retrieve_with_context(
                    query=processing_query,
                    top_k=top_k,
                    search_mode=search_mode
                )
                
                retrieval_validation = self.guards.validate_retrieval(
                    context_result["chunks"],
                    processing_query
                )
                
                if not retrieval_validation["is_sufficient"]:
                    return {
                        "query": query,
                        "status": "insufficient_context",
                        "clarification": retrieval_validation.get("clarification_prompt"),
                        "success": False
                    }
                
                context_text = "\n---\n".join([c["content"] for c in context_result["chunks"]])
                
                chat_history = self.session_manager.format_history_for_llm(session_id) if session_id else ""
                
                prompt = get_generation_prompt(
                    query=processing_query,
                    mode="both",
                    context_chunks=context_text,
                    avg_score=context_result["avg_score"],
                    chat_history=chat_history
                )
                
                response = self.llm_client.generate(
                    prompt=prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.7
                )
                
                parsed = self.formatter.parse_json_response(response["content"])
                
                if not parsed:
                    return self.formatter.create_error_response(
                        query=query,
                        error_type="parse_error",
                        message="Failed to parse response"
                    )
                
                formatted = self.formatter.format_combined(parsed)
                
                formatted["tokens"] = response.get("tokens", {})
                formatted["model"] = response.get("model", "")
                formatted["success"] = True
                formatted["retrieval_context"] = {
                    "num_chunks": context_result["num_chunks"],
                    "avg_score": context_result["avg_score"]
                }
                
                metrics_collector.increment_counter("combined_generated")
                
                # Save to session
                if session_id:
                     self.session_manager.add_turn(
                        session_id, 
                        query, 
                        f"Generated combined use case: {formatted.get('use_case', {}).get('title', 'Untitled')} and {len(formatted.get('test_cases', []))} test cases"
                    )

                logger.info("Combined generation successful")
                return formatted
        
        except Exception as e:
            logger.error(f"Combined generation failed: {e}")
            return self.formatter.create_error_response(
                query=query,
                error_type="pipeline_error",
                message=str(e)
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
