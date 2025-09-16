"""
Safe JSON parsing utilities for handling LLM responses.
"""
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SafeJsonParser:
    """Safe JSON parsing with error handling."""

    @staticmethod
    def parse_json_response(response: str) -> Dict[str, Any]:
        """Safely parse JSON response from LLM."""
        try:
            cleaned = response.strip()

            if "```json" in cleaned:
                start = cleaned.find("```json") + 7
                end = cleaned.find("```", start)
                if end != -1:
                    cleaned = cleaned[start:end].strip()
            elif "```" in cleaned:
                start = cleaned.find("```") + 3
                end = cleaned.find("```", start)
                if end != -1:
                    cleaned = cleaned[start:end].strip()

            parsed = json.loads(cleaned)
            return parsed

        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}. Attempting to fix...")

            try:
                import re
                fixed = re.sub(r',(\s*[}\]])', r'\1', cleaned)
                parsed = json.loads(fixed)
                return parsed
            except Exception:
                logger.error(f"Could not parse JSON response: {cleaned[:200]}...")
                return {"error": "Failed to parse JSON", "raw_response": cleaned}

    @staticmethod
    def extract_json_from_markdown(text: str) -> str:
        """Extract JSON from markdown code blocks."""
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()
        return text.strip()

    @staticmethod
    def fix_common_json_errors(text: str) -> str:
        """Fix common JSON formatting errors."""
        import re
        
        # Remove trailing commas before } or ]
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Fix single quotes to double quotes
        text = re.sub(r"'([^']*)':", r'"\1":', text)
        
        # Fix unquoted keys (simple case)
        text = re.sub(r'(\w+):', r'"\1":', text)
        
        return text

    @staticmethod
    def validate_json_structure(data: Dict[str, Any], required_fields: list = None) -> bool:
        """Validate JSON structure against required fields."""
        if required_fields is None:
            return True
            
        if not isinstance(data, dict):
            return False
            
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False
                
        return True

    @staticmethod
    def clean_and_parse(response: str, required_fields: list = None) -> Dict[str, Any]:
        """Complete JSON cleaning and parsing pipeline."""
        try:
            # Step 1: Extract from markdown if needed
            extracted = SafeJsonParser.extract_json_from_markdown(response)
            
            # Step 2: Fix common errors
            fixed = SafeJsonParser.fix_common_json_errors(extracted)
            
            # Step 3: Parse
            parsed = json.loads(fixed)
            
            # Step 4: Validate structure if required
            if required_fields and not SafeJsonParser.validate_json_structure(parsed, required_fields):
                return {"error": "Invalid JSON structure", "raw_response": response}
                
            return parsed
            
        except Exception as e:
            logger.error(f"Complete JSON parsing failed: {e}")
            return {"error": f"Failed to parse JSON: {str(e)}", "raw_response": response}