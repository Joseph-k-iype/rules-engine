"""
Advanced Type Inference Engine for ODRL Constraints
Analyzes rightOperand values and infers appropriate Rego data types and operators
"""
import re
from typing import Dict, Any, List, Union, Tuple
from datetime import datetime
from enum import Enum


class RegoDataType(Enum):
    """Inferred Rego data types"""
    STRING = "string"
    NUMBER_INT = "number_int"
    NUMBER_FLOAT = "number_float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    TIME = "time"
    DURATION = "duration"
    URI = "uri"
    EMAIL = "email"
    SET_STRING = "set_string"
    SET_NUMBER = "set_number"
    ARRAY = "array"
    HIERARCHICAL = "hierarchical"  # For department/category hierarchies
    PATTERN = "pattern"  # For regex patterns
    UNKNOWN = "unknown"


class TypeInferenceEngine:
    """
    Sophisticated type inference engine that analyzes ODRL constraint values
    and determines the appropriate Rego data type, operators, and functions.
    """
    
    def __init__(self):
        # Temporal patterns
        self.datetime_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$')
        self.date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        self.time_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}$')
        self.duration_pattern = re.compile(r'^P(\d+Y)?(\d+M)?(\d+D)?(T(\d+H)?(\d+M)?(\d+S)?)?$')
        
        # URI and email patterns
        self.uri_pattern = re.compile(r'^https?://[^\s]+$')
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        # Hierarchical patterns (e.g., "dept:engineering:backend")
        self.hierarchical_pattern = re.compile(r'^[a-zA-Z]+:[a-zA-Z0-9_-]+(:[a-zA-Z0-9_-]+)*$')
    
    def infer_type(self, value: Any, left_operand: str = None, rdfs_comment: str = None) -> Dict[str, Any]:
        """
        Infer the data type from a rightOperand value with context.
        
        Args:
            value: The rightOperand value
            left_operand: The leftOperand field name (provides context)
            rdfs_comment: RDFS comment (provides semantic hints)
            
        Returns:
            Dictionary with type info, rego pattern, and recommended functions
        """
        
        # Handle None
        if value is None:
            return self._create_type_result(RegoDataType.UNKNOWN, value)
        
        # Handle lists/arrays
        if isinstance(value, list):
            return self._infer_list_type(value, left_operand, rdfs_comment)
        
        # Handle boolean
        if isinstance(value, bool):
            return self._create_type_result(RegoDataType.BOOLEAN, value)
        
        # Handle numeric types
        if isinstance(value, int):
            return self._create_type_result(RegoDataType.NUMBER_INT, value)
        
        if isinstance(value, float):
            return self._create_type_result(RegoDataType.NUMBER_FLOAT, value)
        
        # Handle string types (most complex)
        if isinstance(value, str):
            return self._infer_string_type(value, left_operand, rdfs_comment)
        
        # Default
        return self._create_type_result(RegoDataType.UNKNOWN, value)
    
    def _infer_string_type(self, value: str, left_operand: str = None, rdfs_comment: str = None) -> Dict[str, Any]:
        """Infer type for string values using multiple heuristics"""
        
        # Check rdfs:comment for hints
        comment_lower = (rdfs_comment or "").lower()
        left_op_lower = (left_operand or "").lower()
        
        # Temporal types
        if self.datetime_pattern.match(value):
            return self._create_type_result(RegoDataType.DATETIME, value)
        
        if self.date_pattern.match(value):
            return self._create_type_result(RegoDataType.DATE, value)
        
        if self.time_pattern.match(value):
            return self._create_type_result(RegoDataType.TIME, value)
        
        if self.duration_pattern.match(value):
            return self._create_type_result(RegoDataType.DURATION, value)
        
        # URI type
        if self.uri_pattern.match(value):
            return self._create_type_result(RegoDataType.URI, value)
        
        # Email type
        if self.email_pattern.match(value):
            return self._create_type_result(RegoDataType.EMAIL, value)
        
        # Hierarchical type (from context)
        if (self.hierarchical_pattern.match(value) or 
            'hierarchy' in comment_lower or 
            'subcategories' in comment_lower or
            'parent' in comment_lower or
            left_op_lower in ['department', 'category', 'datacategory', 'organization']):
            return self._create_type_result(RegoDataType.HIERARCHICAL, value)
        
        # Pattern type (from context)
        if ('pattern' in comment_lower or 
            'format' in comment_lower or
            'regex' in comment_lower or
            'match' in comment_lower):
            return self._create_type_result(RegoDataType.PATTERN, value)
        
        # Default to string
        return self._create_type_result(RegoDataType.STRING, value)
    
    def _infer_list_type(self, values: List[Any], left_operand: str = None, rdfs_comment: str = None) -> Dict[str, Any]:
        """Infer type for list values"""
        
        if not values:
            return self._create_type_result(RegoDataType.ARRAY, values)
        
        # Check first element type
        first_elem = values[0]
        
        # All strings
        if all(isinstance(v, str) for v in values):
            # Check if all are numbers as strings
            if all(v.isdigit() for v in values):
                return self._create_type_result(RegoDataType.SET_NUMBER, [int(v) for v in values])
            return self._create_type_result(RegoDataType.SET_STRING, values)
        
        # All numbers
        if all(isinstance(v, (int, float)) for v in values):
            return self._create_type_result(RegoDataType.SET_NUMBER, values)
        
        # Mixed or complex
        return self._create_type_result(RegoDataType.ARRAY, values)
    
    def _create_type_result(self, data_type: RegoDataType, value: Any) -> Dict[str, Any]:
        """Create a type inference result with Rego recommendations"""
        
        result = {
            "inferred_type": data_type.value,
            "original_value": value,
            "rego_type": self._get_rego_type(data_type),
            "recommended_functions": self._get_recommended_functions(data_type),
            "comparison_operators": self._get_comparison_operators(data_type),
            "requires_parsing": self._requires_parsing(data_type)
        }
        
        return result
    
    def _get_rego_type(self, data_type: RegoDataType) -> str:
        """Map inferred type to Rego type"""
        mapping = {
            RegoDataType.STRING: "string",
            RegoDataType.NUMBER_INT: "number",
            RegoDataType.NUMBER_FLOAT: "number",
            RegoDataType.BOOLEAN: "boolean",
            RegoDataType.DATETIME: "number (nanoseconds)",
            RegoDataType.DATE: "number (nanoseconds)",
            RegoDataType.TIME: "number (nanoseconds)",
            RegoDataType.DURATION: "number (nanoseconds)",
            RegoDataType.URI: "string",
            RegoDataType.EMAIL: "string",
            RegoDataType.SET_STRING: "set[string]",
            RegoDataType.SET_NUMBER: "set[number]",
            RegoDataType.ARRAY: "array",
            RegoDataType.HIERARCHICAL: "string",
            RegoDataType.PATTERN: "string",
            RegoDataType.UNKNOWN: "any"
        }
        return mapping.get(data_type, "any")
    
    def _get_recommended_functions(self, data_type: RegoDataType) -> List[str]:
        """Get recommended Rego functions for this type"""
        functions = {
            RegoDataType.STRING: ["==", "!=", "contains", "startswith", "endswith"],
            RegoDataType.NUMBER_INT: ["==", "!=", "<", ">", "<=", ">="],
            RegoDataType.NUMBER_FLOAT: ["==", "!=", "<", ">", "<=", ">="],
            RegoDataType.BOOLEAN: ["==", "!="],
            RegoDataType.DATETIME: ["time.parse_rfc3339_ns", "time.now_ns", "<", ">", "<=", ">="],
            RegoDataType.DATE: ["time.parse_rfc3339_ns", "time.now_ns", "<", ">", "<=", ">="],
            RegoDataType.TIME: ["time.parse_rfc3339_ns", "<", ">"],
            RegoDataType.DURATION: ["time.parse_duration_ns", "+", "-"],
            RegoDataType.URI: ["==", "!=", "startswith"],
            RegoDataType.EMAIL: ["==", "!=", "regex.match", "endswith"],
            RegoDataType.SET_STRING: ["in", "==", "!="],
            RegoDataType.SET_NUMBER: ["in", "==", "!="],
            RegoDataType.ARRAY: ["in", "count"],
            RegoDataType.HIERARCHICAL: ["startswith", "==", "contains"],
            RegoDataType.PATTERN: ["regex.match", "regex.find_n"],
            RegoDataType.UNKNOWN: ["=="]
        }
        return functions.get(data_type, ["=="])
    
    def _get_comparison_operators(self, data_type: RegoDataType) -> List[str]:
        """Get valid comparison operators for this type"""
        operators = {
            RegoDataType.STRING: ["eq", "neq"],
            RegoDataType.NUMBER_INT: ["eq", "neq", "lt", "gt", "lteq", "gteq"],
            RegoDataType.NUMBER_FLOAT: ["eq", "neq", "lt", "gt", "lteq", "gteq"],
            RegoDataType.BOOLEAN: ["eq", "neq"],
            RegoDataType.DATETIME: ["eq", "neq", "lt", "gt", "lteq", "gteq"],
            RegoDataType.DATE: ["eq", "neq", "lt", "gt", "lteq", "gteq"],
            RegoDataType.TIME: ["eq", "neq", "lt", "gt", "lteq", "gteq"],
            RegoDataType.DURATION: ["eq", "neq", "lt", "gt", "lteq", "gteq"],
            RegoDataType.URI: ["eq", "neq", "isA", "hasPart"],
            RegoDataType.EMAIL: ["eq", "neq"],
            RegoDataType.SET_STRING: ["isAnyOf", "isAllOf", "isNoneOf"],
            RegoDataType.SET_NUMBER: ["isAnyOf", "isAllOf", "isNoneOf"],
            RegoDataType.ARRAY: ["isAnyOf", "isPartOf", "hasPart"],
            RegoDataType.HIERARCHICAL: ["eq", "isA", "isPartOf"],
            RegoDataType.PATTERN: ["eq", "neq"],
            RegoDataType.UNKNOWN: ["eq", "neq"]
        }
        return operators.get(data_type, ["eq", "neq"])
    
    def _requires_parsing(self, data_type: RegoDataType) -> bool:
        """Check if type requires parsing/conversion"""
        return data_type in [
            RegoDataType.DATETIME,
            RegoDataType.DATE,
            RegoDataType.TIME,
            RegoDataType.DURATION
        ]
    
    def generate_rego_expression(
        self, 
        left_operand: str, 
        operator: str, 
        right_operand: Any,
        inferred_type: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate the appropriate Rego expression based on inferred type.
        
        Returns:
            Dictionary with rego_expression and explanation
        """
        
        data_type = RegoDataType(inferred_type["inferred_type"])
        input_ref = f"input.{left_operand}"
        
        # Decision tree based on data type
        if data_type == RegoDataType.DATETIME:
            return self._generate_datetime_expression(input_ref, operator, right_operand)
        
        elif data_type == RegoDataType.DATE:
            return self._generate_date_expression(input_ref, operator, right_operand)
        
        elif data_type == RegoDataType.DURATION:
            return self._generate_duration_expression(input_ref, operator, right_operand)
        
        elif data_type in [RegoDataType.NUMBER_INT, RegoDataType.NUMBER_FLOAT]:
            return self._generate_numeric_expression(input_ref, operator, right_operand)
        
        elif data_type == RegoDataType.BOOLEAN:
            return self._generate_boolean_expression(input_ref, operator, right_operand)
        
        elif data_type in [RegoDataType.SET_STRING, RegoDataType.SET_NUMBER]:
            return self._generate_set_expression(input_ref, operator, right_operand)
        
        elif data_type == RegoDataType.HIERARCHICAL:
            return self._generate_hierarchical_expression(input_ref, operator, right_operand)
        
        elif data_type == RegoDataType.PATTERN:
            return self._generate_pattern_expression(input_ref, operator, right_operand)
        
        elif data_type == RegoDataType.EMAIL:
            return self._generate_email_expression(input_ref, operator, right_operand)
        
        elif data_type == RegoDataType.URI:
            return self._generate_uri_expression(input_ref, operator, right_operand)
        
        else:  # STRING or UNKNOWN
            return self._generate_string_expression(input_ref, operator, right_operand)
    
    def _generate_datetime_expression(self, input_ref: str, operator: str, value: str) -> Dict[str, str]:
        """Generate expression for datetime comparison"""
        
        operator_map = {
            "eq": "==",
            "neq": "!=",
            "lt": "<",
            "gt": ">",
            "lteq": "<=",
            "gteq": ">="
        }
        
        rego_op = operator_map.get(operator, "==")
        
        # Parse the datetime value
        parsed_value = f'time.parse_rfc3339_ns("{value}")'
        
        # For future dates, compare with now
        if operator in ["lt", "lteq"]:
            expression = f"time.now_ns() {rego_op} {parsed_value}"
            explanation = f"Current time must be {operator} {value}"
        else:
            expression = f"{parsed_value} {rego_op} time.now_ns()"
            explanation = f"Time {value} must be {operator} current time"
        
        return {
            "rego_expression": expression,
            "explanation": explanation,
            "type": "temporal_datetime"
        }
    
    def _generate_date_expression(self, input_ref: str, operator: str, value: str) -> Dict[str, str]:
        """Generate expression for date comparison"""
        
        operator_map = {
            "eq": "==",
            "neq": "!=",
            "lt": "<",
            "gt": ">",
            "lteq": "<=",
            "gteq": ">="
        }
        
        rego_op = operator_map.get(operator, "==")
        
        # Convert date to datetime for parsing
        datetime_value = f"{value}T00:00:00Z"
        parsed_value = f'time.parse_rfc3339_ns("{datetime_value}")'
        
        expression = f"time.now_ns() {rego_op} {parsed_value}"
        
        return {
            "rego_expression": expression,
            "explanation": f"Date comparison: {operator} {value}",
            "type": "temporal_date"
        }
    
    def _generate_duration_expression(self, input_ref: str, operator: str, value: str) -> Dict[str, str]:
        """Generate expression for duration"""
        
        parsed_duration = f'time.parse_duration_ns("{value}")'
        
        expression = f"time.now_ns() - {input_ref} {self._map_operator(operator)} {parsed_duration}"
        
        return {
            "rego_expression": expression,
            "explanation": f"Duration constraint: {operator} {value}",
            "type": "duration"
        }
    
    def _generate_numeric_expression(self, input_ref: str, operator: str, value: Union[int, float]) -> Dict[str, str]:
        """Generate expression for numeric comparison"""
        
        rego_op = self._map_operator(operator)
        expression = f"{input_ref} {rego_op} {value}"
        
        return {
            "rego_expression": expression,
            "explanation": f"Numeric comparison: {operator} {value}",
            "type": "numeric"
        }
    
    def _generate_boolean_expression(self, input_ref: str, operator: str, value: bool) -> Dict[str, str]:
        """Generate expression for boolean"""
        
        bool_str = "true" if value else "false"
        
        if operator == "neq":
            expression = f"{input_ref} != {bool_str}"
        else:
            expression = f"{input_ref} == {bool_str}"
        
        return {
            "rego_expression": expression,
            "explanation": f"Boolean check: {operator} {value}",
            "type": "boolean"
        }
    
    def _generate_set_expression(self, input_ref: str, operator: str, values: List[Any]) -> Dict[str, str]:
        """Generate expression for set membership"""
        
        # Format values based on type
        if all(isinstance(v, str) for v in values):
            formatted_values = ', '.join([f'"{v}"' for v in values])
        else:
            formatted_values = ', '.join([str(v) for v in values])
        
        if operator == "isAnyOf":
            expression = f"{input_ref} in {{{formatted_values}}}"
            explanation = f"Value must be one of: {values}"
        elif operator == "isNoneOf":
            expression = f"not {input_ref} in {{{formatted_values}}}"
            explanation = f"Value must not be any of: {values}"
        elif operator == "isAllOf":
            # More complex - need to check all values are present
            expression = f"count([v | v := {input_ref}[_]; v in {{{formatted_values}}}]) == {len(values)}"
            explanation = f"Must contain all of: {values}"
        else:
            expression = f"{input_ref} in {{{formatted_values}}}"
            explanation = f"Set membership check"
        
        return {
            "rego_expression": expression,
            "explanation": explanation,
            "type": "set_membership"
        }
    
    def _generate_hierarchical_expression(self, input_ref: str, operator: str, value: str) -> Dict[str, str]:
        """Generate expression for hierarchical data"""
        
        if operator in ["isA", "isPartOf"]:
            # Use prefix matching for hierarchical
            expression = f'startswith({input_ref}, "{value}")'
            explanation = f"Hierarchical: must be under {value}"
        else:
            expression = f'{input_ref} == "{value}"'
            explanation = f"Exact hierarchical match: {value}"
        
        return {
            "rego_expression": expression,
            "explanation": explanation,
            "type": "hierarchical"
        }
    
    def _generate_pattern_expression(self, input_ref: str, operator: str, pattern: str) -> Dict[str, str]:
        """Generate expression for pattern matching"""
        
        # Escape special characters in pattern
        escaped_pattern = pattern.replace('\\', '\\\\').replace('"', '\\"')
        
        expression = f'regex.match("{escaped_pattern}", {input_ref})'
        
        return {
            "rego_expression": expression,
            "explanation": f"Pattern match: {pattern}",
            "type": "pattern"
        }
    
    def _generate_email_expression(self, input_ref: str, operator: str, email: str) -> Dict[str, str]:
        """Generate expression for email validation/comparison"""
        
        if operator == "eq":
            expression = f'{input_ref} == "{email}"'
            explanation = f"Email must be: {email}"
        else:
            # Email domain check
            domain = email.split('@')[1] if '@' in email else email
            expression = f'endswith({input_ref}, "@{domain}")'
            explanation = f"Email domain check: {domain}"
        
        return {
            "rego_expression": expression,
            "explanation": explanation,
            "type": "email"
        }
    
    def _generate_uri_expression(self, input_ref: str, operator: str, uri: str) -> Dict[str, str]:
        """Generate expression for URI comparison"""
        
        if operator in ["hasPart", "isPartOf"]:
            expression = f'startswith({input_ref}, "{uri}")'
            explanation = f"URI must start with: {uri}"
        else:
            expression = f'{input_ref} == "{uri}"'
            explanation = f"URI must be: {uri}"
        
        return {
            "rego_expression": expression,
            "explanation": explanation,
            "type": "uri"
        }
    
    def _generate_string_expression(self, input_ref: str, operator: str, value: str) -> Dict[str, str]:
        """Generate expression for string comparison"""
        
        rego_op = self._map_operator(operator)
        expression = f'{input_ref} {rego_op} "{value}"'
        
        return {
            "rego_expression": expression,
            "explanation": f"String comparison: {operator} {value}",
            "type": "string"
        }
    
    def _map_operator(self, odrl_operator: str) -> str:
        """Map ODRL operator to Rego operator"""
        mapping = {
            "eq": "==",
            "neq": "!=",
            "lt": "<",
            "gt": ">",
            "lteq": "<=",
            "gteq": ">=",
            "isAnyOf": "in",
            "isA": "==",
            "hasPart": "in",
            "isPartOf": "in"
        }
        return mapping.get(odrl_operator, "==")


# Singleton instance
_type_inference_engine = None

def get_type_inference_engine() -> TypeInferenceEngine:
    """Get or create the type inference engine singleton"""
    global _type_inference_engine
    if _type_inference_engine is None:
        _type_inference_engine = TypeInferenceEngine()
    return _type_inference_engine