"""
Enhanced ReAct Workflow with Coverage-Based Rules, AST Validation, and Mixture of Experts
Uses OpenAI o3-mini reasoning model from config.py
NO temperature or max_tokens parameters - relies on model's reasoning capabilities
"""
import json
import sys
import uuid
from typing import Dict, Any, List
from pathlib import Path

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import OPENAI_MODEL, Config

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
    if not Config.API_KEY:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Please set it using: export OPENAI_API_KEY='your-api-key'"
        )
    
    return ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=Config.API_KEY,
        base_url=Config.BASE_URL
    )


def get_agent_config():
    """
    Get configuration for agent invocation.
    Includes thread_id required by checkpointer.
    """
    return {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }


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
        extract_and_infer_constraints_with_coverage
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
    Create specialized expert for AST validation.
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
    Create MoE orchestrator agent that coordinates expert consultations.
    """
    llm = get_llm_for_agent()
    
    # MoE orchestrator has access to all tools but delegates to experts
    tools = [
        extract_coverage_and_jurisdictions,
        generate_regex_patterns_for_jurisdictions,
        extract_and_infer_constraints_with_coverage,
        generate_ast_from_policy,
        validate_ast_logic
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
    Create Rego generator agent with coverage-based approach.
    """
    llm = get_llm_for_agent()
    
    tools = [
        generate_coverage_based_rego_rule,
        generate_regex_patterns_for_jurisdictions,
        extract_and_infer_constraints_with_coverage,
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
    Create AST validation agent.
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
    config = get_agent_config()
    
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
        jurisdiction_result = jurisdiction_expert.invoke(
            {"messages": [HumanMessage(content=jurisdiction_query)]},
            config=config
        )
        expert_analyses["jurisdiction_expert"] = {
            "analysis": jurisdiction_result["messages"][-1].content,
            "expert_type": "jurisdiction"
        }
    except Exception as e:
        expert_analyses["jurisdiction_expert"] = {"error": str(e)}
    
    # Consult regex expert
    try:
        regex_query = f"Generate regex patterns for jurisdictions in this ODRL policy:\n{odrl_str}"
        regex_result = regex_expert.invoke(
            {"messages": [HumanMessage(content=regex_query)]},
            config=config
        )
        expert_analyses["regex_expert"] = {
            "analysis": regex_result["messages"][-1].content,
            "expert_type": "regex"
        }
    except Exception as e:
        expert_analyses["regex_expert"] = {"error": str(e)}
    
    # Consult type system expert
    try:
        type_query = f"Infer types and constraints in this ODRL policy:\n{odrl_str}"
        type_result = type_expert.invoke(
            {"messages": [HumanMessage(content=type_query)]},
            config=config
        )
        expert_analyses["type_expert"] = {
            "analysis": type_result["messages"][-1].content,
            "expert_type": "type_system"
        }
    except Exception as e:
        expert_analyses["type_expert"] = {"error": str(e)}
    
    # Consult logic expert
    try:
        logic_query = f"Analyze logical consistency in this ODRL policy:\n{odrl_str}"
        logic_result = logic_expert.invoke(
            {"messages": [HumanMessage(content=logic_query)]},
            config=config
        )
        expert_analyses["logic_expert"] = {
            "analysis": logic_result["messages"][-1].content,
            "expert_type": "logic"
        }
    except Exception as e:
        expert_analyses["logic_expert"] = {"error": str(e)}
    
    # Consult AST expert
    try:
        ast_query = f"Validate AST structure for this ODRL policy:\n{odrl_str}"
        ast_result = ast_expert.invoke(
            {"messages": [HumanMessage(content=ast_query)]},
            config=config
        )
        expert_analyses["ast_expert"] = {
            "analysis": ast_result["messages"][-1].content,
            "expert_type": "ast"
        }
    except Exception as e:
        expert_analyses["ast_expert"] = {"error": str(e)}
    
    # Synthesize expert opinions
    consensus = {
        "expert_count": len(expert_analyses),
        "consensus_reached": all("error" not in analysis for analysis in expert_analyses.values()),
        "confidence": sum(1 for analysis in expert_analyses.values() if "error" not in analysis) / len(expert_analyses)
    }
    
    return {
        "experts": expert_analyses,
        "consensus": consensus
    }


# ============================================================================
# Main Conversion Workflow
# ============================================================================

def convert_odrl_to_rego_with_coverage(
    odrl_json: Dict[str, Any],
    use_mixture_of_experts: bool = True,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Convert ODRL policy to Rego using coverage-based approach.
    
    Args:
        odrl_json: ODRL policy as JSON
        use_mixture_of_experts: Whether to use MoE pattern
        verbose: Print detailed reasoning chains
        
    Returns:
        Conversion result with Rego code and metadata
    """
    result = {
        "success": False,
        "policy_id": odrl_json.get("@id", "unknown"),
        "generated_rego": "",
        "messages": [],
        "reasoning_chain": [],
        "logical_issues": [],
        "correction_attempts": 0,
        "stage_reached": "initialization",
        "expert_analyses": None
    }
    
    config = get_agent_config()
    
    try:
        odrl_str = json.dumps(odrl_json, indent=2)
        
        # Stage 1: Parse ODRL with coverage extraction
        result["stage_reached"] = "parsing"
        result["messages"].append("Stage 1: Parsing ODRL with coverage-based approach...")
        
        parser_agent = create_coverage_parser_agent()
        parser_query = f"Parse this ODRL policy and extract coverage/jurisdictions:\n{odrl_str}"
        parser_result = parser_agent.invoke(
            {"messages": [HumanMessage(content=parser_query)]},
            config=config
        )
        parser_content = parser_result["messages"][-1].content
        
        if verbose:
            print(f"\n[Parser Agent]\n{parser_content}\n")
        
        result["reasoning_chain"].append({
            "stage": "parsing",
            "reasoning": parser_content
        })
        
        # Stage 2: Mixture of Experts (optional)
        if use_mixture_of_experts:
            result["stage_reached"] = "expert_consultation"
            result["messages"].append("Stage 2: Consulting expert agents...")
            
            expert_analyses = consult_experts(odrl_json)
            result["expert_analyses"] = expert_analyses
            
            if verbose:
                print(f"\n[Expert Analyses]\n{json.dumps(expert_analyses, indent=2)}\n")
            
            result["reasoning_chain"].append({
                "stage": "expert_consultation",
                "reasoning": json.dumps(expert_analyses, indent=2)
            })
        
        # Stage 3: AST Validation
        result["stage_reached"] = "ast_validation"
        result["messages"].append("Stage 3: Validating AST structure...")
        
        ast_agent = create_ast_validation_agent()
        ast_query = f"Generate and validate AST for this ODRL policy:\n{odrl_str}"
        ast_result = ast_agent.invoke(
            {"messages": [HumanMessage(content=ast_query)]},
            config=config
        )
        ast_content = ast_result["messages"][-1].content
        
        if verbose:
            print(f"\n[AST Validation]\n{ast_content}\n")
        
        result["reasoning_chain"].append({
            "stage": "ast_validation",
            "reasoning": ast_content
        })
        
        # Stage 4: Generate Rego
        result["stage_reached"] = "rego_generation"
        result["messages"].append("Stage 4: Generating coverage-based Rego code...")
        
        generator = create_coverage_based_rego_generator()
        
        # Prepare context with expert analyses if available
        context = f"ODRL Policy:\n{odrl_str}\n\nParser Analysis:\n{parser_content}\n\nAST Validation:\n{ast_content}"
        if use_mixture_of_experts and result["expert_analyses"]:
            context += f"\n\nExpert Analyses:\n{json.dumps(result['expert_analyses'], indent=2)}"
        
        rego_query = f"Generate coverage-based Rego code for:\n{context}"
        generator_result = generator.invoke(
            {"messages": [HumanMessage(content=rego_query)]},
            config=config
        )
        generator_content = generator_result["messages"][-1].content
        
        if verbose:
            print(f"\n[Rego Generator]\n{generator_content}\n")
        
        # Extract Rego code
        if "```rego" in generator_content:
            rego_code = generator_content.split("```rego")[1].split("```")[0].strip()
        elif "```" in generator_content:
            rego_code = generator_content.split("```")[1].strip()
        else:
            rego_code = generator_content
        
        result["generated_rego"] = rego_code
        result["reasoning_chain"].append({
            "stage": "rego_generation",
            "reasoning": generator_content
        })
        
        # Stage 5: Self-Reflection & Validation
        result["stage_reached"] = "reflection"
        result["messages"].append("Stage 5: Self-reflection and validation...")
        
        reflection_agent = create_reflection_agent()
        reflection_query = f"Validate this generated Rego code:\n```rego\n{rego_code}\n```"
        reflection_result = reflection_agent.invoke(
            {"messages": [HumanMessage(content=reflection_query)]},
            config=config
        )
        reflection_content = reflection_result["messages"][-1].content
        
        if verbose:
            print(f"\n[Reflection]\n{reflection_content}\n")
        
        result["reasoning_chain"].append({
            "stage": "reflection",
            "reasoning": reflection_content
        })
        
        # Check if corrections needed
        needs_correction = any(keyword in reflection_content.lower() 
                             for keyword in ["error", "issue", "problem", "incorrect", "invalid", "critical"])
        
        # Stage 6: Correction (if needed)
        if needs_correction:
            result["stage_reached"] = "correction"
            result["messages"].append("Stage 6: Applying corrections...")
            
            correction_agent = create_correction_agent()
            
            max_corrections = 3
            for attempt in range(max_corrections):
                result["correction_attempts"] = attempt + 1
                
                correction_query = f"""The following Rego code has issues:
```rego
{result['generated_rego']}
```

Issues identified:
{reflection_content}

Please fix:
1. Coverage/jurisdiction logic
2. Regex patterns
3. Type handling
4. Logical issues
5. Syntax errors

Provide corrected code with reasoning."""
                
                correction_result = correction_agent.invoke(
                    {"messages": [HumanMessage(content=correction_query)]},
                    config=config
                )
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
                validation_result = reflection_agent.invoke(
                    {"messages": [HumanMessage(content=validation_query)]},
                    config=config
                )
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
    Handles both single policies and arrays of policies.
    
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
    try:
        with open(input_file, 'r') as f:
            odrl_data = json.load(f)
        
        # Handle both single policies and arrays of policies
        policies_to_convert = []
        if isinstance(odrl_data, list):
            print(f"ℹ️ Input file contains {len(odrl_data)} policies. Processing all...")
            policies_to_convert = [p for p in odrl_data if isinstance(p, dict)]
            if len(policies_to_convert) != len(odrl_data):
                print(f"⚠️ Warning: Skipped {len(odrl_data) - len(policies_to_convert)} invalid items")
        elif isinstance(odrl_data, dict):
            policies_to_convert = [odrl_data]
        else:
            print(f"✗ Error: Input file must contain a JSON object or array, got {type(odrl_data).__name__}")
            return {
                "success": False,
                "policy_id": "unknown",
                "error_message": f"Invalid JSON structure: {type(odrl_data).__name__}",
                "stage_reached": "file_reading",
                "messages": [],
                "reasoning_chain": [],
                "correction_attempts": 0
            }
    
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON in input file: {e}")
        return {
            "success": False,
            "policy_id": "unknown",
            "error_message": f"Invalid JSON: {str(e)}",
            "stage_reached": "file_reading",
            "messages": [],
            "reasoning_chain": [],
            "correction_attempts": 0
        }
    except FileNotFoundError:
        print(f"✗ Error: File not found: {input_file}")
        return {
            "success": False,
            "policy_id": "unknown",
            "error_message": f"File not found: {input_file}",
            "stage_reached": "file_reading",
            "messages": [],
            "reasoning_chain": [],
            "correction_attempts": 0
        }
    
    # Convert all policies
    all_results = []
    all_rego_code = []
    
    for idx, odrl_json in enumerate(policies_to_convert, 1):
        policy_id = odrl_json.get("@id", f"policy_{idx}")
        print(f"\n{'='*80}")
        print(f"Processing policy {idx}/{len(policies_to_convert)}: {policy_id}")
        print(f"{'='*80}")
        
        result = convert_odrl_to_rego_with_coverage(
            odrl_json=odrl_json,
            use_mixture_of_experts=use_mixture_of_experts,
            verbose=verbose
        )
        
        all_results.append(result)
        
        if result["success"]:
            all_rego_code.append(f"\n# {'='*60}\n# Policy: {policy_id}\n# {'='*60}\n\n{result['generated_rego']}")
            print(f"✓ Successfully converted policy {idx}")
        else:
            print(f"✗ Failed to convert policy {idx}: {result.get('error_message', 'Unknown error')}")
    
    # Aggregate results
    successful = sum(1 for r in all_results if r["success"])
    failed = len(all_results) - successful
    
    aggregated_result = {
        "success": successful > 0,
        "policy_id": f"{successful}/{len(all_results)} policies",
        "generated_rego": "\n".join(all_rego_code),
        "messages": [
            f"Processed {len(all_results)} policies",
            f"✓ Successful: {successful}",
            f"✗ Failed: {failed}" if failed > 0 else "✓ All policies converted successfully"
        ],
        "reasoning_chain": [r["reasoning_chain"] for r in all_results],
        "logical_issues": [issue for r in all_results for issue in r.get("logical_issues", [])],
        "correction_attempts": sum(r.get("correction_attempts", 0) for r in all_results),
        "stage_reached": "completed",
        "individual_results": all_results
    }
    
    if not aggregated_result["success"]:
        return aggregated_result
    
    # Write to output file
    if output_file is None:
        output_file = input_file.replace('.json', '.rego')
    
    try:
        # Read existing rego if specified
        existing_content = ""
        if existing_rego_file:
            try:
                with open(existing_rego_file, 'r') as f:
                    existing_content = f.read() + "\n\n"
            except FileNotFoundError:
                print(f"⚠ Warning: Existing rego file not found: {existing_rego_file}")
        
        # Write output
        with open(output_file, 'w') as f:
            f.write(existing_content + aggregated_result["generated_rego"])
        
        aggregated_result["messages"].append(f"✓ Rego code written to: {output_file}")
        
    except Exception as e:
        aggregated_result["success"] = False
        aggregated_result["error_message"] = f"Failed to write output file: {str(e)}"
        aggregated_result["messages"].append(f"✗ Error writing output: {str(e)}")
    
    return aggregated_result