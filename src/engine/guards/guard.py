from typing import Any, Dict, List

from src.engine.guards.evidence import EvidenceThreshold
from src.engine.guards.hallucination import HallucinationGuard
from src.engine.guards.injection import PromptInjectionGuard
from src.config.settings import settings


class GuardOrchestrator:

    def __init__(self):
        self.prompt_injection_guard = PromptInjectionGuard()
        self.evidence_threshold = EvidenceThreshold()
        self.hallucination_guard = HallucinationGuard()

    def validate_query(self, query: str, strict: bool = False) -> Dict[str, Any]:

        results = {"is_safe": True, "query": query, "checks": {}}

        if settings.ENABLE_PROMPT_INJECTION_GUARD:
            injection_check = self.prompt_injection_guard.check_query(query)
            results["checks"]["prompt_injection"] = injection_check

            if not injection_check["is_safe"]:
                results["is_safe"] = False
                if strict:
                    raise ValueError(
                        f"Query failed prompt injection check: "
                        f"{injection_check['risk_level']} risk"
                    )

        return results

    def validate_retrieval(
        self, retrieval_results: List[Dict[str, Any]], query: str = ""
    ) -> Dict[str, Any]:

        results = {"is_sufficient": True, "checks": {}}

        if settings.ENABLE_EVIDENCE_THRESHOLD:
            evidence_check = self.evidence_threshold.check_evidence(
                retrieval_results, query
            )
            results["checks"]["evidence_threshold"] = evidence_check

            if not evidence_check["sufficient"]:
                results["is_sufficient"] = False
                results["recommendation"] = evidence_check.get("recommendation")
                results["clarification_needed"] = True
                results["clarification_prompt"] = (
                    self.evidence_threshold.get_clarification_prompt(
                        query, evidence_check
                    )
                )

        return results

    def validate_output(
        self,
        generated_output: str,
        context_chunks: List[Dict[str, Any]],
        query: str = "",
        strict: bool = False,
    ) -> Dict[str, Any]:

        results = {"is_valid": True, "output": generated_output, "checks": {}}

        if settings.ENABLE_HALLUCINATION_GUARD:
            grounding_check = self.hallucination_guard.check_grounding(
                generated_output, context_chunks, query
            )
            results["checks"]["hallucination"] = grounding_check

            if not grounding_check["is_grounded"]:
                results["is_valid"] = False
                results["warning"] = self.hallucination_guard.get_hallucination_report(
                    grounding_check
                )

                if strict:
                    raise ValueError(
                        f"Output failed grounding check: "
                        f"{grounding_check['grounding_ratio']:.1%} grounded"
                    )

        return results

    def full_pipeline_validation(
        self,
        query: str,
        retrieval_results: List[Dict[str, Any]],
        generated_output: str = None,
    ) -> Dict[str, Any]:

        results = {"overall_safe": True, "validations": {}}

        query_validation = self.validate_query(query)
        results["validations"]["query"] = query_validation

        if not query_validation["is_safe"]:
            results["overall_safe"] = False
            results["blocked_reason"] = "unsafe_query"
            return results

        retrieval_validation = self.validate_retrieval(retrieval_results, query)
        results["validations"]["retrieval"] = retrieval_validation

        if not retrieval_validation["is_sufficient"]:
            results["overall_safe"] = False
            results["action_required"] = "clarification"
            results["clarification_prompt"] = retrieval_validation.get(
                "clarification_prompt"
            )
            return results

        if generated_output:
            output_validation = self.validate_output(
                generated_output, retrieval_results, query
            )
            results["validations"]["output"] = output_validation

            if not output_validation["is_valid"]:
                results["overall_safe"] = False
                results["warning"] = output_validation.get("warning")

        return results

    def get_guard_stats(self) -> Dict[str, Any]:
        return {
            "prompt_injection_guard": {
                "enabled": settings.ENABLE_PROMPT_INJECTION_GUARD,
                "patterns_count": len(self.prompt_injection_guard.injection_patterns),
            },
            "evidence_threshold": self.evidence_threshold.get_stats(),
            "hallucination_guard": {
                "enabled": settings.ENABLE_HALLUCINATION_GUARD,
                "max_deviation": self.hallucination_guard.max_deviation,
            },
        }
