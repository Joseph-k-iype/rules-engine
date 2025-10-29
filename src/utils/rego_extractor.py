"""
Rego Code Extraction and Validation Utilities
Extracts ONLY valid Rego code from agent responses
"""
import re
from typing import Optional, Dict, Any, List


class RegoExtractor:
    """
    Extracts clean Rego code from agent responses that may contain
    explanations, reasoning, markdown formatting, etc.
    """
    
    # Rego keywords that must appear in valid Rego code
    REGO_KEYWORDS = [
        'package', 'import', 'if', 'else', 'contains', 'default',
        'allow', 'deny', 'not', 'some', 'every', 'in', 'as'
    ]
    
    # Lines that indicate reasoning/explanation (not Rego code)
    EXPLANATION_PATTERNS = [
        r'^(Step|First|Second|Third|Finally|Now|Next|Then|Here|This|The|Let me|I will|We|You)',
        r'^(Analysis|Reasoning|Explanation|Note|Example|Summary):',
        r'^\d+\.',  # Numbered lists
        r'^[-*•]',  # Bullet points
        r'(analyze|generate|create|implement|consider|ensure)',
        r'(should|must|will|can|need to|going to)',
    ]
    
    @staticmethod
    def extract_rego_code(text: str) -> str:
        """
        Extract ONLY valid Rego code from agent response.
        
        Handles:
        - Markdown code blocks
        - Mixed explanation and code
        - Extra whitespace
        - Reasoning chains
        
        Args:
            text: Agent response that may contain Rego code
            
        Returns:
            Clean Rego code string
        """
        if not text or not text.strip():
            return ""
        
        # Strategy 1: Try to extract from markdown code blocks
        rego_from_markdown = RegoExtractor._extract_from_markdown(text)
        if rego_from_markdown and RegoExtractor._is_valid_rego(rego_from_markdown):
            return rego_from_markdown
        
        # Strategy 2: Try to extract from plain text
        rego_from_text = RegoExtractor._extract_from_plain_text(text)
        if rego_from_text and RegoExtractor._is_valid_rego(rego_from_text):
            return rego_from_text
        
        # Strategy 3: Filter out explanation lines
        rego_filtered = RegoExtractor._filter_explanation_lines(text)
        if rego_filtered and RegoExtractor._is_valid_rego(rego_filtered):
            return rego_filtered
        
        # If all strategies fail, return the cleaned text
        return text.strip()
    
    @staticmethod
    def _extract_from_markdown(text: str) -> str:
        """Extract code from markdown code blocks."""
        # Try ```rego blocks first
        rego_pattern = r'```rego\s*\n(.*?)```'
        matches = re.findall(rego_pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            # Return the largest block (most likely the complete code)
            return max(matches, key=len).strip()
        
        # Try generic ``` blocks
        code_pattern = r'```\s*\n(.*?)```'
        matches = re.findall(code_pattern, text, re.DOTALL)
        if matches:
            # Filter to find blocks that look like Rego
            for match in matches:
                if 'package ' in match or 'import rego' in match:
                    return match.strip()
        
        return ""
    
    @staticmethod
    def _extract_from_plain_text(text: str) -> str:
        """Extract Rego code from plain text by finding package declaration."""
        lines = text.split('\n')
        
        # Find the first line with 'package '
        start_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('package '):
                start_idx = i
                break
        
        if start_idx == -1:
            return ""
        
        # Take everything from package declaration onwards
        # but stop if we hit clear explanation text
        rego_lines = []
        for line in lines[start_idx:]:
            # Stop if we hit explanation patterns
            is_explanation = False
            for pattern in RegoExtractor.EXPLANATION_PATTERNS:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    is_explanation = True
                    break
            
            if is_explanation and rego_lines:
                # Stop collecting if we already have some Rego code
                break
            
            if not is_explanation:
                rego_lines.append(line)
        
        return '\n'.join(rego_lines).strip()
    
    @staticmethod
    def _filter_explanation_lines(text: str) -> str:
        """Filter out lines that are clearly explanations, not code."""
        lines = text.split('\n')
        rego_lines = []
        
        in_code_block = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines initially, but keep them in code blocks
            if not stripped and not in_code_block:
                continue
            
            # Detect start of code block
            if stripped.startswith('package '):
                in_code_block = True
            
            # If in code block, keep all lines unless they're clear explanations
            if in_code_block:
                is_explanation = False
                for pattern in RegoExtractor.EXPLANATION_PATTERNS:
                    if re.match(pattern, stripped, re.IGNORECASE):
                        is_explanation = True
                        break
                
                if not is_explanation:
                    rego_lines.append(line)
            # If not in code block yet, check if line looks like code
            else:
                # Check if line contains Rego syntax
                if any(keyword in stripped for keyword in RegoExtractor.REGO_KEYWORDS):
                    rego_lines.append(line)
                    in_code_block = True
        
        return '\n'.join(rego_lines).strip()
    
    @staticmethod
    def _is_valid_rego(code: str) -> bool:
        """
        Check if extracted code looks like valid Rego.
        
        Valid Rego must have:
        - A package declaration
        - At least one of: import, rule definition, or constraint
        """
        if not code:
            return False
        
        lines = code.split('\n')
        non_empty_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith('#')]
        
        # Must have at least 2 non-empty, non-comment lines
        if len(non_empty_lines) < 2:
            return False
        
        # Must start with package declaration
        if not non_empty_lines[0].startswith('package '):
            return False
        
        # Must contain at least one rule or import
        has_import = any('import ' in line for line in non_empty_lines)
        has_rule = any(' if {' in line or ' if{' in line or ' := ' in line or ' = ' in line 
                      for line in non_empty_lines)
        
        return has_import or has_rule


class RegoValidator:
    """
    Validates Rego code syntax and common errors.
    """
    
    @staticmethod
    def validate_syntax(rego_code: str) -> Dict[str, Any]:
        """
        Validate Rego code for common syntax errors.
        
        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        errors = []
        warnings = []
        
        if not rego_code or not rego_code.strip():
            return {
                'valid': False,
                'errors': ['Empty Rego code'],
                'warnings': []
            }
        
        lines = rego_code.split('\n')
        
        # Check for package declaration
        has_package = any(line.strip().startswith('package ') for line in lines)
        if not has_package:
            errors.append("Missing package declaration")
        
        # Check for import rego.v1
        has_rego_import = any('import rego.v1' in line for line in lines)
        if not has_rego_import:
            warnings.append("Missing 'import rego.v1' - required for Rego v1 syntax")
        
        # Check for rules without 'if' keyword
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('#'):
                continue
            
            # Check for rule definitions
            if '{' in stripped and not stripped.startswith('package') and not stripped.startswith('import'):
                # This might be a rule
                if 'if' not in line and ' := ' not in line:
                    # Check if this is a multi-value rule (should use 'if' and 'contains')
                    if '[' in line and ']' in line:
                        # Rule like: allow[msg] { ... } should be allow contains msg if { ... }
                        warnings.append(f"Line {i}: Rule may need 'if' keyword and 'contains' for Rego v1")
                    elif ' {' in line or ' {' in line:
                        # Rule without if keyword
                        warnings.append(f"Line {i}: Rule should use 'if' keyword in Rego v1")
        
        # Check for URN/URI usage (should use clean identifiers)
        for i, line in enumerate(lines, 1):
            if 'urn:' in line.lower() or 'http://' in line or 'https://' in line:
                if not line.strip().startswith('#'):
                    warnings.append(f"Line {i}: Contains URN/URI - consider using clean identifiers")
        
        # Check for quoted numbers (common type error)
        for i, line in enumerate(lines, 1):
            # Look for patterns like input.age >= "18" or input.count == "100"
            if re.search(r'(>=|<=|>|<|==|!=)\s*["\'](\d+)["\']', line):
                errors.append(f"Line {i}: Number should not be quoted")
        
        # Check for string booleans (should be true/false, not "true"/"false")
        for i, line in enumerate(lines, 1):
            if re.search(r'(==|!=)\s*["\'](?:true|false)["\']', line, re.IGNORECASE):
                if 'string' not in line.lower() and 'text' not in line.lower():
                    errors.append(f"Line {i}: Boolean should not be quoted")
        
        # Check for array syntax in 'in' operator (should use sets)
        for i, line in enumerate(lines, 1):
            if ' in [' in line:
                warnings.append(f"Line {i}: Consider using set syntax {{}} instead of array [] with 'in' operator")
        
        # Check for unclosed braces
        open_braces = rego_code.count('{')
        close_braces = rego_code.count('}')
        if open_braces != close_braces:
            errors.append(f"Mismatched braces: {open_braces} open, {close_braces} close")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def format_validation_report(validation_result: Dict[str, Any]) -> str:
        """Format validation result as readable report."""
        lines = []
        
        if validation_result['valid']:
            lines.append("✓ VALIDATION PASSED")
        else:
            lines.append("✗ VALIDATION FAILED")
        
        if validation_result['errors']:
            lines.append(f"\nErrors ({len(validation_result['errors'])}):")
            for error in validation_result['errors']:
                lines.append(f"  ✗ {error}")
        
        if validation_result['warnings']:
            lines.append(f"\nWarnings ({len(validation_result['warnings'])}):")
            for warning in validation_result['warnings']:
                lines.append(f"  ⚠ {warning}")
        
        if validation_result['valid'] and not validation_result['warnings']:
            lines.append("\nNo issues found. Code appears syntactically correct.")
        
        return '\n'.join(lines)


def extract_and_validate_rego(agent_response: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Extract Rego code from agent response and validate it.
    
    Args:
        agent_response: Raw agent response (may contain explanations)
        verbose: If True, print detailed extraction info
        
    Returns:
        Dict with 'rego_code', 'extracted_successfully', 'validation_result'
    """
    # Extract
    rego_code = RegoExtractor.extract_rego_code(agent_response)
    
    if verbose:
        print("\n" + "="*80)
        print("REGO EXTRACTION")
        print("="*80)
        print(f"Original length: {len(agent_response)} chars")
        print(f"Extracted length: {len(rego_code)} chars")
        print(f"Extraction successful: {len(rego_code) > 0}")
    
    # Validate
    validation = RegoValidator.validate_syntax(rego_code)
    
    if verbose:
        print("\n" + "="*80)
        print("REGO VALIDATION")
        print("="*80)
        print(RegoValidator.format_validation_report(validation))
        print("="*80)
    
    return {
        'rego_code': rego_code,
        'extracted_successfully': len(rego_code) > 0 and RegoExtractor._is_valid_rego(rego_code),
        'validation_result': validation
    }


# Example usage
if __name__ == "__main__":
    # Test with sample agent response containing explanations
    sample_response = """
Let me generate the Rego code step by step.

First, I'll analyze the policy structure...
The policy has permissions for UK jurisdiction.

Here's the generated code:

```rego
package policy_sar_uar_uk

import rego.v1

# SAR/UAR Data Sharing - UK
allow_share_sar_uar_uk if {
    input.action == "share"
    input.jurisdiction == "UK"
    input.requestor_type in {"UK National Crime Agency", "Credit Institution"}
}

deny contains msg if {
    input.action == "share"
    input.jurisdiction == "UK"
    not input.requestor_type in {"UK National Crime Agency", "Credit Institution"}
    msg := "Unauthorized requestor"
}
```

This code implements the policy requirements by...
    """
    
    result = extract_and_validate_rego(sample_response, verbose=True)
    
    print("\n" + "="*80)
    print("EXTRACTED REGO CODE")
    print("="*80)
    print(result['rego_code'])
    print("="*80)