"""
ReAct Agent Workflow with Intelligent Type Inference
Uses sophisticated type analysis to generate properly typed Rego code
"""
import json
import os
import sys
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import OPENAI_MODEL

# Import type-aware tools
from .react_tools import (
    extract_policy_metadata,
    extract_and_infer_constraints,
    infer_constraint_type,
    generate_typed_rego_pattern,
    generate_complete_typed_rule,
    generate_type_inference_report,
    analyze_rdfs_comments,
    check_rego_syntax,
    fix_missing_if
)

from ..prompting.odrl_rego_strategies import (
    ODRL_PARSER_REACT_PROMPT,
    TYPE_INFERENCE_REACT_PROMPT,
    REGO_GENERATOR_REACT_PROMPT,
    REFLECTION_REACT_PROMPT,
    CORRECTION_REACT_PROMPT
)


# ============================================================================
# Configuration
# ============================================================================

def get_llm_for_agent():
    """Get LLM instance using existing config.py settings"""
    return ChatOpenAI(model=OPENAI_MODEL, temperature=0)


# ============================================================================
# ReAct Agent Creators (Type-Aware)
# ============================================================================

def create_odrl_parser_agent():
    """
    Create ReAct agent for ODRL parsing with type inference.
    """
    llm = get_llm_for_agent()
    
    tools = [
        extract_policy_metadata,
        extract_and_infer_constraints,  # Main tool - extracts + infers types
        generate_type_inference_report,  # Overview of types
        analyze_rdfs_comments
    ]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=ODRL_PARSER_REACT_PROMPT,
        checkpointer=checkpointer
    )
    
    return agent


def create_type_inference_agent():
    """
    Create ReAct agent specialized in type inference and pattern generation.
    """
    llm = get_llm_for_agent()
    
    tools = [
        extract_and_infer_constraints,
        infer_constraint_type,  # Analyze specific constraint types
        generate_typed_rego_pattern,  # Generate type-aware patterns
        generate_type_inference_report
    ]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=TYPE_INFERENCE_REACT_PROMPT,
        checkpointer=checkpointer
    )
    
    return agent


def create_rego_generator_agent():
    """
    Create ReAct agent for generating type-aware Rego v1 code.
    """
    llm = get_llm_for_agent()
    
    tools = [
        extract_and_infer_constraints,
        generate_typed_rego_pattern,
        generate_complete_typed_rule,  # Main tool - generates typed rules
        check_rego_syntax
    ]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=REGO_GENERATOR_REACT_PROMPT,
        checkpointer=checkpointer
    )
    
    return agent


def create_reflection_agent():
    """
    Create ReAct agent for validating type correctness in generated Rego.
    """
    llm = get_llm_for_agent()
    
    tools = [
        check_rego_syntax
    ]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=REFLECTION_REACT_PROMPT,
        checkpointer=checkpointer
    )
    
    return agent


def create_correction_agent():
    """
    Create ReAct agent for fixing type errors in Rego code.
    """
    llm = get_llm_for_agent()
    
    tools = [
        generate_typed_rego_pattern,
        generate_complete_typed_rule,
        check_rego_syntax,
        fix_missing_if
    ]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=CORRECTION_REACT_PROMPT,
        checkpointer=checkpointer
    )
    
    return agent


# ============================================================================
# Orchestrated Workflow with Type Inference
# ============================================================================

def convert_odrl_to_rego_react(
    odrl_json: Dict[str, Any],
    existing_rego: str = None,
    max_corrections: int = 3
) -> Dict[str, Any]:
    """
    Complete ODRL to Rego conversion with intelligent type inference.
    
    This workflow:
    1. Extracts constraints and infers their data types
    2. Generates type-appropriate Rego patterns
    3. Creates complete rules with correct type handling
    4. Validates type correctness
    5. Fixes any type mismatches
    
    Args:
        odrl_json: ODRL policy in JSON-LD format
        existing_rego: Existing Rego code to append to (optional)
        max_corrections: Maximum correction attempts
        
    Returns:
        Dictionary with conversion results including type inference report
    """
    
    results = {
        "success": False,
        "generated_rego": "",
        "policy_id": "",
        "messages": [],
        "reasoning_chain": [],
        "type_inference_report": {},
        "types_detected": [],
        "logical_issues": [],
        "correction_attempts": 0,
        "error_message": None,
        "stage_reached": "initialization"
    }
    
    try:
        odrl_str = json.dumps(odrl_json, indent=2)
        
        # ========================================================================
        # STAGE 1: Parse ODRL and Infer Constraint Types
        # ========================================================================
        results["messages"].append("Stage 1: Parsing ODRL with intelligent type inference...")
        results["stage_reached"] = "parsing_with_type_inference"
        
        parser_agent = create_odrl_parser_agent()
        
        parser_config = {"configurable": {"thread_id": "odrl-parser-typed"}}
        parser_input = {
            "messages": [
                HumanMessage(content=f"""
Analyze this ODRL policy and infer the data types of all constraints:

{odrl_str}

CRITICAL: Use intelligent type inference!

1. Use `extract_and_infer_constraints` to get ALL constraints with inferred types
2. Use `generate_type_inference_report` for an overview
3. For each constraint, report:
   - The actual value
   - The INFERRED TYPE (datetime, number, string, set, hierarchical, etc.)
   - Why that type was inferred
   - What Rego operators/functions should be used

Example analysis:
"Constraint: dateTime < '2025-12-31T23:59:59Z'
 Inferred Type: datetime (detected ISO 8601 format)
 Rego Pattern: time.now_ns() < time.parse_rfc3339_ns('2025-12-31T23:59:59Z')
 
 Constraint: role isAnyOf ['data_controller', 'dpo']
 Inferred Type: set_string (list of strings)
 Rego Pattern: input.role in {{'data_controller', 'dpo'}}"
                """)
            ]
        }
        
        parser_response = parser_agent.invoke(parser_input, parser_config)
        parser_result = parser_response["messages"][-1].content
        
        results["reasoning_chain"].append({
            "stage": "parsing_with_type_inference",
            "reasoning": parser_result
        })
        
        # Extract metadata
        metadata_result = extract_policy_metadata(odrl_str)
        results["policy_id"] = metadata_result.get("policy_id", "unknown")
        
        # Get type inference report
        type_report = generate_type_inference_report(odrl_str)
        results["type_inference_report"] = type_report
        results["types_detected"] = type_report.get("types_found", [])
        
        results["messages"].append(f"Parsed policy: {results['policy_id']}")
        results["messages"].append(f"Types detected: {', '.join(results['types_detected'])}")
        
        # ========================================================================
        # STAGE 2: Generate Type-Aware Rego Patterns
        # ========================================================================
        results["messages"].append("Stage 2: Generating type-aware Rego patterns...")
        results["stage_reached"] = "type_aware_pattern_generation"
        
        type_agent = create_type_inference_agent()
        
        type_config = {"configurable": {"thread_id": "type-inference"}}
        type_input = {
            "messages": [
                HumanMessage(content=f"""
Generate type-appropriate Rego patterns for each constraint:

ODRL Policy:
{odrl_str}

Parser found these types:
{parser_result}

Type Distribution:
{json.dumps(results['type_inference_report'].get('type_counts', {{}}), indent=2)}

CRITICAL INSTRUCTIONS:
1. For EACH constraint, use `generate_typed_rego_pattern` to get the correct pattern
2. Use TYPE-APPROPRIATE Rego operators:
   - Temporal (datetime, date): time.parse_rfc3339_ns(), time.now_ns(), <, >
   - Numeric (int, float): Direct comparison <, >, ==, >=, <=
   - Set (list of values): input.field in {{"value1", "value2"}}
   - Hierarchical: startswith(input.field, "prefix")
   - String: == or contains() or startswith()
   - Pattern: regex.match()

3. NEVER treat non-strings as strings!
   ❌ Wrong: input.age == "18"
   ✅ Right: input.age >= 18

Generate patterns with correct type handling!
                """)
            ]
        }
        
        type_response = type_agent.invoke(type_input, type_config)
        type_result = type_response["messages"][-1].content
        
        results["reasoning_chain"].append({
            "stage": "type_aware_patterns",
            "reasoning": type_result
        })
        results["messages"].append("Generated type-aware patterns for all constraints")
        
        # ========================================================================
        # STAGE 3: Generate Complete Typed Rego Code
        # ========================================================================
        results["messages"].append("Stage 3: Generating complete Rego code with type handling...")
        results["stage_reached"] = "typed_code_generation"
        
        generator_agent = create_rego_generator_agent()
        
        existing_rego_prompt = ""
        if existing_rego:
            existing_rego_prompt = f"""
            
EXISTING REGO TO APPEND TO:
```rego
{existing_rego}
```
            """
        
        gen_config = {"configurable": {"thread_id": "rego-generator-typed"}}
        gen_input = {
            "messages": [
                HumanMessage(content=f"""
Generate complete OPA Rego v1 code with PROPER TYPE HANDLING:

ODRL Policy:
{odrl_str}

Type Analysis:
{type_result}

Types in Policy:
{json.dumps(results['types_detected'])}

{existing_rego_prompt}

CRITICAL REQUIREMENTS:
1. Use `generate_complete_typed_rule` for each permission/prohibition
2. Each constraint must use TYPE-APPROPRIATE operators:
   - Temporal constraints: Use time.* functions
   - Numeric constraints: Use numeric operators
   - Set constraints: Use 'in' with proper set syntax
   - Hierarchical: Use startswith() when appropriate

3. EXAMPLES OF CORRECT TYPE USAGE:
   ✅ time.now_ns() < time.parse_rfc3339_ns("2025-12-31T23:59:59Z")  # temporal
   ✅ input.age >= 18  # numeric
   ✅ input.role in {{"data_controller", "dpo"}}  # set
   ✅ startswith(input.category, "personal:contact")  # hierarchical

4. Include 'import rego.v1' and use 'if' keywords
5. Validate with check_rego_syntax

Generate type-correct Rego code. Return ONLY the Rego code, no markdown.
                """)
            ]
        }
        
        gen_response = generator_agent.invoke(gen_input, gen_config)
        rego_code = gen_response["messages"][-1].content
        
        # Clean markdown fences
        if "```" in rego_code:
            lines = rego_code.split('\n')
            rego_code = '\n'.join(
                line for line in lines 
                if not line.strip().startswith('```')
            )
        
        results["generated_rego"] = rego_code.strip()
        results["messages"].append(f"Generated type-aware Rego code ({len(rego_code)} characters)")
        
        # ========================================================================
        # STAGE 4: Validate Type Correctness
        # ========================================================================
        results["messages"].append("Stage 4: Validating type correctness...")
        results["stage_reached"] = "type_validation"
        
        reflection_agent = create_reflection_agent()
        
        refl_config = {"configurable": {"thread_id": "reflection-typed"}}
        refl_input = {
            "messages": [
                HumanMessage(content=f"""
Validate this Rego code for TYPE CORRECTNESS:

```rego
{results['generated_rego']}
```

Original ODRL with Types:
{odrl_str}

Types Expected:
{json.dumps(results['types_detected'])}

CHECK FOR TYPE ERRORS:
1. Are temporal values using time.* functions? (not string comparison)
2. Are numeric values using numeric operators? (not quoted strings)
3. Are sets using 'in' with proper syntax?
4. Are hierarchical values using appropriate functions?

COMMON TYPE ERRORS:
❌ input.age == "18" (should be input.age >= 18)
❌ input.date == "2025-12-31" (should use time functions)
❌ input.role == "admin" || input.role == "user" (should use set: in {{"admin", "user"}})

Report validation results with focus on TYPE CORRECTNESS.
                """)
            ]
        }
        
        refl_response = reflection_agent.invoke(refl_input, refl_config)
        validation_result = refl_response["messages"][-1].content
        
        results["reasoning_chain"].append({
            "stage": "type_validation",
            "reasoning": validation_result
        })
        
        # Check if valid
        is_valid = _check_validation_result(validation_result)
        
        # ========================================================================
        # STAGE 5: Type Correction (if needed)
        # ========================================================================
        if not is_valid and max_corrections > 0:
            results["messages"].append(f"Stage 5: Correcting type errors (max {max_corrections})...")
            results["stage_reached"] = "type_correction"
            
            correction_agent = create_correction_agent()
            
            for attempt in range(max_corrections):
                results["correction_attempts"] += 1
                
                corr_config = {"configurable": {"thread_id": f"correction-typed-{attempt}"}}
                corr_input = {
                    "messages": [
                        HumanMessage(content=f"""
Fix TYPE ERRORS in this Rego code:

```rego
{results['generated_rego']}
```

Validation Issues:
{validation_result}

Expected Types:
{json.dumps(results['type_inference_report'], indent=2)}

CRITICAL FIXES NEEDED:
1. Use `generate_typed_rego_pattern` to regenerate patterns with correct types
2. Replace string comparisons with appropriate typed operators
3. Fix temporal, numeric, and set handling

Common Fixes:
- String → Numeric: "18" → 18, == → >=
- String → Temporal: "2025-12-31" → time.parse_rfc3339_ns()
- Multiple OR → Set: == "a" || == "b" → in {{"a", "b"}}

Return corrected Rego with PROPER TYPE HANDLING!
                        """)
                    ]
                }
                
                corr_response = correction_agent.invoke(corr_input, corr_config)
                corrected_code = corr_response["messages"][-1].content
                
                # Clean and update
                if "```" in corrected_code:
                    lines = corrected_code.split('\n')
                    corrected_code = '\n'.join(
                        line for line in lines 
                        if not line.strip().startswith('```')
                    )
                
                results["generated_rego"] = corrected_code.strip()
                results["messages"].append(f"Type correction attempt {attempt + 1}/{max_corrections}")
                
                # Re-validate
                refl_input["messages"][0] = HumanMessage(content=f"""
Validate this corrected Rego code for type correctness:

```rego
{results['generated_rego']}
```

Expected types: {json.dumps(results['types_detected'])}
                """)
                
                refl_response = reflection_agent.invoke(refl_input, refl_config)
                validation_result = refl_response["messages"][-1].content
                
                is_valid = _check_validation_result(validation_result)
                
                if is_valid:
                    results["messages"].append("✓ Type validation passed after correction")
                    break
        
        # ========================================================================
        # Final Status
        # ========================================================================
        results["success"] = is_valid
        if is_valid:
            results["stage_reached"] = "completed"
            results["messages"].append("✓ ODRL to typed Rego conversion successful!")
        else:
            results["stage_reached"] = "validation_failed"
            results["error_message"] = f"Type validation failed after {max_corrections} attempts"
            results["messages"].append(f"✗ Conversion failed: {results['error_message']}")
        
    except Exception as e:
        results["error_message"] = f"Conversion error: {str(e)}"
        results["messages"].append(f"ERROR: {str(e)}")
        results["stage_reached"] = "failed"
        import traceback
        results["messages"].append(traceback.format_exc())
    
    return results
    
    def _check_validation_result(validation_text: str) -> bool:
        """Check if validation passed"""
        try:
            if "```json" in validation_text:
                json_start = validation_text.find("```json") + 7
                json_end = validation_text.find("```", json_start)
                validation_json = json.loads(validation_text[json_start:json_end])
                return validation_json.get("is_valid", False)
            else:
                return "valid" in validation_text.lower() and "invalid" not in validation_text.lower()
        except:
            return "valid" in validation_text.lower() and "error" not in validation_text.lower()


# Helper function for validation
def _check_validation_result(text: str) -> bool:
    return "valid" in text.lower() and "invalid" not in text.lower()


# ============================================================================
# Convenience Functions
# ============================================================================

def convert_odrl_file_to_rego(
    input_file: str,
    output_file: str = None,
    existing_rego_file: str = None,
    max_corrections: int = 3
) -> Dict[str, Any]:
    """
    Convert ODRL file to typed Rego file.
    
    Args:
        input_file: Path to ODRL JSON file
        output_file: Path for output Rego file (optional)
        existing_rego_file: Path to existing Rego to append to (optional)
        max_corrections: Maximum correction attempts
        
    Returns:
        Conversion results with type inference report
    """
    # Load ODRL
    with open(input_file, 'r') as f:
        odrl_json = json.load(f)
    
    # Load existing Rego if provided
    existing_rego = None
    if existing_rego_file and os.path.exists(existing_rego_file):
        with open(existing_rego_file, 'r') as f:
            existing_rego = f.read()
    
    # Convert with type inference
    result = convert_odrl_to_rego_react(odrl_json, existing_rego, max_corrections)
    
    # Save if successful
    if result["success"] and output_file:
        with open(output_file, 'w') as f:
            f.write(result["generated_rego"])
        result["output_file"] = output_file
    
    return result