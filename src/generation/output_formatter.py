import json
from typing import Dict, Any, Optional

from src.utils import get_logger

logger = get_logger(__name__)


class OutputFormatter:
    
    def __init__(self):
        logger.info("OutputFormatter initialized")
    
    def parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        
        try:
            response = response.strip()
            
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]
            
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                json_str = response[start_idx:end_idx + 1]
                parsed = json.loads(json_str)
                logger.debug("Successfully parsed JSON response")
                return parsed
            
            parsed = json.loads(response)
            logger.debug("Successfully parsed JSON response")
            return parsed
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Response preview: {response[:500]}...")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            return None
    
    def validate_use_case(self, data: Dict[str, Any]) -> bool:
       
        required_fields = ["query", "use_case"]
        use_case_fields = ["title", "description", "preconditions", "steps", "expected_result"]
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        use_case = data.get("use_case", {})
        for field in use_case_fields:
            if field not in use_case:
                logger.warning(f"Missing use case field: {field}")
                return False
        
        return True
    
    def validate_test_cases(self, data: Dict[str, Any]) -> bool:
        
        if "test_cases" not in data:
            logger.warning("Missing test_cases field")
            return False
        
        test_cases = data.get("test_cases", [])
        if not isinstance(test_cases, list) or len(test_cases) == 0:
            logger.warning("test_cases must be a non-empty list")
            return False
        
        required_fields = ["test_id", "type", "title", "steps", "expected_result"]
        
        for i, tc in enumerate(test_cases):
            for field in required_fields:
                if field not in tc:
                    logger.warning(f"Test case {i} missing field: {field}")
                    return False
        
        return True
    
    def format_use_case(self, data: Dict[str, Any]) -> Dict[str, Any]:
        
        use_case = data.get("use_case", {})
        
        formatted = {
            "query": data.get("query", ""),
            "use_case": {
                "title": use_case.get("title", ""),
                "description": use_case.get("description", ""),
                "preconditions": use_case.get("preconditions", []),
                "steps": use_case.get("steps", []),
                "expected_result": use_case.get("expected_result", ""),
                "negative_cases": use_case.get("negative_cases", []),
                "boundary_cases": use_case.get("boundary_cases", [])
            },
            "grounding_evidence": data.get("grounding_evidence", []),
            "assumptions": data.get("assumptions", []),
            "clarifying_questions": data.get("clarifying_questions", []),
            "confidence": data.get("confidence", 0.0)
        }
        
        return formatted
    
    def format_test_cases(self, data: Dict[str, Any]) -> Dict[str, Any]:
        
        test_cases = data.get("test_cases", [])
        
        formatted_cases = []
        for tc in test_cases:
            formatted_cases.append({
                "test_id": tc.get("test_id", ""),
                "type": tc.get("type", "functional"),
                "title": tc.get("title", ""),
                "preconditions": tc.get("preconditions", []),
                "steps": tc.get("steps", []),
                "test_data": tc.get("test_data", {}),
                "expected_result": tc.get("expected_result", ""),
                "priority": tc.get("priority", "medium"),
                "category": tc.get("category", "functional")
            })
        
        return {
            "query": data.get("query", ""),
            "test_cases": formatted_cases,
            "grounding_evidence": data.get("grounding_evidence", []),
            "assumptions": data.get("assumptions", []),
            "clarifying_questions": data.get("clarifying_questions", []),
            "confidence": data.get("confidence", 0.0)
        }
    
    def format_combined(self, data: Dict[str, Any]) -> Dict[str, Any]:
        
        use_case_formatted = self.format_use_case(data)
        test_cases_formatted = self.format_test_cases(data)
        
        return {
            "query": data.get("query", ""),
            "use_case": use_case_formatted["use_case"],
            "test_cases": test_cases_formatted["test_cases"],
            "grounding_evidence": data.get("grounding_evidence", []),
            "assumptions": data.get("assumptions", []),
            "clarifying_questions": data.get("clarifying_questions", []),
            "confidence": data.get("confidence", 0.0)
        }
    
    def create_error_response(
        self,
        query: str,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        
        return {
            "query": query,
            "status": "error",
            "error_type": error_type,
            "message": message,
            "details": details or {},
            "success": False
        }
    
    def to_json_string(self, data: Dict[str, Any], pretty: bool = True) -> str:
        
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)
