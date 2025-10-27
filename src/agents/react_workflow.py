"""
Enhanced ReAct Workflow with Coverage-Based Rules, AST Validation, and Mixture of Experts
Uses OpenAI o3-mini reasoning model from config.py
NO temperature or max_tokens parameters - relies on model's reasoning capabilities
"""
import json
import sys
from typing import Dict, Any, List
from pathlib import Path

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import OPENAI_MODEL

# Import enhanced tools
from .react_tools import (
    # Coverage tools
    extract_coverage_and_jurisdictions,
    extract_custom_original_data,
    generate_regex_patterns_for_jurisdictions,
    
    # AST tools
    generate_ast_from_policy,
    validate_ast_logic,
    traverse_ast_by_coverage,
    
    # Enhanced constraint tools
    extract_and_infer_constraints_with_coverage,
    generate_coverage_based_rego_rule,
    
    # Original tools
    extract_policy_metadata,
    analyze_rdfs_comments,
    check_rego_syntax,
    fix_missing_if
)

from ..prompting.odrl_rego_strategies import (
    ODRL_PARSER_REACT_PROMPT,
    MIXTURE_OF_EXPERTS_REACT_PROMPT,
    REGO_GENERATOR_REACT_PROMPT,
    REFLECTION_REACT_PROMPT,
    CORRECTION_REACT_PROMPT,
    AST_VALIDATION_REACT_PROMPT,
    
    # Expert prompts
    JURISDICTION_EXPERT_PROMPT,
    REGEX_EXPERT_PROMPT,
    TYPE_SYSTEM_EXPERT_PROMPT,
    LOGIC_EXPERT_PROMPT,
    AST_EXPERT_PROMPT
)


# ============================================================================
# Configuration (NO temperature or max_tokens)
# ============================================================================

def get_llm_for_agent():
    """
    Get LLM instance using config.py settings.
    NO temperature or max_tokens - o3-mini handles reasoning internally.
    """
    return ChatOpenAI(model=OPENAI_MODEL)


# ============================================================================
# Enhanced Coverage-Based Agent Creators
# ============================================================================

def create_coverage_parser_agent():
    """
    Create agent for parsing ODRL with coverage-first approach.
    Extracts jurisdictions and groups rules by coverage+action.
    """
    llm = get_llm_for_agent()
    
    tools = [
        extract_coverage_and_jurisdictions,  # PRIMARY TOOL
        extract_custom_original_data,
        generate_regex_patterns_for_jurisdictions,
        extract_policy_metadata,
        extract_and_infer_constraints_with_coverage,
        generate_ast_from_policy,
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


def create_jurisdiction_expert_agent():
    """
    Create specialized expert for jurisdiction/coverage analysis.
    Part of Mixture of Experts pattern.
    """
    llm = get_llm_for_agent()
    
    tools = [
        extract_coverage_and_jurisdictions,
        generate_regex_patterns_for_jurisdictions,
        traverse_ast_by_coverage
    ]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=JURISDICTION_EXPERT_PROMPT,
        checkpointer=checkpointer
    )
    
    return agent


def create_regex_expert_agent():
    """
    Create specialized expert for regex pattern generation.
    """
    llm = get_llm_for_agent()
    
    tools = [
        generate_regex_patterns_for_jurisdictions
    ]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=REGEX_EXPERT_PROMPT,
        checkpointer=checkpointer
    )
    
    return agent


def create_type_system_expert_agent():
    """
    Create specialized expert for type inference.
    """
    llm = get_llm_for_agent()
    
    tools = [
        extract_and_infer_constraints_with_coverage
    ]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=TYPE_SYSTEM_EXPERT_PROMPT,
        checkpointer=checkpointer
    )
    
    return agent


def create_logic_expert_agent():
    """
    Create specialized expert for logical consistency analysis.
    """
    llm = get_llm_for_agent()
    
    tools = [
        validate_ast_logic,
        generate_ast_from_policy
    ]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=LOGIC_EXPERT_PROMPT,
        checkpointer=checkpointer
    )
    
    return agent


def create_ast_expert_agent():
    """
    Create specialized expert for AST analysis.
    """
    llm = get_llm_for_agent()
    
    tools = [
        generate_ast_from_policy,
        validate_ast_logic,
        traverse_ast_by_coverage
    ]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=AST_EXPERT_PROMPT,
        checkpointer=checkpointer
    )
    
    return agent


def create_mixture_of_experts_orchestrator():
    """
    Create orchestrator agent that coordinates expert agents.
    """
    llm = get_llm_for_agent()
    
    # Orchestrator has access to all tools
    tools = [
        extract_coverage_and_jurisdictions,
        extract_custom_original_data,
        generate_regex_patterns_for_jurisdictions,
        generate_ast_from_policy,
        validate_ast_logic,
        traverse_ast_by_coverage,
        extract_and_infer_constraints_with_coverage,
        analyze_rdfs_comments
    ]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=MIXTURE_OF_EXPERTS_REACT_PROMPT,
        checkpointer=checkpointer
    )
    
    return agent


def create_coverage_based_rego_generator():
    """
    Create agent for generating coverage-based Rego rules.
    """
    llm = get_llm_for_agent()
    
    tools = [
        extract_and_infer_constraints_with_coverage,
        generate_coverage_based_rego_rule,  # PRIMARY TOOL
        traverse_ast_by_coverage,
        generate_regex_patterns_for_jurisdictions,
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


def create_ast_validation_agent():
    """
    Create agent for AST-based logic validation.
    """
    llm = get_llm_for_agent()
    
    tools = [
        generate_ast_from_policy,
        validate_ast_logic,
        traverse_ast_by_coverage
    ]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=AST_VALIDATION_REACT_PROMPT,
        checkpointer=checkpointer
    )
    
    return agent


def create_reflection_agent():
    """
    Create self-reflection agent for validation.
    """
    llm = get_llm_for_agent()
    
    tools = [
        validate_ast_logic,
        check_rego_syntax,
        traverse_ast_by_coverage
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
    Create correction agent for fixing issues.
    """
    llm = get_llm_for_agent()
    
    tools = [
        generate_coverage_based_rego_rule,
        generate_regex_patterns_for_jurisdictions,
        validate_ast_logic,
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
# Mixture of Experts Workflow
# ============================================================================

def consult_experts(odrl_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Consult multiple expert agents and synthesize their analyses.
    
    Args:
        odrl_json: ODRL policy
        
    Returns:
        Aggregated expert analyses with consensus
    """
    odrl_str = json.dumps(odrl_json)
    
    # Create expert agents
    jurisdiction_expert = create_jurisdiction_expert_agent()
    regex_expert = create_regex_expert_agent()
    type_expert = create_type_system_expert_agent()
    logic_expert = create_logic_expert_agent()
    ast_expert = create_ast_expert_agent()
    
    expert_analyses = {}
    
    # Consult jurisdiction expert
    try:
        jurisdiction_query = f"Analyze the jurisdictions and coverage in this ODRL policy:\n{odrl_str}"
        jurisdiction_result = jurisdiction_expert.invoke({"messages": [HumanMessage(content=jurisdiction_query)]})
        expert_analyses["jurisdiction_expert"] = {
            "analysis": jurisdiction_result["messages"][-1].content,
            "expert_type": "jurisdiction"
        }
    except Exception as e:
        expert_analyses["jurisdiction_expert"] = {"error": str(e)}
    
    # Consult regex expert
    try:
        regex_query = f"Generate optimal regex patterns for jurisdiction matching in this policy:\n{odrl_str}"
        regex_result = regex_expert.invoke({"messages": [HumanMessage(content=regex_query)]})
        expert_analyses["regex_expert"] = {
            "analysis": regex_result["messages"][-1].content,
            "expert_type": "regex"
        }
    except Exception as e:
        expert_analyses["regex_expert"] = {"error": str(e)}
    
    # Consult type system expert
    try:
        type_query = f"Analyze data types in all constraints:\n{odrl_str}"
        type_result = type_expert.invoke({"messages": [HumanMessage(content=type_query)]})
        expert_analyses["type_expert"] = {
            "analysis": type_result["messages"][-1].content,
            "expert_type": "type_system"
        }
    except Exception as e:
        expert_analyses["type_expert"] = {"error": str(e)}
    
    # Consult logic expert
    try:
        logic_query = f"Validate logical consistency of this policy:\n{odrl_str}"
        logic_result = logic_expert.invoke({"messages": [HumanMessage(content=logic_query)]})
        expert_analyses["logic_expert"] = {
            "analysis": logic_result["messages"][-1].content,
            "expert_type": "logic"
        }
    except Exception as e:
        expert_analyses["logic_expert"] = {"error": str(e)}
    
    # Consult AST expert
    try:
        ast_query = f"Build and validate AST for this policy:\n{odrl_str}"
        ast_result = ast_expert.invoke({"messages": [HumanMessage(content=ast_query)]})
        expert_analyses["ast_expert"] = {
            "analysis": ast_result["messages"][-1].content,
            "expert_type": "ast"
        }
    except Exception as e:
        expert_analyses["ast_expert"] = {"error": str(e)}
    
    # Build consensus
    consensus = _build_expert_consensus(expert_analyses)
    
    return {
        "expert_analyses": expert_analyses,
        "consensus": consensus,
        "expert_count": len(expert_analyses)
    }


def _build_expert_consensus(expert_analyses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build consensus from expert analyses.
    """
    agreements = []
    disagreements = []
    concerns = []
    
    # Extract key findings from each expert
    for expert_name, analysis in expert_analyses.items():
        if "error" not in analysis:
            # Parse expert analysis to find agreements/disagreements
            # This is a simplified version - in practice, would use more sophisticated NLP
            content = analysis.get("analysis", "")
            if "agree" in content.lower() or "confirm" in content.lower():
                agreements.append({
                    "expert": expert_name,
                    "finding": content[:200]  # First 200 chars
                })
            if "concern" in content.lower() or "issue" in content.lower():
                concerns.append({
                    "expert": expert_name,
                    "concern": content[:200]
                })
    
    return {
        "agreements": agreements,
        "disagreements": disagreements,
        "concerns": concerns,
        "consensus_reached": len(disagreements) == 0,
        "confidence": 1.0 - (len(concerns) * 0.1)  # Reduce confidence for each concern
    }


# ============================================================================
# Enhanced Coverage-Based Workflow
# ============================================================================

def convert_odrl_to_rego_with_coverage(
    odrl_json: Dict[str, Any],
    existing_rego: str = None,
    max_corrections: int = 3,
    use_mixture_of_experts: bool = True
) -> Dict[str, Any]:
    """
    Complete ODRL to Rego conversion with coverage-based approach.
    
    Workflow:
    1. Parse ODRL with coverage-first approach
    2. Optionally consult mixture of experts
    3. Generate AST and validate logic
    4. Generate coverage-based Rego rules
    5. Self-reflect and validate
    6. Correct if needed (up to max_corrections attempts)
    
    Args:
        odrl_json: ODRL policy
        existing_rego: Existing Rego to append to (optional)
        max_corrections: Maximum correction attempts
        use_mixture_of_experts: Whether to use MoE pattern
        
    Returns:
        Complete conversion result with reasoning chains
    """
    odrl_str = json.dumps(odrl_json)
    
    result = {
        "success": False,
        "policy_id": odrl_json.get("@id", "unknown"),
        "generated_rego": "",
        "messages": [],
        "reasoning_chain": [],
        "expert_analyses": {},
        "ast_validation": {},
        "reflection": {},
        "correction_attempts": 0,
        "stage_reached": "initialization"
    }
    
    try:
        # Stage 1: Coverage-based parsing
        result["messages"].append("Stage 1: Parsing ODRL with coverage-first approach...")
        result["stage_reached"] = "parsing"
        
        parser_agent = create_coverage_parser_agent()
        parse_query = f"""Parse this ODRL policy with coverage-first approach:
1. Extract all jurisdictions/regions
2. Group rules by coverage + action
3. Map custom:originalData IDs
4. Generate regex patterns for jurisdictions
5. Infer types for all constraints

Policy:
{odrl_str}

Provide detailed chain of thought reasoning at each step."""
        
        parse_result = parser_agent.invoke({"messages": [HumanMessage(content=parse_query)]})
        parsed_content = parse_result["messages"][-1].content
        
        result["reasoning_chain"].append({
            "stage": "parsing",
            "reasoning": parsed_content
        })
        result["messages"].append("✓ Parsing complete")
        
        # Stage 2: Mixture of Experts (Optional)
        if use_mixture_of_experts:
            result["messages"].append("Stage 2: Consulting expert agents...")
            result["stage_reached"] = "expert_consultation"
            
            expert_results = consult_experts(odrl_json)
            result["expert_analyses"] = expert_results
            
            result["reasoning_chain"].append({
                "stage": "expert_consultation",
                "reasoning": f"Consulted {expert_results['expert_count']} experts. Consensus reached: {expert_results['consensus']['consensus_reached']}"
            })
            result["messages"].append(f"✓ Expert consultation complete. Confidence: {expert_results['consensus']['confidence']:.2f}")
        
        # Stage 3: AST Generation and Validation
        result["messages"].append("Stage 3: Generating and validating AST...")
        result["stage_reached"] = "ast_validation"
        
        ast_agent = create_ast_validation_agent()
        ast_query = f"""Generate AST from this ODRL policy and validate its logical correctness:
{odrl_str}

Perform deep traversal and validate:
1. Structural correctness
2. Logical consistency
3. No contradictions
4. Complete coverage

Provide traversal log and correctness score."""
        
        ast_result = ast_agent.invoke({"messages": [HumanMessage(content=ast_query)]})
        ast_content = ast_result["messages"][-1].content
        
        result["ast_validation"] = {
            "analysis": ast_content
        }
        result["reasoning_chain"].append({
            "stage": "ast_validation",
            "reasoning": ast_content
        })
        result["messages"].append("✓ AST validation complete")
        
        # Stage 4: Generate Coverage-Based Rego Rules
        result["messages"].append("Stage 4: Generating coverage-based Rego rules...")
        result["stage_reached"] = "rego_generation"
        
        rego_agent = create_coverage_based_rego_generator()
        
        existing_rego_context = ""
        if existing_rego:
            existing_rego_context = f"""
IMPORTANT: Append to existing Rego code:
```rego
{existing_rego}
```
Ensure no conflicts and consistent style."""
        
        rego_query = f"""Generate coverage-based Rego v1 rules for this ODRL policy:
{odrl_str}

Requirements:
1. Use coverage (jurisdiction) + action as primary rule organization
2. Generate regex patterns for jurisdiction matching using regex.match() or regex.find_all_string_submatch_n()
3. Create hierarchical jurisdiction checks with startswith()
4. Use proper type handling for ALL constraints
5. NO hardcoded values - all from policy
6. Include import rego.v1 and use 'if' keyword

{existing_rego_context}

Provide step-by-step reasoning for rule generation."""
        
        rego_result = rego_agent.invoke({"messages": [HumanMessage(content=rego_query)]})
        generated_rego = rego_result["messages"][-1].content
        
        # Extract Rego code if wrapped in markdown
        if "```rego" in generated_rego:
            parts = generated_rego.split("```rego")
            if len(parts) > 1:
                rego_code = parts[1].split("```")[0].strip()
            else:
                rego_code = generated_rego
        elif "```" in generated_rego:
            parts = generated_rego.split("```")
            if len(parts) > 1:
                rego_code = parts[1].strip()
            else:
                rego_code = generated_rego
        else:
            rego_code = generated_rego
        
        result["generated_rego"] = rego_code
        result["reasoning_chain"].append({
            "stage": "rego_generation",
            "reasoning": generated_rego
        })
        result["messages"].append("✓ Rego generation complete")
        
        # Stage 5: Self-Reflection and Validation
        result["messages"].append("Stage 5: Self-reflection and validation...")
        result["stage_reached"] = "reflection"
        
        reflection_agent = create_reflection_agent()
        reflection_query = f"""Critically evaluate this generated Rego code:

```rego
{rego_code}
```

Original ODRL policy:
{odrl_str}

Validation checklist:
1. Coverage/jurisdiction logic correct?
2. Regex patterns accurate?
3. Type handling correct?
4. Logic valid?
5. Syntax correct?

Provide detailed self-assessment with confidence scores."""
        
        reflection_result = reflection_agent.invoke({"messages": [HumanMessage(content=reflection_query)]})
        reflection_content = reflection_result["messages"][-1].content
        
        result["reflection"] = {
            "analysis": reflection_content
        }
        result["reasoning_chain"].append({
            "stage": "reflection",
            "reasoning": reflection_content
        })
        
        # Determine if corrections needed
        needs_correction = ("critical" in reflection_content.lower() or 
                          "error" in reflection_content.lower() or
                          "incorrect" in reflection_content.lower())
        
        if needs_correction and result["correction_attempts"] < max_corrections:
            result["messages"].append("⚠ Issues detected, applying corrections...")
            
            # Stage 6: Correction
            correction_agent = create_correction_agent()
            
            for attempt in range(max_corrections):
                result["correction_attempts"] = attempt + 1
                result["stage_reached"] = f"correction_attempt_{attempt + 1}"
                
                correction_query = f"""Fix issues in this Rego code:

Current code:
```rego
{result['generated_rego']}
```

Issues identified:
{reflection_content}

Original policy:
{odrl_str}

Apply corrections:
1. Fix coverage/jurisdiction logic
2. Correct regex patterns
3. Fix type handling
4. Resolve logical issues
5. Fix syntax errors

Provide corrected code with reasoning."""
                
                correction_result = correction_agent.invoke({"messages": [HumanMessage(content=correction_query)]})
                corrected_content = correction_result["messages"][-1].content
                
                # Extract corrected code
                if "```rego" in corrected_content:
                    corrected_code = corrected_content.split("```rego")[1].split("```")[0].strip()
                elif "```" in corrected_content:
                    corrected_code = corrected_content.split("```")[1].strip()
                else:
                    corrected_code = corrected_content
                
                result["generated_rego"] = corrected_code
                result["reasoning_chain"].append({
                    "stage": f"correction_{attempt + 1}",
                    "reasoning": corrected_content
                })
                
                # Re-validate
                validation_query = f"Validate this corrected Rego code:\n```rego\n{corrected_code}\n```"
                validation_result = reflection_agent.invoke({"messages": [HumanMessage(content=validation_query)]})
                validation_content = validation_result["messages"][-1].content
                
                if "valid" in validation_content.lower() and "critical" not in validation_content.lower():
                    result["messages"].append(f"✓ Corrections successful after {attempt + 1} attempt(s)")
                    break
            
            result["messages"].append(f"Correction attempts: {result['correction_attempts']}")
        else:
            result["messages"].append("✓ Validation passed, no corrections needed")
        
        # Final stage
        result["stage_reached"] = "completed"
        result["success"] = True
        result["messages"].append("✓ Conversion complete!")
        
    except Exception as e:
        result["success"] = False
        result["error_message"] = str(e)
        result["messages"].append(f"✗ Error: {str(e)}")
    
    return result


def convert_odrl_file_to_rego(
    input_file: str,
    output_file: str = None,
    existing_rego_file: str = None,
    use_mixture_of_experts: bool = True,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Convert ODRL file to Rego file with coverage-based approach.
    
    Args:
        input_file: Path to ODRL JSON file
        output_file: Path to output Rego file (default: input_file.rego)
        existing_rego_file: Path to existing Rego file to append to
        use_mixture_of_experts: Whether to use MoE pattern
        verbose: Print detailed reasoning chains
        
    Returns:
        Conversion result
    """
    # Read ODRL policy
    with open(input_file, 'r') as f:
        odrl_json = json.load(f)
    
    # Read existing Rego if provided
    existing_rego = None
    if existing_rego_file:
        with open(existing_rego_file, 'r') as f:
            existing_rego = f.read()
    
    # Convert
    result = convert_odrl_to_rego_with_coverage(
        odrl_json,
        existing_rego=existing_rego,
        use_mixture_of_experts=use_mixture_of_experts
    )
    
    # Print messages
    for msg in result["messages"]:
        print(msg)
    
    # Print reasoning chains if verbose
    if verbose:
        print("\n" + "="*80)
        print("REASONING CHAINS")
        print("="*80)
        for chain in result["reasoning_chain"]:
            print(f"\n[{chain['stage'].upper()}]")
            print(chain["reasoning"])
            print("-"*80)
    
    # Write output
    if result["success"]:
        if not output_file:
            output_file = input_file.replace(".json", ".rego")
        
        with open(output_file, 'w') as f:
            f.write(result["generated_rego"])
        
        print(f"\n✓ Rego code written to: {output_file}")
    
    return result


# Export main functions
__all__ = [
    "convert_odrl_to_rego_with_coverage",
    "convert_odrl_file_to_rego",
    "consult_experts",
    
    # Agent creators
    "create_coverage_parser_agent",
    "create_jurisdiction_expert_agent",
    "create_regex_expert_agent",
    "create_type_system_expert_agent",
    "create_logic_expert_agent",
    "create_ast_expert_agent",
    "create_mixture_of_experts_orchestrator",
    "create_coverage_based_rego_generator",
    "create_ast_validation_agent",
    "create_reflection_agent",
    "create_correction_agent"
]