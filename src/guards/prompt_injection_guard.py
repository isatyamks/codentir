from typing import Dict, Any, List, Optional
import re

from src.config import settings, PROMPT_INJECTION_PATTERNS


class PromptInjectionGuard:
    
    def __init__(self):
        self.injection_patterns = PROMPT_INJECTION_PATTERNS.copy()
        self.custom_patterns = []
    
    def add_pattern(self, pattern: str):
        if pattern not in self.custom_patterns:
            self.custom_patterns.append(pattern.lower())
    
    def check_query(self, query: str) -> Dict[str, Any]:
        if not query:
            return {
                "is_safe": True,
                "detected_patterns": [],
                "risk_level": "none"
            }
        
        query_lower = query.lower()
        detected = []
        
        all_patterns = self.injection_patterns + self.custom_patterns
        
        for pattern in all_patterns:
            if pattern in query_lower:
                detected.append(pattern)
        
        risk_level = self._assess_risk_level(len(detected))
        
        return {
            "is_safe": len(detected) == 0,
            "detected_patterns": detected,
            "risk_level": risk_level,
            "original_query": query
        }
    
    def check_document(self, content: str) -> Dict[str, Any]:

        if not content:
            return {
                "is_safe": True,
                "detected_patterns": [],
                "risk_level": "none"
            }
        
        content_lower = content.lower()
        detected = []
        
        for pattern in self.injection_patterns:
            if pattern in content_lower:
                detected.append(pattern)
        
        return {
            "is_safe": len(detected) == 0,
            "detected_patterns": detected,
            "risk_level": self._assess_risk_level(len(detected)),
            "recommendation": "sanitize" if detected else "safe"
        }
    
    def sanitize_query(self, query: str) -> str:

        sanitized = query
        
        check_result = self.check_query(query)
        
        if not check_result["is_safe"]:
            for pattern in check_result["detected_patterns"]:
                sanitized = re.sub(
                    re.escape(pattern),
                    "[REMOVED]",
                    sanitized,
                    flags=re.IGNORECASE
                )
        
        return sanitized
    
    def _assess_risk_level(self, pattern_count: int) -> str:
        if pattern_count == 0:
            return "none"
        elif pattern_count == 1:
            return "low"
        elif pattern_count <= 3:
            return "medium"
        else:
            return "high"
    
    def validate_safe(self, query: str, raise_error: bool = False) -> bool:

        result = self.check_query(query)
        
        if not result["is_safe"]:
            message = (
                f"Unsafe query detected: {len(result['detected_patterns'])} "
                f"injection patterns found. Risk level: {result['risk_level']}"
            )
            
            if raise_error:
                raise ValueError(message)
            else:
                return False
        
        return True
