"""
LangGraph Workflow for ODRL to Rego Conversion
Implements a state machine with reflection and self-correction
"""
import sys
from pathlib import Path
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .agent_state import AgentState, ConversionStage
from .odrl_agents import (
    ODRLParserAgent,
    TypeInferenceAgent,
    LogicAnalyzerAgent,
    RegoGeneratorAgent,
    ReflectionAgent,
    CorrectionAgent
)


def create_odrl_to_rego_workflow():
    """
    Create the LangGraph workflow for ODRL to Rego conversion.
    
    Workflow:
    1. Parse ODRL → 2. Infer Types → 3. Analyze Logic → 4. Generate Rego → 
    5. Validate → 6a. If valid: END or 6b. If invalid: Correct → back to 5
    """
    
    # Initialize agents
    parser = ODRLParserAgent()
    type_inference = TypeInferenceAgent()
    logic_analyzer = LogicAnalyzerAgent()
    rego_generator = RegoGeneratorAgent()
    reflection = ReflectionAgent()
    correction = CorrectionAgent()
    
    # Create workflow graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("parse_odrl", parser.parse_odrl)
    workflow.add_node("infer_types", type_inference.infer_types)
    workflow.add_node("analyze_logic", logic_analyzer.analyze_logic)
    workflow.add_node("generate_rego", rego_generator.generate_rego)
    workflow.add_node("validate", reflection.validate_rego)
    workflow.add_node("correct", correction.correct_rego)
    
    # Define routing functions
    def route_after_parsing(state: AgentState) -> Literal["infer_types", "end"]:
        """Route after ODRL parsing"""
        if state["current_stage"] == ConversionStage.FAILED:
            return "end"
        return "infer_types"
    
    def route_after_type_inference(state: AgentState) -> Literal["analyze_logic", "end"]:
        """Route after type inference"""
        if state["current_stage"] == ConversionStage.FAILED:
            return "end"
        return "analyze_logic"
    
    def route_after_logic_analysis(state: AgentState) -> Literal["generate_rego", "end"]:
        """Route after logic analysis"""
        if state["current_stage"] == ConversionStage.FAILED:
            return "end"
        return "generate_rego"
    
    def route_after_generation(state: AgentState) -> Literal["validate", "end"]:
        """Route after Rego generation"""
        if state["current_stage"] == ConversionStage.FAILED:
            return "end"
        return "validate"
    
    def route_after_validation(state: AgentState) -> Literal["correct", "end"]:
        """
        Route after validation.
        If validation passed, end workflow.
        If validation failed and corrections available, go to correction.
        Otherwise, end with failure.
        """
        if state["current_stage"] == ConversionStage.COMPLETED:
            return "end"
        elif state["current_stage"] == ConversionStage.CORRECTION:
            if state["correction_attempts"] >= state["max_corrections"]:
                return "end"
            return "correct"
        return "end"
    
    def route_after_correction(state: AgentState) -> Literal["validate", "end"]:
        """
        Route after correction.
        Always go back to validation unless failed.
        """
        if state["current_stage"] == ConversionStage.FAILED:
            return "end"
        return "validate"
    
    # Add edges
    workflow.set_entry_point("parse_odrl")
    
    workflow.add_conditional_edges(
        "parse_odrl",
        route_after_parsing,
        {
            "infer_types": "infer_types",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "infer_types",
        route_after_type_inference,
        {
            "analyze_logic": "analyze_logic",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "analyze_logic",
        route_after_logic_analysis,
        {
            "generate_rego": "generate_rego",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "generate_rego",
        route_after_generation,
        {
            "validate": "validate",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "correct": "correct",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "correct",
        route_after_correction,
        {
            "validate": "validate",
            "end": END
        }
    )
    
    # Compile workflow with memory for checkpointing
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


def initialize_state(
    odrl_json: Dict[str, Any],
    existing_rego: str = None,
    max_corrections: int = 3
) -> AgentState:
    """
    Initialize the agent state for a new conversion.
    
    Args:
        odrl_json: ODRL policy in JSON-LD format
        existing_rego: Existing Rego code to append to (optional)
        max_corrections: Maximum number of correction attempts
    
    Returns:
        Initialized AgentState
    """
    return {
        # Input
        "odrl_json": odrl_json,
        "existing_rego": existing_rego,
        
        # Parsed ODRL components (initialized empty)
        "policy_id": "",
        "policy_type": "",
        "permissions": [],
        "prohibitions": [],
        "obligations": [],
        "constraints": [],
        "rdfs_comments": {},
        "custom_properties": {},
        
        # Type inference results
        "inferred_types": {},
        "constraint_evaluations": [],
        
        # Logic analysis results
        "permission_rules": [],
        "prohibition_rules": [],
        "negation_validation": {},
        "logical_issues": [],
        
        # Generated Rego
        "generated_rego": "",
        "rego_package": "",
        "rego_imports": [],
        
        # Validation results
        "syntax_errors": [],
        "logic_errors": [],
        "validation_passed": False,
        "reflection_feedback": "",
        
        # Correction tracking
        "correction_attempts": 0,
        "max_corrections": max_corrections,
        "corrections_applied": [],
        
        # Workflow control
        "current_stage": ConversionStage.PARSING,
        "error_message": None,
        "messages": [],
        
        # Chain of thought reasoning
        "reasoning_chain": [],
        
        # Expert consultation
        "expert_analyses": {}
    }


async def convert_odrl_to_rego(
    odrl_json: Dict[str, Any],
    existing_rego: str = None,
    max_corrections: int = 3,
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Convert an ODRL policy to Rego using the LangGraph workflow.
    
    Args:
        odrl_json: ODRL policy in JSON-LD format
        existing_rego: Existing Rego code to append to (optional)
        max_corrections: Maximum number of correction attempts
        config: LangGraph configuration (for checkpointing)
    
    Returns:
        Dictionary with conversion results including:
        - generated_rego: The final Rego code
        - validation_passed: Whether validation succeeded
        - messages: Log messages from the workflow
        - reasoning_chain: Chain of thought for each stage
    """
    # Initialize state
    initial_state = initialize_state(odrl_json, existing_rego, max_corrections)
    
    # Create workflow
    app = create_odrl_to_rego_workflow()
    
    # Run workflow
    if config is None:
        config = {"configurable": {"thread_id": "odrl-to-rego-conversion"}}
    
    final_state = await app.ainvoke(initial_state, config)
    
    # Return results
    return {
        "success": final_state["validation_passed"],
        "generated_rego": final_state["generated_rego"],
        "policy_id": final_state["policy_id"],
        "messages": final_state["messages"],
        "reasoning_chain": final_state["reasoning_chain"],
        "logical_issues": final_state["logical_issues"],
        "correction_attempts": final_state["correction_attempts"],
        "error_message": final_state.get("error_message"),
        "stage_reached": final_state["current_stage"].value
    }


def convert_odrl_to_rego_sync(
    odrl_json: Dict[str, Any],
    existing_rego: str = None,
    max_corrections: int = 3
) -> Dict[str, Any]:
    """
    Synchronous version of ODRL to Rego conversion.
    
    Args:
        odrl_json: ODRL policy in JSON-LD format
        existing_rego: Existing Rego code to append to (optional)
        max_corrections: Maximum number of correction attempts
    
    Returns:
        Dictionary with conversion results
    """
    import asyncio
    
    # Get or create event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Run async function
    return loop.run_until_complete(
        convert_odrl_to_rego(odrl_json, existing_rego, max_corrections)
    )