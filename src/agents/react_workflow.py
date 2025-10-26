"""
ReAct Agent Workflow for ODRL to Rego Conversion
Uses LangGraph's create_react_agent with custom tools
Integrates with existing config.py for LLM configuration
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

# Import tools and prompts
from .react_tools import (
    extract_policy_metadata,
    extract_permissions,
    extract_prohibitions,
    extract_constraints,
    analyze_rdfs_comments,
    analyze_operator,
    analyze_rightOperand,
    suggest_rego_pattern,
    check_rego_syntax,
    fix_missing_if
)

from ..prompting.odrl_rego_strategies import (
    ODRL_PARSER_REACT_PROMPT,
    TYPE_INFERENCE_REACT_PROMPT,
    LOGIC_ANALYZER_REACT_PROMPT,
    REGO_GENERATOR_REACT_PROMPT,
    REFLECTION_REACT_PROMPT,
    CORRECTION_REACT_PROMPT
)


# ============================================================================
# Configuration
# ============================================================================

def get_llm_for_agent():
    """
    Get LLM instance using existing config.py settings
    """
    return ChatOpenAI(model=OPENAI_MODEL)


# ============================================================================
# ReAct Agent Creators
# ============================================================================

def create_odrl_parser_agent():
    """
    Create ReAct agent for ODRL parsing with deep semantic understanding.
    """
    llm = get_llm_for_agent()
    
    tools = [
        extract_policy_metadata,
        extract_permissions,
        extract_prohibitions,
        extract_constraints,
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
    Create ReAct agent for type inference from ODRL constraints.
    """
    llm = get_llm_for_agent()
    
    tools = [
        analyze_operator,
        analyze_rightOperand,
        suggest_rego_pattern,
        extract_constraints,
        analyze_rdfs_comments
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
    Create ReAct agent for generating Rego v1 code.
    """
    llm = get_llm_for_agent()
    
    tools = [
        suggest_rego_pattern,
        analyze_operator,
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
    Create ReAct agent for validating generated Rego code.
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
    Create ReAct agent for fixing issues in Rego code.
    """
    llm = get_llm_for_agent()
    
    tools = [
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
# Orchestrated Workflow
# ============================================================================

def convert_odrl_to_rego_react(
    odrl_json: Dict[str, Any],
    existing_rego: str = None,
    max_corrections: int = 3
) -> Dict[str, Any]:
    """
    Complete ODRL to Rego conversion using ReAct agents.
    
    This orchestrates multiple ReAct agents in sequence:
    1. Parser agent analyzes ODRL
    2. Type inference agent determines data types
    3. Generator agent creates Rego code
    4. Reflection agent validates code
    5. Correction agent fixes issues (if needed)
    
    Args:
        odrl_json: ODRL policy in JSON-LD format
        existing_rego: Existing Rego code to append to (optional)
        max_corrections: Maximum correction attempts
        
    Returns:
        Dictionary with conversion results
    """
    
    results = {
        "success": False,
        "generated_rego": "",
        "policy_id": "",
        "messages": [],
        "reasoning_chain": [],
        "logical_issues": [],
        "correction_attempts": 0,
        "error_message": None,
        "stage_reached": "initialization"
    }
    
    try:
        odrl_str = json.dumps(odrl_json, indent=2)
        
        # ========================================================================
        # STAGE 1: Parse ODRL with ReAct Agent
        # ========================================================================
        results["messages"].append("Stage 1: Parsing ODRL with ReAct agent...")
        results["stage_reached"] = "parsing"
        
        parser_agent = create_odrl_parser_agent()
        
        parser_config = {"configurable": {"thread_id": "odrl-parser"}}
        parser_input = {
            "messages": [
                HumanMessage(content=f"""
Analyze this ODRL policy and extract all components:

{odrl_str}

Use your tools systematically to:
1. Extract policy metadata
2. Extract all permissions
3. Extract all prohibitions  
4. Analyze all constraints
5. Analyze RDFS comments for context

Provide a comprehensive analysis with reasoning.
                """)
            ]
        }
        
        parser_response = parser_agent.invoke(parser_input, parser_config)
        parser_result = parser_response["messages"][-1].content
        
        results["reasoning_chain"].append({
            "stage": "parsing",
            "reasoning": parser_result
        })
        
        # Extract policy ID from the analysis
        metadata_result = extract_policy_metadata(odrl_str)
        results["policy_id"] = metadata_result.get("policy_id", "unknown")
        results["messages"].append(f"Parsed policy: {results['policy_id']}")
        
        # ========================================================================
        # STAGE 2: Type Inference with ReAct Agent
        # ========================================================================
        results["messages"].append("Stage 2: Inferring types with ReAct agent...")
        results["stage_reached"] = "type_inference"
        
        type_agent = create_type_inference_agent()
        
        type_config = {"configurable": {"thread_id": "type-inference"}}
        type_input = {
            "messages": [
                HumanMessage(content=f"""
Infer Rego data types for all constraints in this ODRL policy:

{odrl_str}

ODRL Parser's Analysis:
{parser_result}

Use your tools to:
1. Analyze each constraint's operator
2. Analyze each rightOperand value
3. Generate Rego patterns for each constraint
4. Consider RDFS comments for type hints

Provide detailed type inference results with reasoning.
                """)
            ]
        }
        
        type_response = type_agent.invoke(type_input, type_config)
        type_result = type_response["messages"][-1].content
        
        results["reasoning_chain"].append({
            "stage": "type_inference",
            "reasoning": type_result
        })
        results["messages"].append("Type inference complete")
        
        # ========================================================================
        # STAGE 3: Generate Rego with ReAct Agent
        # ========================================================================
        results["messages"].append("Stage 3: Generating Rego code with ReAct agent...")
        results["stage_reached"] = "generation"
        
        generator_agent = create_rego_generator_agent()
        
        existing_rego_prompt = ""
        if existing_rego:
            existing_rego_prompt = f"""
            
EXISTING REGO TO APPEND TO:
```rego
{existing_rego}
```

Your generated code must:
- Not conflict with existing rules
- Follow the same style
- Be properly appended
            """
        
        gen_config = {"configurable": {"thread_id": "rego-generator"}}
        gen_input = {
            "messages": [
                HumanMessage(content=f"""
Generate OPA Rego v1 code for this ODRL policy:

ODRL Policy:
{odrl_str}

ODRL Analysis:
{parser_result}

Type Inference:
{type_result}

{existing_rego_prompt}

Use your tools to:
1. Generate Rego patterns for each constraint
2. Create permission rules
3. Create prohibition rules
4. Validate syntax as you go

Generate complete, syntactically correct Rego v1 code.
CRITICAL: Include 'import rego.v1' and use 'if' keywords.

Return ONLY the Rego code, no markdown formatting.
                """)
            ]
        }
        
        gen_response = generator_agent.invoke(gen_input, gen_config)
        rego_code = gen_response["messages"][-1].content
        
        # Clean markdown fences if present
        if "```" in rego_code:
            lines = rego_code.split('\n')
            rego_code = '\n'.join(
                line for line in lines 
                if not line.strip().startswith('```')
            )
        
        results["generated_rego"] = rego_code.strip()
        results["messages"].append(f"Generated Rego code ({len(rego_code)} characters)")
        
        # ========================================================================
        # STAGE 4: Validate with Reflection Agent
        # ========================================================================
        results["messages"].append("Stage 4: Validating Rego code...")
        results["stage_reached"] = "validation"
        
        reflection_agent = create_reflection_agent()
        
        refl_config = {"configurable": {"thread_id": "reflection"}}
        refl_input = {
            "messages": [
                HumanMessage(content=f"""
Validate this generated Rego code:

```rego
{results['generated_rego']}
```

Original ODRL Policy:
{odrl_str}

Use your tools to:
1. Check Rego v1 syntax compliance
2. Verify all ODRL rules are implemented
3. Check for logical consistency
4. Identify any issues

Provide comprehensive validation results in JSON format.
                """)
            ]
        }
        
        refl_response = reflection_agent.invoke(refl_input, refl_config)
        validation_result = refl_response["messages"][-1].content
        
        results["reasoning_chain"].append({
            "stage": "validation",
            "reasoning": validation_result
        })
        
        # Try to parse validation as JSON
        try:
            # Extract JSON from response if wrapped in markdown
            if "```json" in validation_result:
                json_start = validation_result.find("```json") + 7
                json_end = validation_result.find("```", json_start)
                validation_json = json.loads(validation_result[json_start:json_end])
            elif "{" in validation_result:
                # Find JSON object
                start = validation_result.find("{")
                end = validation_result.rfind("}") + 1
                validation_json = json.loads(validation_result[start:end])
            else:
                validation_json = {"is_valid": "pass" in validation_result.lower()}
        except:
            validation_json = {"is_valid": "error" not in validation_result.lower()}
        
        is_valid = validation_json.get("is_valid", True)
        
        # ========================================================================
        # STAGE 5: Correction Loop (if needed)
        # ========================================================================
        correction_attempts = 0
        
        while not is_valid and correction_attempts < max_corrections:
            correction_attempts += 1
            results["correction_attempts"] = correction_attempts
            results["messages"].append(f"Stage 5: Correction attempt {correction_attempts}/{max_corrections}...")
            results["stage_reached"] = "correction"
            
            correction_agent = create_correction_agent()
            
            corr_config = {"configurable": {"thread_id": f"correction-{correction_attempts}"}}
            corr_input = {
                "messages": [
                    HumanMessage(content=f"""
Fix the issues in this Rego code:

```rego
{results['generated_rego']}
```

Validation Feedback:
{validation_result}

Use your tools to:
1. Check what specific syntax issues exist
2. Fix missing 'if' keywords
3. Fix any other issues
4. Validate the corrected code

Return the corrected Rego code in JSON format:
{{"corrected_code": "...", "changes": ["..."]}}
                    """)
                ]
            }
            
            corr_response = correction_agent.invoke(corr_input, corr_config)
            correction_result = corr_response["messages"][-1].content
            
            # Extract corrected code
            try:
                if "```json" in correction_result:
                    json_start = correction_result.find("```json") + 7
                    json_end = correction_result.find("```", json_start)
                    correction_json = json.loads(correction_result[json_start:json_end])
                elif "{" in correction_result:
                    start = correction_result.find("{")
                    end = correction_result.rfind("}") + 1
                    correction_json = json.loads(correction_result[start:end])
                else:
                    correction_json = {"corrected_code": results["generated_rego"]}
                
                results["generated_rego"] = correction_json.get("corrected_code", results["generated_rego"])
                results["messages"].append(f"Applied corrections (attempt {correction_attempts})")
                
            except:
                results["messages"].append(f"Could not parse correction result")
                break
            
            # Re-validate
            refl_input["messages"][0].content = f"""
Validate this corrected Rego code:

```rego
{results['generated_rego']}
```

Use your tools to check if issues are resolved.
            """
            
            refl_response = reflection_agent.invoke(refl_input, refl_config)
            validation_result = refl_response["messages"][-1].content
            
            try:
                if "```json" in validation_result:
                    json_start = validation_result.find("```json") + 7
                    json_end = validation_result.find("```", json_start)
                    validation_json = json.loads(validation_result[json_start:json_end])
                else:
                    start = validation_result.find("{")
                    end = validation_result.rfind("}") + 1
                    validation_json = json.loads(validation_result[start:end])
                
                is_valid = validation_json.get("is_valid", False)
            except:
                is_valid = "error" not in validation_result.lower()
            
            if is_valid:
                results["messages"].append("✓ Validation passed after correction")
                break
        
        # ========================================================================
        # Final Status
        # ========================================================================
        results["success"] = is_valid
        if is_valid:
            results["stage_reached"] = "completed"
            results["messages"].append("✓ ODRL to Rego conversion successful!")
        else:
            results["stage_reached"] = "validation_failed"
            results["error_message"] = f"Validation failed after {max_corrections} correction attempts"
            results["messages"].append(f"✗ Conversion failed: {results['error_message']}")
        
    except Exception as e:
        results["error_message"] = f"Conversion error: {str(e)}"
        results["messages"].append(f"ERROR: {str(e)}")
        results["stage_reached"] = "failed"
    
    return results


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
    Convert ODRL file to Rego file using ReAct agents.
    
    Args:
        input_file: Path to ODRL JSON file
        output_file: Path for output Rego file (optional)
        existing_rego_file: Path to existing Rego to append to (optional)
        max_corrections: Maximum correction attempts
        
    Returns:
        Conversion results
    """
    # Load ODRL
    with open(input_file, 'r') as f:
        odrl_json = json.load(f)
    
    # Load existing Rego if provided
    existing_rego = None
    if existing_rego_file:
        with open(existing_rego_file, 'r') as f:
            existing_rego = f.read()
    
    # Convert
    result = convert_odrl_to_rego_react(odrl_json, existing_rego, max_corrections)
    
    # Save if successful
    if result["success"] and output_file:
        with open(output_file, 'w') as f:
            f.write(result["generated_rego"])
        result["output_file"] = output_file
    
    return result