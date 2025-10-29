"""
Enhanced ReAct Workflow with Coverage-Based Rules, AST Validation, and Clean Code Extraction
Uses OpenAI o3-mini reasoning model from config.py
Ensures ONLY valid Rego code is generated (no explanations or reasoning in output files)
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

# Import extraction utilities
from ..utils.rego_extractor import extract_and_validate_rego, RegoExtractor, RegoValidator


# ============================================================================
# Configuration
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
    """
    llm = get_llm_for_agent()
    
    tools = [
        extract_coverage_and_jurisdictions,
        extract_custom_original_data,
        extract_policy_metadata,
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
    """Create jurisdiction/coverage expert agent."""
    llm = get_llm_for_agent()
    
    tools = [
        extract_coverage_and_jurisdictions,
        generate_regex_patterns_for_jurisdictions
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
    """Create regex pattern expert agent."""
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
    """Create type system expert agent."""
    llm = get_llm_for_agent()
    
    tools = [
        extract_and_infer_constraints_with_coverage,
        analyze_rdfs_comments
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
    """Create logic validation expert agent."""
    llm = get_llm_for_agent()
    
    tools = [
        validate_ast_logic,
        extract_custom_original_data
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
    """Create AST expert agent."""
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
    Create mixture of experts orchestrator agent.
    """
    llm = get_llm_for_agent()
    
    # Note: This agent doesn't call tools directly, but coordinates other agents
    # We give it basic tools for validation
    tools = [
        extract_coverage_and_jurisdictions,
        extract_custom_original_data
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
    Create coverage-based Rego generator agent.
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
    """Create AST validation agent."""
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
    """Create self-reflection agent for validation."""
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
    """Create correction agent for fixing issues."""
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
    """
    config = get_agent_config()
    expert_analyses = {}
    
    try:
        # Prepare policy string
        policy_str = json.dumps(odrl_json, indent=2)
        
        # Consult Jurisdiction Expert
        jurisdiction_expert = create_jurisdiction_expert_agent()
        jurisdiction_query = f"Analyze jurisdiction/coverage patterns in:\n{policy_str}"
        jurisdiction_result = jurisdiction_expert.invoke(
            {"messages": [HumanMessage(content=jurisdiction_query)]},
            config=config
        )
        expert_analyses['jurisdiction'] = jurisdiction_result["messages"][-1].content
        
        # Consult Type System Expert
        type_expert = create_type_system_expert_agent()
        type_query = f"Infer types for all constraints in:\n{policy_str}"
        type_result = type_expert.invoke(
            {"messages": [HumanMessage(content=type_query)]},
            config=config
        )
        expert_analyses['types'] = type_result["messages"][-1].content
        
        # Consult Logic Expert
        logic_expert = create_logic_expert_agent()
        logic_query = f"Validate logical consistency of:\n{policy_str}"
        logic_result = logic_expert.invoke(
            {"messages": [HumanMessage(content=logic_query)]},
            config=config
        )
        expert_analyses['logic'] = logic_result["messages"][-1].content
        
        # Consult AST Expert
        ast_expert = create_ast_expert_agent()
        ast_query = f"Generate and validate AST for:\n{policy_str}"
        ast_result = ast_expert.invoke(
            {"messages": [HumanMessage(content=ast_query)]},
            config=config
        )
        expert_analyses['ast'] = ast_result["messages"][-1].content
        
    except Exception as e:
        expert_analyses['error'] = str(e)
    
    return expert_analyses


# ============================================================================
# Main Conversion Function with Clean Code Extraction
# ============================================================================

def convert_odrl_to_rego_with_coverage(
    odrl_json: Dict[str, Any],
    existing_rego: str = None,
    use_mixture_of_experts: bool = True,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Convert ODRL policy to Rego using coverage-based approach.
    
    CRITICAL: Extracts ONLY valid Rego code, removing all explanations and reasoning.
    
    Args:
        odrl_json: ODRL policy in JSON-LD format
        existing_rego: Optional existing Rego code to append to
        use_mixture_of_experts: Whether to consult expert agents
        verbose: Print detailed progress
        
    Returns:
        Dict with conversion results
    """
    result = {
        "success": False,
        "policy_id": odrl_json.get("uid", odrl_json.get("@id", "unknown")),
        "generated_rego": "",
        "messages": [],
        "reasoning_chain": [],
        "logical_issues": [],
        "correction_attempts": 0,
        "stage_reached": "initialization",
        "expert_analyses": {}
    }
    
    config = get_agent_config()
    
    try:
        # Prepare policy string
        odrl_str = json.dumps(odrl_json, indent=2)
        
        # Stage 1: Parser Analysis
        result["stage_reached"] = "parsing"
        result["messages"].append("Stage 1: Parsing ODRL policy...")
        
        parser = create_coverage_parser_agent()
        parser_query = f"Parse and analyze this ODRL policy:\n{odrl_str}"
        parser_result = parser.invoke(
            {"messages": [HumanMessage(content=parser_query)]},
            config=config
        )
        parser_content = parser_result["messages"][-1].content
        
        if verbose:
            print(f"\n[Parser Analysis]\n{parser_content}\n")
        
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
        
        # Stage 3: AST Validation
        result["stage_reached"] = "ast_validation"
        result["messages"].append("Stage 3: Validating policy structure via AST...")
        
        ast_validator = create_ast_validation_agent()
        ast_query = f"Validate AST for:\n{odrl_str}"
        ast_result = ast_validator.invoke(
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
        
        # Add instruction to output ONLY Rego code
        rego_query = f"""Generate coverage-based Rego code for:\n{context}

CRITICAL: Output ONLY valid Rego code. NO explanations, NO reasoning, NO markdown.
Start with 'package' declaration and include ONLY Rego syntax."""
        
        generator_result = generator.invoke(
            {"messages": [HumanMessage(content=rego_query)]},
            config=config
        )
        generator_content = generator_result["messages"][-1].content
        
        if verbose:
            print(f"\n[Rego Generator Raw Output]\n{generator_content}\n")
        
        # CRITICAL: Extract ONLY Rego code, remove all explanations
        extraction_result = extract_and_validate_rego(generator_content, verbose=verbose)
        rego_code = extraction_result['rego_code']
        
        if not extraction_result['extracted_successfully']:
            result["messages"].append("⚠ Warning: Rego extraction may be incomplete")
        
        result["generated_rego"] = rego_code
        result["reasoning_chain"].append({
            "stage": "rego_generation",
            "reasoning": generator_content,
            "extraction_result": extraction_result
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
                
                correction_query = f"""Fix issues in this Rego code:

```rego
{result['generated_rego']}
```

Issues identified:
{reflection_content}

CRITICAL: Output ONLY corrected Rego code. NO explanations."""
                
                correction_result = correction_agent.invoke(
                    {"messages": [HumanMessage(content=correction_query)]},
                    config=config
                )
                corrected_content = correction_result["messages"][-1].content
                
                # Extract corrected code
                corrected_extraction = extract_and_validate_rego(corrected_content, verbose=verbose)
                corrected_code = corrected_extraction['rego_code']
                
                result["generated_rego"] = corrected_code
                result["reasoning_chain"].append({
                    "stage": f"correction_{attempt + 1}",
                    "reasoning": corrected_content,
                    "extraction_result": corrected_extraction
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
        
        # Final validation
        final_validation = RegoValidator.validate_syntax(result["generated_rego"])
        if not final_validation['valid']:
            result["messages"].append("⚠ Final validation found issues:")
            for error in final_validation['errors']:
                result["messages"].append(f"  ✗ {error}")
        
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
    """
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both single policy and array of policies
        policies = data if isinstance(data, list) else [data]
        
        # Read existing rego if provided
        existing_rego = None
        if existing_rego_file:
            try:
                with open(existing_rego_file, 'r', encoding='utf-8') as f:
                    existing_rego = f.read()
            except FileNotFoundError:
                pass
        
        # Convert each policy
        all_results = []
        all_rego_code = []
        
        for i, policy in enumerate(policies, 1):
            if verbose:
                print(f"\n{'='*80}")
                print(f"Converting Policy {i}/{len(policies)}")
                print(f"{'='*80}")
            
            result = convert_odrl_to_rego_with_coverage(
                odrl_json=policy,
                existing_rego=existing_rego if i == 1 else None,
                use_mixture_of_experts=use_mixture_of_experts,
                verbose=verbose
            )
            
            all_results.append(result)
            
            if result["success"]:
                all_rego_code.append(result["generated_rego"])
        
        # Combine all Rego code
        combined_rego = "\n\n# " + "="*78 + "\n\n".join(all_rego_code) if len(all_rego_code) > 1 else all_rego_code[0] if all_rego_code else ""
        
        # Aggregate results
        successful = sum(1 for r in all_results if r["success"])
        failed = len(all_results) - successful
        
        aggregated_result = {
            "success": failed == 0,
            "generated_rego": combined_rego,
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
                    with open(existing_rego_file, 'r', encoding='utf-8') as f:
                        existing_content = f.read() + "\n\n"
                except FileNotFoundError:
                    print(f"⚠  Warning: Existing rego file not found: {existing_rego_file}")
            
            # Write output with UTF-8 encoding
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(existing_content + aggregated_result["generated_rego"])
            
            aggregated_result["messages"].append(f"✓ Rego code written to: {output_file}")
            
        except Exception as e:
            aggregated_result["success"] = False
            aggregated_result["error_message"] = f"Failed to write output file: {str(e)}"
            aggregated_result["messages"].append(f"✗ Error writing output: {str(e)}")
        
        return aggregated_result
        
    except Exception as e:
        return {
            "success": False,
            "error_message": str(e),
            "messages": [f"✗ Failed to read input file: {str(e)}"],
            "generated_rego": "",
            "reasoning_chain": [],
            "logical_issues": [],
            "correction_attempts": 0,
            "stage_reached": "file_reading"
        }


__all__ = [
    "convert_odrl_to_rego_with_coverage",
    "convert_odrl_file_to_rego",
    "consult_experts",
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
    "create_correction_agent",
]