from typing import Dict, Any, List
import json
import re

from src.config import settings


class HallucinationGuard:
    
    def __init__(self, max_deviation: float = None):
        self.max_deviation = max_deviation or settings.MAX_CONTEXT_DEVIATION
    
    def check_grounding(
        self,
        generated_output: str,
        context_chunks: List[Dict[str, Any]],
        query: str = ""
    ) -> Dict[str, Any]:
        
        if not generated_output:
            return {
                "is_grounded": True,
                "reason": "empty_output",
                "confidence": 1.0,
                "grounded_statements": 0,
                "total_statements": 0,
                "ungrounded_statements": [],
                "grounding_ratio": 1.0,
                "threshold": 1 - self.max_deviation
            }
        
        if not context_chunks:
            return {
                "is_grounded": False,
                "reason": "no_context",
                "confidence": 0.0,
                "warning": "Output generated without context - likely hallucination",
                "grounded_statements": 0,
                "total_statements": 0,
                "ungrounded_statements": [],
                "grounding_ratio": 0.0,
                "threshold": 1 - self.max_deviation
            }
        
        context_text = self._combine_context(context_chunks)
        
        output_statements = self._extract_facts(generated_output)
        
        grounded_count = 0
        ungrounded_statements = []
        
        for statement in output_statements:
            if self._is_statement_grounded(statement, context_text):
                grounded_count += 1
            else:
                ungrounded_statements.append(statement)
        
        total_statements = len(output_statements)
        grounding_ratio = grounded_count / total_statements if total_statements > 0 else 1.0
        
        is_grounded = grounding_ratio >= (1 - self.max_deviation)
        
        result = {
            "is_grounded": is_grounded,
            "grounding_ratio": round(grounding_ratio, 4),
            "grounded_statements": grounded_count,
            "total_statements": total_statements,
            "ungrounded_statements": ungrounded_statements[:5],
            "confidence": round(grounding_ratio, 4),
            "threshold": 1 - self.max_deviation
        }
        
        return result
    
    def _combine_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        context_texts = []
        
        for chunk in context_chunks:
            if isinstance(chunk, dict) and 'content' in chunk:
                context_texts.append(chunk['content'])
            elif isinstance(chunk, str):
                context_texts.append(chunk)
        
        return " ".join(context_texts).lower()
    
    def _extract_facts(self, text: str) -> List[str]:
        try:
            if text.strip().startswith('{'):
                json_data = json.loads(text)
                statements = self._extract_from_json(json_data)
            else:
                statements = self._extract_from_text(text)
            
            return statements
        
        except json.JSONDecodeError:
            return self._extract_from_text(text)
    
    def _extract_from_json(self, data: Any, statements: List[str] = None) -> List[str]:
        if statements is None:
            statements = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ['query', 'chunk_id', 'metadata', 'grounding_evidence']:
                    continue
                
                if isinstance(value, str) and len(value) > 10:
                    statements.append(value)
                elif isinstance(value, (dict, list)):
                    self._extract_from_json(value, statements)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str) and len(item) > 10:
                    statements.append(item)
                elif isinstance(item, (dict, list)):
                    self._extract_from_json(item, statements)
        
        return statements
    
    def _extract_from_text(self, text: str) -> List[str]:
        sentences = re.split(r'[.!?]\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _is_statement_grounded(self, statement: str, context: str) -> bool:
        statement_lower = statement.lower()
        context_lower = context.lower()
        
        if len(statement) < 15:
            return True
        
        statement_words = set(re.findall(r'\b\w+\b', statement_lower))
        
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
                       'for', 'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been',
                       'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                       'can', 'could', 'should', 'may', 'might', 'must', 'shall',
                       'user', 'users', 'system', 'feature', 'data', 'support'}
        
        statement_words = {w for w in statement_words if len(w) > 2 and w not in common_words}
        
        if not statement_words:
            return True
        
        matched_words = 0
        for word in statement_words:
            if word in context_lower:
                matched_words += 1
            else:
                for context_word in context_lower.split():
                    if word in context_word or context_word in word:
                        matched_words += 0.5
                        break
        
        match_ratio = matched_words / len(statement_words)
        
        return match_ratio >= 0.3
    
    def validate_output(
        self,
        output: str,
        context: List[Dict[str, Any]],
        raise_error: bool = False
    ) -> bool:
        
        check = self.check_grounding(output, context)
        
        if not check["is_grounded"]:
            message = (
                f"Hallucination detected: only {check['grounding_ratio']:.1%} "
                f"of statements are grounded in context "
                f"(threshold: {check['threshold']:.1%})"
            )
            
            if raise_error:
                raise ValueError(message)
            else:
                return False
        
        return True
    
    def get_hallucination_report(
        self,
        check_result: Dict[str, Any]
    ) -> str:
        if check_result["is_grounded"]:
            return "Output is well-grounded in the provided context."
        
        return (
            f"Warning: Potential hallucination detected.\n"
            f"- Grounded statements: {check_result['grounded_statements']}/{check_result['total_statements']}\n"
            f"- Grounding ratio: {check_result['grounding_ratio']:.1%}\n"
            f"- Threshold: {check_result['threshold']:.1%}\n"
            f"- Ungrounded examples: {', '.join(check_result['ungrounded_statements'][:3])}"
        )
