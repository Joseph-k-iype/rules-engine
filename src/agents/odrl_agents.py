"""
ODRL to Rego Conversion Agents
Individual agent implementations for the LangGraph workflow
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import OPENAI_MODEL, Config
from .agent_state import AgentState, ConversionStage, ODRLComponentAnalysis, RegoValidationResult
from .rego_prompts import (
    ODRL_PARSER_PROMPT,
    TYPE_INFERENCE_PROMPT,
    LOGIC_ANALYZER_PROMPT,
    REGO_GENERATOR_PROMPT,
    REFLECTION_PROMPT,
    CORRECTION_PROMPT
)


class ODRLParserAgent:
    """
    Agent responsible for parsing and understanding ODRL JSON-LD documents.
    Uses Chain of Thought reasoning to extract policy components.
    """
    
    def __init__(self):
        if not Config.API_KEY:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it using: export OPENAI_API_KEY='your-api-key'"
            )
        
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )
        self.parser = JsonOutputParser()
    
    def parse_odrl(self, state: AgentState) -> AgentState:
        """
        Parse ODRL document and extract all components with semantic understanding.
        """
        state["messages"].append("Starting ODRL parsing...")
        state["current_stage"] = ConversionStage.PARSING
        
        try:
            odrl_str = json.dumps(state["odrl_json"], indent=2)
            
            messages = [
                SystemMessage(content=ODRL_PARSER_PROMPT),
                HumanMessage(content=f"""
                Parse the following ODRL policy and extract all components with semantic reasoning:
                
                {odrl_str}
                
                Return a JSON object with:
                {{
                    "policy_id": "...",
                    "policy_type": "...",
                    "permissions": [...],
                    "prohibitions": [...],
                    "obligations": [...],
                    "constraints": [...],
                    "rdfs_comments": {{}},
                    "custom_properties": {{}},
                    "reasoning": "Step-by-step analysis of this policy..."
                }}
                """)
            ]
            
            response = self.llm.invoke(messages)
            parsed = json.loads(response.content)
            
            # Update state with parsed components
            state["policy_id"] = parsed.get("policy_id", "unknown")
            state["policy_type"] = parsed.get("policy_type", "Set")
            state["permissions"] = parsed.get("permissions", [])
            state["prohibitions"] = parsed.get("prohibitions", [])
            state["obligations"] = parsed.get("obligations", [])
            state["constraints"] = parsed.get("constraints", [])
            state["rdfs_comments"] = parsed.get("rdfs_comments", {})
            state["custom_properties"] = parsed.get("custom_properties", {})
            
            # Store reasoning
            state["reasoning_chain"].append({
                "stage": "parsing",
                "reasoning": parsed.get("reasoning", "")
            })
            
            state["messages"].append(f"Successfully parsed ODRL policy: {state['policy_id']}")
            state["messages"].append(f"Found {len(state['permissions'])} permissions, {len(state['prohibitions'])} prohibitions")
            
        except Exception as e:
            state["error_message"] = f"ODRL parsing failed: {str(e)}"
            state["current_stage"] = ConversionStage.FAILED
            state["messages"].append(f"ERROR: {str(e)}")
        
        return state


class TypeInferenceAgent:
    """
    Agent responsible for inferring data types from ODRL constraints.
    Uses domain knowledge and constraint analysis.
    """
    
    def __init__(self):
        if not Config.API_KEY:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it using: export OPENAI_API_KEY='your-api-key'"
            )
        
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )
    
    def infer_types(self, state: AgentState) -> AgentState:
        """
        Infer Rego data types for all constraints in the ODRL policy.
        """
        state["messages"].append("Starting type inference...")
        state["current_stage"] = ConversionStage.TYPE_INFERENCE
        
        try:
            constraints_str = json.dumps(state["constraints"], indent=2)
            rdfs_comments_str = json.dumps(state["rdfs_comments"], indent=2)
            
            messages = [
                SystemMessage(content=TYPE_INFERENCE_PROMPT),
                HumanMessage(content=f"""
                Infer data types for constraints in this ODRL policy:
                
                Constraints:
                {constraints_str}
                
                RDFS Comments (for context):
                {rdfs_comments_str}
                
                Return JSON with type inference for each constraint:
                {{
                    "inferred_types": {{
                        "constraint_path": "rego_type_pattern"
                    }},
                    "constraint_evaluations": [
                        {{
                            "constraint": {{}},
                            "rego_type": "...",
                            "rego_functions": ["..."],
                            "evaluation_pattern": "...",
                            "confidence": 0.95,
                            "reasoning": "..."
                        }}
                    ],
                    "overall_reasoning": "..."
                }}
                """)
            ]
            
            response = self.llm.invoke(messages)
            result = json.loads(response.content)
            
            state["inferred_types"] = result.get("inferred_types", {})
            state["constraint_evaluations"] = result.get("constraint_evaluations", [])
            
            state["reasoning_chain"].append({
                "stage": "type_inference",
                "reasoning": result.get("overall_reasoning", "")
            })
            
            state["messages"].append(f"Inferred types for {len(state['inferred_types'])} constraints")
            
        except Exception as e:
            state["error_message"] = f"Type inference failed: {str(e)}"
            state["current_stage"] = ConversionStage.FAILED
            state["messages"].append(f"ERROR: {str(e)}")
        
        return state


class LogicAnalyzerAgent:
    """
    Agent responsible for analyzing permission/prohibition logic and consistency.
    Ensures prohibitions are proper negations of permissions.
    """
    
    def __init__(self):
        if not Config.API_KEY:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it using: export OPENAI_API_KEY='your-api-key'"
            )
        
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )
    
    def analyze_logic(self, state: AgentState) -> AgentState:
        """
        Analyze logical relationships between permissions and prohibitions.
        """
        state["messages"].append("Starting logic analysis...")
        state["current_stage"] = ConversionStage.LOGIC_ANALYSIS
        
        try:
            policy_logic = {
                "permissions": state["permissions"],
                "prohibitions": state["prohibitions"],
                "inferred_types": state["inferred_types"]
            }
            
            logic_str = json.dumps(policy_logic, indent=2)
            
            messages = [
                SystemMessage(content=LOGIC_ANALYZER_PROMPT),
                HumanMessage(content=f"""
                Analyze the logical consistency of this ODRL policy:
                
                {logic_str}
                
                Return JSON with:
                {{
                    "permission_rules": [...],
                    "prohibition_rules": [...],
                    "negation_validation": {{}},
                    "logical_issues": ["..."],
                    "reasoning": "..."
                }}
                """)
            ]
            
            response = self.llm.invoke(messages)
            analysis = json.loads(response.content)
            
            state["permission_rules"] = analysis.get("permission_rules", [])
            state["prohibition_rules"] = analysis.get("prohibition_rules", [])
            state["negation_validation"] = analysis.get("negation_validation", {})
            state["logical_issues"] = analysis.get("logical_issues", [])
            
            state["reasoning_chain"].append({
                "stage": "logic_analysis",
                "reasoning": analysis.get("reasoning", "")
            })
            
            state["messages"].append(f"Logic analysis complete")
            if state["logical_issues"]:
                state["messages"].append(f"Found {len(state['logical_issues'])} issues")
            
        except Exception as e:
            state["error_message"] = f"Logic analysis failed: {str(e)}"
            state["current_stage"] = ConversionStage.FAILED
            state["messages"].append(f"ERROR: {str(e)}")
        
        return state


class RegoGeneratorAgent:
    """
    Agent responsible for generating OPA Rego v1 code from analyzed ODRL policy.
    """
    
    def __init__(self):
        if not Config.API_KEY:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it using: export OPENAI_API_KEY='your-api-key'"
            )
        
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )
        self.parser = StrOutputParser()
    
    def generate_rego(self, state: AgentState) -> AgentState:
        """
        Generate Rego v1 code from ODRL policy analysis.
        """
        state["messages"].append("Starting Rego generation...")
        state["current_stage"] = ConversionStage.REGO_GENERATION
        
        try:
            # Prepare context for generation
            context = {
                "policy_id": state["policy_id"],
                "policy_type": state["policy_type"],
                "permission_rules": state["permission_rules"],
                "prohibition_rules": state["prohibition_rules"],
                "constraint_evaluations": state["constraint_evaluations"],
                "inferred_types": state["inferred_types"]
            }
            
            context_str = json.dumps(context, indent=2)
            
            existing_rego_prompt = ""
            if state.get("existing_rego"):
                existing_rego_prompt = f"""
                
                IMPORTANT: There is existing Rego code that you must understand and append to:
                
                ```rego
                {state['existing_rego']}
                ```
                
                Your generated rules must:
                1. Not conflict with existing rules
                2. Use the same package if appropriate
                3. Follow the same coding style
                4. Be appended cleanly to the existing code
                """
            
            messages = [
                SystemMessage(content=REGO_GENERATOR_PROMPT),
                HumanMessage(content=f"""
                Generate OPA Rego v1 code for this analyzed ODRL policy:
                
                {context_str}
                {existing_rego_prompt}
                
                Generate complete, syntactically correct Rego v1 code that:
                1. Implements all permissions as allow rules
                2. Implements all prohibitions as denial/violation rules
                3. Properly evaluates all constraints with correct types
                4. Includes helpful comments
                5. Is compatible with OPA 1.9.0+
                
                Return ONLY the Rego code, no markdown formatting.
                """)
            ]
            
            response = self.llm.invoke(messages)
            rego_code = response.content.strip()
            
            # Remove markdown code fences if present
            if rego_code.startswith("```"):
                lines = rego_code.split("\n")
                rego_code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            state["generated_rego"] = rego_code
            
            # Extract package and imports
            lines = rego_code.split("\n")
            for line in lines:
                if line.strip().startswith("package "):
                    state["rego_package"] = line.strip().replace("package ", "")
                elif line.strip().startswith("import "):
                    if "rego_imports" not in state:
                        state["rego_imports"] = []
                    state["rego_imports"].append(line.strip())
            
            state["messages"].append(f"Generated Rego code ({len(rego_code)} characters)")
            
        except Exception as e:
            state["error_message"] = f"Rego generation failed: {str(e)}"
            state["current_stage"] = ConversionStage.FAILED
            state["messages"].append(f"ERROR: {str(e)}")
        
        return state


class ReflectionAgent:
    """
    Agent responsible for validating and critiquing generated Rego code.
    Provides detailed feedback for corrections.
    """
    
    def __init__(self):
        if not Config.API_KEY:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it using: export OPENAI_API_KEY='your-api-key'"
            )
        
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )
    
    def validate_rego(self, state: AgentState) -> AgentState:
        """
        Validate generated Rego code for syntax, logic, and completeness.
        """
        state["messages"].append("Starting Rego validation...")
        state["current_stage"] = ConversionStage.VALIDATION
        
        try:
            # Prepare context
            context = {
                "odrl_policy": {
                    "permissions": state["permissions"],
                    "prohibitions": state["prohibitions"],
                    "constraints": state["constraints"]
                },
                "generated_rego": state["generated_rego"]
            }
            
            context_str = json.dumps(context, indent=2)
            
            messages = [
                SystemMessage(content=REFLECTION_PROMPT),
                HumanMessage(content=f"""
                Validate this generated Rego code against the original ODRL policy:
                
                {context_str}
                
                Perform comprehensive validation and return JSON:
                {{
                    "is_valid": true/false,
                    "syntax_errors": ["..."],
                    "logic_errors": ["..."],
                    "suggestions": ["..."],
                    "confidence_score": 0.0-1.0,
                    "detailed_feedback": "..."
                }}
                """)
            ]
            
            response = self.llm.invoke(messages)
            validation = json.loads(response.content)
            
            state["validation_passed"] = validation.get("is_valid", False)
            state["syntax_errors"] = validation.get("syntax_errors", [])
            state["logic_errors"] = validation.get("logic_errors", [])
            state["reflection_feedback"] = validation.get("detailed_feedback", "")
            
            state["reasoning_chain"].append({
                "stage": "validation",
                "reasoning": validation.get("detailed_feedback", "")
            })
            
            if state["validation_passed"]:
                state["messages"].append("✓ Validation passed!")
                state["current_stage"] = ConversionStage.COMPLETED
            else:
                state["messages"].append(f"✗ Validation failed: {len(state['syntax_errors']) + len(state['logic_errors'])} issues found")
                state["current_stage"] = ConversionStage.CORRECTION
            
        except Exception as e:
            state["error_message"] = f"Validation failed: {str(e)}"
            state["current_stage"] = ConversionStage.FAILED
            state["messages"].append(f"ERROR: {str(e)}")
        
        return state


class CorrectionAgent:
    """
    Agent responsible for fixing issues in generated Rego code.
    Learns from validation feedback and applies corrections.
    """
    
    def __init__(self):
        if not Config.API_KEY:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it using: export OPENAI_API_KEY='your-api-key'"
            )
        
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )
    
    def correct_rego(self, state: AgentState) -> AgentState:
        """
        Correct issues in Rego code based on validation feedback.
        """
        state["messages"].append("Starting Rego correction...")
        state["correction_attempts"] += 1
        
        if state["correction_attempts"] > state["max_corrections"]:
            state["error_message"] = f"Max correction attempts ({state['max_corrections']}) exceeded"
            state["current_stage"] = ConversionStage.FAILED
            state["messages"].append("ERROR: Too many correction attempts, giving up")
            return state
        
        try:
            # Prepare correction context
            correction_context = {
                "original_rego": state["generated_rego"],
                "syntax_errors": state["syntax_errors"],
                "logic_errors": state["logic_errors"],
                "validation_feedback": state["reflection_feedback"],
                "previous_corrections": state["corrections_applied"],
                "odrl_reference": {
                    "permissions": state["permissions"],
                    "prohibitions": state["prohibitions"]
                }
            }
            
            context_str = json.dumps(correction_context, indent=2)
            
            messages = [
                SystemMessage(content=CORRECTION_PROMPT),
                HumanMessage(content=f"""
                Fix the issues in this Rego code (Attempt {state['correction_attempts']}/{state['max_corrections']}):
                
                {context_str}
                
                Return JSON:
                {{
                    "corrected_rego": "...",
                    "changes_made": ["..."],
                    "reasoning": "...",
                    "confidence": 0.0-1.0
                }}
                """)
            ]
            
            response = self.llm.invoke(messages)
            correction = json.loads(response.content)
            
            # Update state with corrected code
            state["generated_rego"] = correction.get("corrected_rego", state["generated_rego"])
            
            changes = correction.get("changes_made", [])
            state["corrections_applied"].extend(changes)
            
            state["reasoning_chain"].append({
                "stage": f"correction_{state['correction_attempts']}",
                "reasoning": correction.get("reasoning", "")
            })
            
            state["messages"].append(f"Applied {len(changes)} corrections (attempt {state['correction_attempts']})")
            
            # Return to validation stage
            state["current_stage"] = ConversionStage.VALIDATION
            
        except Exception as e:
            state["error_message"] = f"Correction failed: {str(e)}"
            state["current_stage"] = ConversionStage.FAILED
            state["messages"].append(f"ERROR: {str(e)}")
        
        return state