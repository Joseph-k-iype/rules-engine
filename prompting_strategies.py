"""
Advanced prompting strategies for rule extraction.
Implements Chain of Thought, Mixture of Experts, Mixture of Thought, and Mixture of Reasoning approaches.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class PromptingStrategies:
    """Advanced prompting strategies for legal analysis and rule extraction."""
    
    @staticmethod
    def chain_of_thought_prompt(legislation_text: str, existing_context: str = "") -> str:
        """Chain of Thought prompting for step-by-step reasoning."""
        context_section = f"\n\nEXISTING RULES CONTEXT:\n{existing_context}\n" if existing_context else ""
        
        return f"""
        You are an expert legal analyst specializing in converting legislation into machine-readable rules.
        {context_section}
        Analyze the following legislation text step by step:
        
        LEGISLATION TEXT:
        {legislation_text}
        
        CHAIN OF THOUGHT ANALYSIS:
        
        Step 1: Identify Key Legal Obligations
        - What are the main obligations stated in this text?
        - Who has these obligations (controller, processor, joint_controller)?
        - Are there specific requirements for data handling?
        
        Step 2: Extract Conditional Logic
        - What conditions trigger these obligations?
        - Are there any "if-then" relationships?
        - What are the specific criteria that must be met?
        - Under what circumstances do these rules apply?
        
        Step 3: Determine Data Domains
        - Does this relate to data_transfer, data_usage, or data_storage?
        - Which specific data activities are covered?
        - Are there cross-border transfer considerations?
        
        Step 4: Identify Roles and Data Categories
        - Who are the key actors (controller, processor, joint_controller)?
        - What is the primary impacted role and any secondary impacted role?
        - What data categories are involved (personal_data, sensitive_data, biometric_data, health_data, financial_data, location_data, behavioral_data, identification_data)?
        - Are roles explicitly mentioned or implied?
        
        Step 5: Structure as Machine-Readable Rules
        - Convert each obligation into a conditional rule
        - Define clear facts, operators, and values
        - Ensure alignment with json-rules-engine format
        - Consider existing rules to maintain consistency
        - Assign appropriate confidence scores based on clarity of text
        
        Step 6: Validate and Refine
        - Check for overlaps with existing rules
        - Ensure all extracted elements are explicitly stated in the legislation
        - Verify logical consistency of conditions
        
        Let's work through this step by step...
        """
    
    @staticmethod
    def mixture_of_experts_prompt(legislation_text: str, existing_context: str = "") -> str:
        """Mixture of Experts prompting with specialized perspectives."""
        context_section = f"\n\nEXISTING RULES CONTEXT:\n{existing_context}\n" if existing_context else ""
        
        return f"""
        We need to analyze legislation from multiple expert perspectives. Each expert will contribute their specialized knowledge.
        {context_section}
        LEGISLATION TEXT:
        {legislation_text}
        
        === EXPERT PANEL ANALYSIS ===
        
        EXPERT 1 - PRIVACY LAW SPECIALIST:
        As a privacy law expert, I will focus on:
        - Data protection obligations and rights
        - Cross-border transfer requirements and adequacy decisions
        - Consent and lawful basis considerations
        - Individual rights and freedoms (access, rectification, erasure)
        - Primary and secondary impacted roles (controller vs processor)
        - Specific data categories mentioned (personal, sensitive, health, etc.)
        - Legal basis requirements and their implications
        
        My analysis identifies the following privacy-specific obligations:
        [Detailed privacy law analysis focusing on data protection aspects]
        
        EXPERT 2 - TECHNICAL COMPLIANCE SPECIALIST:
        As a technical expert, I will focus on:
        - Technical and organizational measures required
        - Security requirements and safeguards
        - Data processing procedures and controls
        - Risk assessment and mitigation strategies
        - Data categories and their technical handling requirements
        - Implementation feasibility and technical constraints
        - Monitoring and auditing requirements
        
        My analysis identifies the following technical requirements:
        [Detailed technical analysis focusing on implementation aspects]
        
        EXPERT 3 - REGULATORY INTERPRETATION SPECIALIST:
        As a regulatory expert, I will focus on:
        - Supervisory authority requirements and enforcement
        - Penalty and enforcement mechanisms
        - Compliance documentation needs
        - Audit and accountability measures
        - Consistency with existing regulatory framework
        - Reporting and notification obligations
        - Jurisdictional considerations and applicable countries
        
        My analysis identifies the following regulatory requirements:
        [Detailed regulatory analysis focusing on compliance and enforcement]
        
        EXPERT 4 - BUSINESS OPERATIONS SPECIALIST:
        As a business operations expert, I will focus on:
        - Practical implementation challenges
        - Business process implications
        - Resource requirements and operational impact
        - Risk-benefit analysis from business perspective
        - Integration with existing business practices
        - Cost-benefit considerations
        - Stakeholder impact assessment
        
        My analysis identifies the following operational considerations:
        [Detailed business analysis focusing on practical implementation]
        
        === SYNTHESIS ===
        Now, integrating all expert perspectives to create comprehensive, actionable rules that:
        - Respect the legal precision of Expert 1
        - Address the technical feasibility concerns of Expert 2
        - Meet the regulatory compliance needs of Expert 3
        - Consider the business practicality insights of Expert 4
        - Build upon the existing rules context to maintain consistency
        
        Each expert will contribute different aspects of the legislation and provide a comprehensive rule extraction.
        """
    
    @staticmethod
    def mixture_of_thought_prompt(legislation_text: str, existing_context: str = "") -> str:
        """Mixture of Thought prompting for diverse reasoning approaches."""
        context_section = f"\n\nEXISTING RULES CONTEXT:\n{existing_context}\n" if existing_context else ""
        
        return f"""
        Apply multiple thinking approaches to analyze this legislation comprehensively.
        {context_section}
        LEGISLATION TEXT:
        {legislation_text}
        
        === MULTIPLE THINKING APPROACHES ===
        
        ANALYTICAL THINKING:
        Breaking down complex legislation systematically:
        - Decompose the text into component obligations and requirements
        - Identify logical relationships and dependencies between different provisions
        - Create systematic categorization of requirements by domain (transfer, usage, storage)
        - Analyze consistency with existing rules and identify potential conflicts
        - Map cause-and-effect relationships between conditions and obligations
        - Quantify confidence levels based on textual clarity and specificity
        
        CREATIVE THINKING:
        Exploring alternative perspectives and scenarios:
        - Consider edge cases and alternative interpretations of ambiguous language
        - Think about practical implementation scenarios across different business contexts
        - Explore different ways obligations could be triggered in real-world situations
        - Identify gaps in existing rule coverage that this legislation might address
        - Generate innovative approaches to representing complex legal concepts
        - Consider unintended consequences or secondary effects of rules
        
        CRITICAL THINKING:
        Questioning and evaluating assumptions:
        - Question assumptions and implicit requirements not explicitly stated
        - Evaluate the necessity and sufficiency of identified conditions
        - Consider potential conflicts, contradictions, or ambiguities in the text
        - Assess the strength of evidence for each extracted rule
        - Examine the logical validity of conditional statements
        - Challenge initial interpretations with alternative readings
        
        PRACTICAL THINKING:
        Focusing on real-world application and implementation:
        - Consider operational feasibility and implementation challenges
        - Think about monitoring and enforcement mechanisms required
        - Evaluate primary vs secondary role impacts on different stakeholders
        - Assess resource requirements for compliance
        - Consider integration with existing business processes and systems
        - Examine scalability and adaptability of extracted rules
        
        SYSTEMATIC THINKING:
        Understanding broader context and interconnections:
        - Consider the broader regulatory framework and legal ecosystem
        - Understand interconnections with other provisions and regulations
        - Map relationships between different roles and responsibilities
        - Ensure consistency with existing rule patterns and structures
        - Identify system-level implications and feedback loops
        - Consider long-term evolution and maintenance of rules
        
        TEMPORAL THINKING:
        Considering time-based aspects and evolution:
        - Identify time-sensitive requirements and deadlines
        - Consider how rules might evolve or change over time
        - Analyze retroactive vs prospective application
        - Examine temporal relationships between different obligations
        - Consider compliance timelines and implementation phases
        
        === INTEGRATION ===
        Now synthesizing insights from all thinking approaches to create:
        - Comprehensive rules that capture analytical precision
        - Creative solutions for complex legal concepts
        - Critically validated interpretations
        - Practically implementable requirements
        - Systematically consistent frameworks
        - Time-aware compliance structures
        
        Apply each thinking approach to extract comprehensive, actionable rules...
        """
    
    @staticmethod
    def mixture_of_reasoning_prompt(legislation_text: str, existing_context: str = "") -> str:
        """Mixture of Reasoning prompting for comprehensive analysis."""
        context_section = f"\n\nEXISTING RULES CONTEXT:\n{existing_context}\n" if existing_context else ""
        
        return f"""
        Use multiple reasoning strategies to thoroughly analyze this legislation.
        {context_section}
        LEGISLATION TEXT:
        {legislation_text}
        
        === REASONING STRATEGIES ===
        
        DEDUCTIVE REASONING:
        Starting from general principles to specific applications:
        - Begin with established legal principles and privacy frameworks
        - Apply general data protection concepts to specific provisions
        - Derive specific obligations and requirements from broad statements
        - Maintain consistency with established rule patterns and precedents
        - Use formal logical structures to ensure valid inferences
        - Apply standard interpretation methodologies from legal practice
        
        Example deductive chain:
        General Principle: "Data controllers must ensure lawful processing"
        Specific Provision: [Text from legislation]
        Derived Rule: [Specific conditional rule with precise conditions]
        
        INDUCTIVE REASONING:
        Building from specific examples to general patterns:
        - Examine specific examples and cases mentioned in the legislation
        - Identify recurring patterns and common elements across provisions
        - Generalize from specific instances to broader rules and principles
        - Learn from existing rule structures and successful implementations
        - Build comprehensive frameworks from individual observations
        - Identify emerging trends and novel requirements
        
        Pattern Recognition Process:
        - Collect specific instances: [List examples from text]
        - Identify common characteristics: [Pattern analysis]
        - Formulate general rules: [Generalized conditional statements]
        
        ABDUCTIVE REASONING:
        Inferring the best explanations for intended outcomes:
        - Observe the intended outcomes and policy goals of the legislation
        - Infer the most likely requirements needed to achieve these goals
        - Hypothesize necessary conditions and controls based on objectives
        - Consider primary and secondary role impacts to achieve balance
        - Generate plausible explanations for ambiguous or implicit requirements
        - Fill gaps with reasonable inferences about legislative intent
        
        Goal-Oriented Analysis:
        - Identified objectives: [Legislative goals and purposes]
        - Required conditions: [Inferred necessary conditions]
        - Implementing rules: [Rules designed to achieve objectives]
        
        ANALOGICAL REASONING:
        Drawing parallels from similar regulations and frameworks:
        - Compare to similar regulations (GDPR, CCPA, other privacy laws)
        - Draw parallels from established legal frameworks and precedents
        - Apply proven compliance patterns from related domains
        - Leverage existing rule precedents and successful implementations
        - Adapt solutions from analogous legal and regulatory contexts
        - Learn from both successes and failures in similar regulations
        
        Comparative Analysis:
        - Similar regulations: [Comparable legal frameworks]
        - Successful patterns: [Proven implementation approaches]
        - Adapted solutions: [Modified approaches for current context]
        
        CAUSAL REASONING:
        Understanding cause-and-effect relationships:
        - Identify clear cause-and-effect relationships in the legislation
        - Map triggers and conditions to required actions and outcomes
        - Understand consequences of non-compliance and enforcement mechanisms
        - Analyze data category implications and downstream effects
        - Trace decision trees and conditional logic chains
        - Model complex interdependencies and feedback loops
        
        Causal Chain Analysis:
        - Triggering conditions: [What initiates obligations]
        - Intermediate steps: [Processing and decision points]
        - Final outcomes: [Required actions and compliance states]
        
        PROBABILISTIC REASONING:
        Dealing with uncertainty and confidence levels:
        - Assess likelihood of different interpretations based on textual clarity
        - Assign confidence scores to extracted rules based on evidence strength
        - Handle ambiguous language with probabilistic interpretations
        - Consider uncertainty in role assignments and data categorizations
        - Use evidence-based confidence scoring for rule quality assessment
        - Account for multiple possible interpretations with weighted confidence
        
        Uncertainty Assessment:
        - High confidence elements: [Clear, explicit requirements]
        - Medium confidence elements: [Reasonably implied requirements]
        - Low confidence elements: [Ambiguous or inferred requirements]
        
        === COMPREHENSIVE SYNTHESIS ===
        Integrating all reasoning strategies to produce:
        - Deductively sound rules grounded in legal principles
        - Inductively derived patterns from comprehensive text analysis
        - Abductively inferred requirements aligned with legislative intent
        - Analogically informed solutions based on proven approaches
        - Causally coherent conditional logic and decision trees
        - Probabilistically calibrated confidence scores and uncertainty measures
        
        Apply each reasoning strategy to extract precise, enforceable rules that complement and enhance the existing rule base...
        """
    
    @staticmethod
    def contextual_analysis_prompt(legislation_text: str, specific_focus: str, existing_context: str = "") -> str:
        """Contextual analysis prompt for specific focus areas."""
        context_section = f"\n\nEXISTING RULES CONTEXT:\n{existing_context}\n" if existing_context else ""
        
        return f"""
        Conduct a focused contextual analysis of this legislation with specific attention to: {specific_focus}
        {context_section}
        LEGISLATION TEXT:
        {legislation_text}
        
        === CONTEXTUAL ANALYSIS FRAMEWORK ===
        
        PRIMARY FOCUS: {specific_focus}
        
        TEXTUAL CONTEXT ANALYSIS:
        - Examine the immediate textual context surrounding key provisions
        - Identify qualifying language, exceptions, and conditional statements
        - Analyze the relationship between different sections and subsections
        - Consider the semantic field and terminology consistency
        - Evaluate the precision and specificity of language used
        
        LEGAL CONTEXT ANALYSIS:
        - Consider the broader legal framework and regulatory ecosystem
        - Examine relationships with other applicable laws and regulations
        - Analyze precedential value and interpretation guidelines
        - Consider jurisdictional scope and applicable territories
        - Evaluate enforcement mechanisms and supervisory authorities
        
        OPERATIONAL CONTEXT ANALYSIS:
        - Assess practical implementation requirements and challenges
        - Consider different organizational contexts (size, sector, complexity)
        - Examine resource requirements and compliance costs
        - Analyze stakeholder impacts and change management needs
        - Consider technological and procedural implementation aspects
        
        TEMPORAL CONTEXT ANALYSIS:
        - Identify effective dates and transition periods
        - Consider evolution of requirements over time
        - Analyze relationship to existing compliance frameworks
        - Examine retroactive vs prospective application requirements
        - Consider future-proofing and adaptability needs
        
        RISK CONTEXT ANALYSIS:
        - Assess compliance risks and potential violations
        - Consider enforcement probability and penalty severity
        - Analyze reputational and operational risks
        - Examine risk mitigation strategies and controls
        - Consider risk-based approach to implementation priorities
        
        === FOCUSED EXTRACTION ===
        Based on the contextual analysis, extract rules that:
        - Address the specific focus area comprehensively
        - Account for all relevant contextual factors
        - Provide actionable compliance guidance
        - Integrate effectively with existing rule structures
        - Support risk-based implementation approaches
        
        Focus specifically on {specific_focus} while maintaining broader contextual awareness...
        """
    
    @staticmethod
    def validation_and_refinement_prompt(extracted_rules: List[Dict[str, Any]], 
                                       original_text: str, existing_context: str = "") -> str:
        """Validation and refinement prompt for extracted rules."""
        context_section = f"\n\nEXISTING RULES CONTEXT:\n{existing_context}\n" if existing_context else ""
        
        rules_json = "\n\n".join([f"RULE {i+1}:\n{rule}" for i, rule in enumerate(extracted_rules)])
        
        return f"""
        Validate and refine the following extracted rules against the original legislation text.
        {context_section}
        
        ORIGINAL LEGISLATION TEXT:
        {original_text}
        
        EXTRACTED RULES TO VALIDATE:
        {rules_json}
        
        === VALIDATION FRAMEWORK ===
        
        ACCURACY VALIDATION:
        For each rule, verify:
        - All facts are explicitly mentioned or clearly implied in the original text
        - Operators and values accurately reflect the legislative language
        - Roles and data categories are not fabricated or over-interpreted
        - Conditions are logically sound and properly structured
        - Events and actions are appropriate for the identified obligations
        
        COMPLETENESS VALIDATION:
        Check for:
        - Missing obligations or requirements from the original text
        - Incomplete condition sets that might miss important triggers
        - Overlooked stakeholder roles or responsibilities
        - Missing data categories or processing contexts
        - Gaps in the logical flow from conditions to actions
        
        CONSISTENCY VALIDATION:
        Ensure:
        - Internal consistency within each rule
        - Consistency across all extracted rules
        - Alignment with existing rule patterns and structures
        - Consistent terminology and concept usage
        - Logical coherence of the overall rule set
        
        PRECISION VALIDATION:
        Evaluate:
        - Appropriate level of granularity for each rule
        - Precision of conditional logic and trigger conditions
        - Specificity of actions and compliance requirements
        - Accuracy of confidence scores based on textual clarity
        - Proper assignment of priority levels
        
        IMPLEMENTABILITY VALIDATION:
        Assess:
        - Practical enforceability of extracted rules
        - Clarity of compliance requirements for implementers
        - Feasibility of monitoring and verification
        - Integration potential with existing compliance frameworks
        - Scalability across different organizational contexts
        
        === REFINEMENT REQUIREMENTS ===
        
        For each validation dimension, provide:
        1. IDENTIFIED ISSUES: Specific problems found in the extracted rules
        2. RECOMMENDED CORRECTIONS: Precise changes needed to fix issues
        3. ENHANCEMENT OPPORTUNITIES: Ways to improve rule quality and utility
        4. CONFIDENCE ADJUSTMENTS: Updates to confidence scores based on validation
        
        === OUTPUT FORMAT ===
        Provide refined rules in the same JSON format, with:
        - Corrected inaccuracies
        - Added missing elements
        - Improved consistency
        - Enhanced precision
        - Validated implementability
        - Updated confidence scores
        - Clear reasoning for all changes made
        
        Focus on maintaining fidelity to the original legislation while maximizing rule quality and utility...
        """
    
    @staticmethod
    def get_strategy_metadata(strategy_name: str) -> Dict[str, Any]:
        """Get metadata about a specific prompting strategy."""
        strategies = {
            "chain_of_thought": {
                "description": "Step-by-step analytical reasoning approach",
                "strengths": ["Systematic analysis", "Traceable logic", "Comprehensive coverage"],
                "best_for": ["Complex legal texts", "Multi-step obligations", "Detailed analysis"],
                "confidence_weight": 0.25
            },
            "mixture_of_experts": {
                "description": "Multiple specialized expert perspectives",
                "strengths": ["Diverse viewpoints", "Domain expertise", "Comprehensive coverage"],
                "best_for": ["Complex regulations", "Multi-stakeholder impacts", "Technical requirements"],
                "confidence_weight": 0.25
            },
            "mixture_of_thought": {
                "description": "Multiple cognitive approaches to analysis",
                "strengths": ["Creative insights", "Critical evaluation", "Practical focus"],
                "best_for": ["Ambiguous texts", "Innovation requirements", "Implementation challenges"],
                "confidence_weight": 0.25
            },
            "mixture_of_reasoning": {
                "description": "Multiple logical reasoning approaches",
                "strengths": ["Rigorous logic", "Pattern recognition", "Uncertainty handling"],
                "best_for": ["Formal analysis", "Pattern extraction", "Risk assessment"],
                "confidence_weight": 0.25
            }
        }
        
        return strategies.get(strategy_name, {})
    
    @staticmethod
    def get_all_strategies() -> List[str]:
        """Get list of all available prompting strategies."""
        return ["chain_of_thought", "mixture_of_experts", "mixture_of_thought", "mixture_of_reasoning"]
    
    @staticmethod
    def calculate_weighted_confidence(strategy_results: Dict[str, float]) -> float:
        """Calculate weighted confidence score from multiple strategy results."""
        total_weight = 0.0
        weighted_sum = 0.0
        
        for strategy, confidence in strategy_results.items():
            metadata = PromptingStrategies.get_strategy_metadata(strategy)
            weight = metadata.get("confidence_weight", 0.25)
            weighted_sum += confidence * weight
            total_weight += weight
        
        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return sum(strategy_results.values()) / len(strategy_results)