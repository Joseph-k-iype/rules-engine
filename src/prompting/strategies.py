"""
Anti-hallucination prompting strategies focused on dual action inference, decision-making, and whole document analysis.
Enhanced with decision inference capabilities for yes/no/maybe outcomes.
"""


class PromptingStrategies:
    """Anti-hallucination prompting strategies focused on dual action inference, decision-making, and whole document analysis."""

    @staticmethod
    def comprehensive_document_analysis_prompt(legislation_text: str, existing_context: str = "", level: str = "level_1", chunk_info: str = "") -> str:
        """Comprehensive document analysis prompt that ensures the entire document is understood."""
        context_section = f"\n\nEXISTING RULES CONTEXT:\n{existing_context}\n" if existing_context else ""
        chunk_section = f"\n\nCHUNK INFORMATION:\n{chunk_info}\n" if chunk_info else ""

        return f"""
        Perform a comprehensive analysis of this legislation text with strict adherence to what is stated.
        Read and understand the ENTIRE document before extracting any rules, conditions, or decisions.
        {context_section}{chunk_section}

        LEGISLATION TEXT TO ANALYZE:
        {legislation_text}

        COMPREHENSIVE ANALYSIS REQUIREMENTS:

        1. FULL DOCUMENT UNDERSTANDING:
        - Read the entire text from beginning to end
        - Identify all sections, articles, paragraphs, and subsections
        - Understand the overall structure and purpose of the legislation
        - Note cross-references between different parts of the document
        - Identify how different sections relate to each other

        2. EXTRACT ALL OBLIGATIONS FROM ENTIRE DOCUMENT:
        - Extract every obligation stated anywhere in the text
        - Identify who has each obligation (controller, processor, joint_controller, data_subject)
        - Note the exact text that creates each obligation
        - Link related obligations across different sections
        - Use simple, clear English without legal jargon or document references

        3. IDENTIFY ALL CONDITIONS AND TRIGGERS:
        - Find all conditions that trigger obligations throughout the document
        - Note data-related triggers (data types, processing activities, transfers)
        - Extract factual conditions that can be evaluated
        - Identify when conditions in one section affect obligations in another

        4. COMPREHENSIVE DATA REQUIREMENTS:
        - Identify all requirements for data handling mentioned anywhere
        - Note all data categories mentioned throughout the text
        - Extract all data processing operations referenced
        - Map data requirements to specific obligations

        5. COMPREHENSIVE ROLE AND RESPONSIBILITY MAPPING:
        - Identify every role mentioned in the document
        - Map all responsibilities to each role
        - Note how roles interact with each other
        - Identify role-specific obligations throughout the document

        6. COMPREHENSIVE DATA CATEGORY IDENTIFICATION:
        - Find every data category mentioned in the document
        - Note specific data types and classifications
        - Identify sensitive data categories
        - Map data categories to processing requirements

        7. DECISION SCENARIO IDENTIFICATION:
        - Identify scenarios where decisions must be made
        - Find conditions that lead to different outcomes
        - Note situations with conditional permissions or prohibitions
        - Identify cross-border transfer scenarios and their conditions
        - Extract compliance assessment situations
        - Find data processing authorization scenarios

        CRITICAL: Analyze the ENTIRE document as a whole. Do not focus on individual sections in isolation.
        Extract information present throughout the complete legislation text. Do not infer beyond what is directly stated.
        Ensure your analysis reflects understanding of the full document context.
        Use simple, clear English without referencing specific document levels or guidance documents.
        """

    @staticmethod
    def focused_analysis_prompt(legislation_text: str, existing_context: str = "", level: str = "level_1", chunk_info: str = "") -> str:
        """Focused analysis prompt that minimizes hallucination and includes decision identification."""
        context_section = f"\n\nEXISTING RULES CONTEXT:\n{existing_context}\n" if existing_context else ""
        chunk_section = f"\n\nCHUNK INFORMATION:\n{chunk_info}\n" if chunk_info else ""

        return f"""
        Analyze this legislation text with strict adherence to what is stated.
        {context_section}{chunk_section}

        LEGISLATION TEXT TO ANALYZE:
        {legislation_text}

        ANALYSIS REQUIREMENTS:

        1. IDENTIFY EXPLICIT OBLIGATIONS:
        - Extract only obligations stated in the text
        - Identify who has each obligation (controller, processor, joint_controller, data_subject)
        - Note the exact text that creates each obligation
        - Use simple, clear English without legal jargon or document references

        2. EXTRACT CONDITIONS AND TRIGGERS:
        - Identify conditions that trigger obligations
        - Note data-related triggers (data types, processing activities, transfers)
        - Extract factual conditions that can be evaluated

        3. DETERMINE DATA-SPECIFIC REQUIREMENTS:
        - Identify requirements for data handling
        - Note data categories mentioned in the text
        - Extract data processing operations referenced

        4. INFER DUAL ACTIONS (BASED ON TEXT):
        - For each obligation, identify what rule actions must be taken (organizational/policy level)
        - For each obligation, identify what user actions can be taken (individual/practical level)
        - Focus on actions involving data processing, storage, transfer, or deletion
        - Base actions on requirements in the legislation
        - Ensure actions are practical and implementable
        - Use simple, clear English without legal jargon or document references

        5. IDENTIFY DECISION SCENARIOS:
        - Find scenarios where yes/no/maybe decisions must be made
        - Identify conditional permissions (allowed if conditions are met)
        - Extract conditional prohibitions (forbidden unless conditions are met)
        - Note cross-border transfer decision points
        - Identify compliance assessment scenarios
        - Find data processing authorization scenarios
        - Use simple, clear English without legal jargon or document references

        Extract information present in the legislation text. Do not infer beyond what is directly stated.
        Focus on logical statements and practical scenarios without ambiguous references.
        """

    @staticmethod
    def expert_verification_prompt(legislation_text: str, preliminary_analysis: str, level: str = "level_1") -> str:
        """Expert verification prompt to validate findings against source text."""

        return f"""
        Verify the preliminary analysis against the source legislation.

        SOURCE LEGISLATION:
        {legislation_text}

        PRELIMINARY ANALYSIS TO VERIFY:
        {preliminary_analysis}

        VERIFICATION TASKS:

        1. ACCURACY CHECK:
        - Verify each identified obligation exists in the source text
        - Confirm conditions and triggers are accurately extracted
        - Validate data categories and processing operations mentioned
        - Ensure language is simple and clear without document references

        2. COMPLETENESS REVIEW:
        - Identify any explicit obligations that were missed
        - Check for data-specific requirements not captured
        - Verify all relevant roles and responsibilities are identified

        3. DUAL ACTION VALIDATION:
        - Confirm each proposed rule action is supported by the legislation text
        - Confirm each proposed user action is practical and based on legislation
        - Verify actions are specific to data handling requirements
        - Ensure actions can be performed by appropriate entities
        - Check that language is in simple English without document references

        4. DECISION SCENARIO VALIDATION:
        - Confirm each identified decision scenario exists in the source text
        - Verify conditions for different outcomes (yes/no/maybe) are accurate
        - Ensure decision logic is based on explicit legislative requirements
        - Check that scenarios are described in simple, clear English

        5. REMOVE UNSUPPORTED ELEMENTS:
        - Flag any elements not supported by the source text
        - Remove elements that cannot be traced to specific legislative language
        - Remove references to guidance documents or document levels

        Provide corrected analysis that adheres to the source legislation text.
        Use simple, clear English throughout without ambiguous document references.
        """

    @staticmethod
    def decision_inference_prompt(legislation_text: str, focused_analysis: str, agent_analysis: str) -> str:
        """Specific prompt for inferring decision scenarios with yes/no/maybe outcomes."""

        return f"""
        Based on the legislation text and previous analysis, identify all decision scenarios that can result in yes, no, or maybe outcomes.

        LEGISLATION TEXT:
        {legislation_text}

        FOCUSED ANALYSIS:
        {focused_analysis}

        AGENT ANALYSIS:
        {agent_analysis}

        DECISION INFERENCE REQUIREMENTS:

        1. IDENTIFY DECISION SCENARIOS:
        - Find situations where permissions must be granted or denied
        - Identify cross-border data transfer decision points
        - Extract data processing authorization scenarios
        - Find compliance assessment situations
        - Identify consent requirement scenarios
        - Note access permission situations

        2. DETERMINE DECISION OUTCOMES:
        For each scenario, identify:
        - CONDITIONS FOR YES: What must be true for permission/approval
        - CONDITIONS FOR NO: What would result in denial/prohibition
        - CONDITIONS FOR MAYBE: What would require additional actions before approval

        3. LINK TO REQUIRED ACTIONS:
        - For YES outcomes: What actions confirm compliance
        - For MAYBE outcomes: What actions are needed to achieve YES
        - For NO outcomes: What would need to change for a different outcome

        4. DECISION EXAMPLES TO IDENTIFY:
        - Data transfer between countries (maybe = requires adequate protection)
        - Processing sensitive data (maybe = requires explicit consent)
        - Sharing data with third parties (maybe = requires contractual safeguards)
        - Automated decision making (maybe = requires human oversight)
        - Cross-border processing (maybe = requires adequate jurisdiction)
        - Data retention (maybe = requires legitimate purpose)

        5. OUTPUT FORMAT:
        For each decision scenario, provide:
        - scenario: Clear description in simple English
        - decision_type: Type of decision (data_transfer, data_processing, etc.)
        - decision_context: Context (cross_border_transfer, internal_processing, etc.)
        - outcome: Primary outcome based on current conditions (yes/no/maybe)
        - conditions_for_yes: List of conditions that would result in yes
        - conditions_for_no: List of conditions that would result in no
        - conditions_for_maybe: List of conditions that would result in maybe
        - required_actions_for_yes: Actions needed for yes outcome
        - required_actions_for_maybe: Actions needed to move from maybe to yes
        - rationale: Clear explanation of the decision logic
        - applicable_data_categories: Data types this applies to
        - applicable_roles: Roles affected by this decision
        - cross_border: Whether this involves cross-border operations

        CRITICAL REQUIREMENTS:
        - Base all decisions on explicit text in the legislation
        - Use simple, clear English without legal jargon
        - Do not reference document levels or guidance documents
        - Focus on practical, implementable scenarios
        - Ensure decisions are logical and traceable to source text
        - Provide clear rationale for each decision outcome

        Return a JSON array of decision objects based on the legislation text.
        """

    @staticmethod
    def synthesis_prompt_template(
        legislation_text: str,
        article_reference: str,
        source_files: str,
        document_level: str,
        chunk_reference: str,
        existing_context: str,
        metadata_context: str,
        applicable_countries: str,
        adequacy_countries: str,
        focused_analysis: str,
        verified_analysis: str,
        agent_analysis: str,
        comprehensive_analysis: str,
        decision_analysis: str = ""
    ) -> str:
        """Template for synthesis prompt with all analyses including decisions."""

        chunk_context = f"\nCHUNK REFERENCE: {chunk_reference}\n" if chunk_reference else ""
        decision_context = f"\nDECISION ANALYSIS:\n{decision_analysis}\n" if decision_analysis else ""

        return f"""
        Based on the analyses below, create machine-readable rules with MAXIMUM COMPREHENSIVENESS including decision support.
        Extract EVERY possible rule, obligation, condition, requirement, and decision scenario from the legislation text.
        Create multiple rules if the text covers different aspects or scenarios.

        EXISTING RULES CONTEXT:
        {existing_context}

        METADATA CONTEXT:
        {metadata_context}{chunk_context}

        COMPREHENSIVE DOCUMENT ANALYSIS:
        {comprehensive_analysis}

        SOURCE LEGISLATION:
        Article: {article_reference}
        Document Level: {document_level}
        Source Files: {source_files}
        Text: {legislation_text}

        ANALYSIS RESULTS:

        Focused Analysis:
        {focused_analysis}

        Expert Verification:
        {verified_analysis}

        Agent Dual Action Analysis:
        {agent_analysis}
        {decision_context}

        COMPREHENSIVE EXTRACTION REQUIREMENTS:
        1. Extract EVERY obligation, requirement, prohibition, permission mentioned
        2. Create separate rules for different roles (controller, processor, data_subject, joint_controller)
        3. Create separate rules for different data categories mentioned
        4. Create separate rules for different scenarios or conditions
        5. Create rules for both positive obligations (must do) and negative obligations (must not do)
        6. Extract rules for different timeframes if mentioned (immediate, within X days, etc.)
        7. Create rules for different jurisdictions if multiple countries are mentioned
        8. Extract both explicit and reasonably implied obligations
        9. Focus on practical data operations and create actionable rules
        10. Create comprehensive conditions that capture all requirements
        11. Include decision scenarios with yes/no/maybe outcomes
        12. Link decisions to required actions for compliance
        
        SYNTHESIS REQUIREMENTS:
        1. Create rules in json-rules-engine format
        2. Each condition must reference the document level: "{document_level}"
        3. Each condition must include chunk_reference if applicable: {chunk_reference}
        4. MANDATORY: Each rule MUST have primary_impacted_role and data_category fields populated
        5. Actions must reference specific articles and be in simple English without document references
        6. Actions must focus on practical data operations (encryption, masking, access controls, etc.)
        7. User actions must be practical tasks individuals can perform
        8. Use exact enum values for all structured fields
        9. Timeline is optional - include only if mentioned in legislation
        10. Include detailed reasoning for each rule showing exactly which part of the text supports it
        11. Include decision scenarios with clear yes/no/maybe logic
        12. Use simple, clear English without legal jargon or document references

        CRITICAL FIELD REQUIREMENTS:
        - primary_impacted_role: MUST be one of: "controller", "processor", "joint_controller", "data_subject"
        - secondary_impacted_role: Optional, same values as above
        - data_category: MUST be array with values like: "personal_data", "sensitive_data", "biometric_data", "health_data", "financial_data", "location_data", "behavioral_data", "identification_data"

        DECISION REQUIREMENTS:
        - Extract decision scenarios that result in yes/no/maybe outcomes
        - Link decisions to specific conditions and required actions
        - Ensure decisions are practical and implementable
        - Base decisions on explicit legislative requirements
        - Include cross-border transfer decisions
        - Include data processing authorization decisions
        - Include compliance assessment decisions

        REASONING REQUIREMENTS:
        Each rule must include in its description or metadata exactly which part of the legislation text it was derived from and why.
        
        COMPREHENSIVE RULE CREATION:
        Create multiple rules rather than trying to combine everything into one rule.
        If the text mentions different obligations for controllers vs processors, create separate rules.
        If the text mentions different requirements for different data types, create separate rules.
        If the text has both immediate and long-term requirements, create separate rules.
        If the text contains decision scenarios, create rules with corresponding decisions.
        
        CRITICAL: Return ONLY a valid JSON array of rules. Create as many rules as necessary to comprehensively cover all obligations and decisions in the text.

        [
          {{
            "id": "unique_rule_id_1",
            "name": "Rule Name for Specific Obligation",
            "description": "Specific rule description derived from exact text reference",
            "source_article": "{article_reference}",
            "source_file": "filename",
            "priority": 1,
            "confidence_score": 0.8,
            "primary_impacted_role": "controller",
            "secondary_impacted_role": "processor",
            "data_category": ["personal_data", "sensitive_data"],
            "applicable_countries": {applicable_countries},
            "adequacy_countries": {adequacy_countries},
            "source_documents": {source_files},
            "rule_derivation_reasoning": "This rule was derived from the text that states specific requirement which creates an obligation for specific role to take specific action",
            "conditions": {{
              "all": [
                {{
                  "fact": "specific_condition_fact",
                  "operator": "equal",
                  "value": "condition_value",
                  "description": "Condition based on specific legislative requirement",
                  "data_domain": ["data_usage"],
                  "role": "controller",
                  "reasoning": "This condition derived from article text which establishes requirement for specific scenario",
                  "document_level": "{document_level}",
                  "chunk_reference": "{chunk_reference or 'none'}"
                }}
              ]
            }},
            "event": {{
              "type": "compliance_required",
              "params": {{}}
            }},
            "actions": [
              {{
                "id": "action_id_1",
                "action_type": "specific_data_operation",
                "title": "Specific Data Protection Action",
                "description": "Implement specific data protection measure as required by legislation",
                "priority": "medium",
                "data_specific_steps": ["Specific step 1", "Specific step 2", "Specific step 3"],
                "responsible_role": "controller",
                "legislative_requirement": "Exact requirement from legislation",
                "data_impact": "Specific impact on data processing",
                "verification_method": ["Method 1", "Method 2"],
                "timeline": "optional timeline if specified",
                "derived_from_text": "Exact text from legislation that requires this action",
                "applicable_countries": {applicable_countries},
                "confidence_score": 0.8
              }}
            ],
            "user_actions": [
              {{
                "id": "user_action_id_1",
                "action_type": "user_specific_data_operation",
                "title": "User Data Protection Task",
                "description": "Specific task users must perform based on legislation",
                "priority": "medium",
                "user_data_steps": ["User step 1", "User step 2", "User step 3"],
                "affected_data_categories": ["personal_data", "sensitive_data"],
                "user_role_context": "data_subject",
                "legislative_requirement": "Exact requirement from legislation",
                "compliance_outcome": "Specific compliance outcome achieved",
                "user_verification_steps": ["Verification 1", "Verification 2"],
                "timeline": "optional timeline if specified",
                "derived_from_text": "Exact text from legislation that requires this user action",
                "confidence_score": 0.8
              }}
            ],
            "decisions": [
              {{
                "id": "decision_id_1",
                "decision_type": "data_transfer",
                "decision_context": "cross_border_transfer",
                "outcome": "maybe",
                "scenario": "Transfer of personal data from Country A to Country B",
                "conditions_for_yes": ["Adequate protection measures in place", "Data subject consent obtained"],
                "conditions_for_no": ["No adequate protection", "Data subject objects"],
                "conditions_for_maybe": ["Adequate protection can be implemented", "Additional safeguards needed"],
                "required_actions_for_yes": ["Verify adequate protection", "Document consent"],
                "required_actions_for_maybe": ["Implement data masking", "Establish contractual safeguards"],
                "rationale": "Legislation allows cross-border transfer only with adequate protection or additional safeguards",
                "decision_factors": ["Adequacy status of target country", "Data sensitivity level"],
                "applicable_data_categories": ["personal_data"],
                "applicable_roles": ["controller"],
                "source_jurisdiction": "Country A",
                "target_jurisdiction": "Country B",
                "cross_border": true,
                "derived_from_text": "Exact text from legislation that creates this decision scenario",
                "confidence_score": 0.8
              }}
            ]
          }},
          {{
            "id": "unique_rule_id_2",
            "name": "Another Rule for Different Obligation",
            ...
          }}
        ]

        IMPORTANT RULES:
        - Create MULTIPLE rules to comprehensively cover all obligations and decisions
        - Each rule should focus on a specific obligation or requirement
        - Include detailed reasoning and text references for each rule
        - primary_impacted_role and data_category fields are MANDATORY
        - ALL list fields MUST be arrays, never strings
        - Actions must reference the specific article: {article_reference}
        - Actions must be in simple English without legal jargon or document references
        - Focus on practical data operations
        - Include decision scenarios with clear yes/no/maybe logic
        - Link decisions to specific actions and conditions
        - Return ONLY the JSON array, no other text or markdown

        Be comprehensive - it's better to create more specific rules than to miss obligations or decisions.
        """

    @staticmethod
    def role_inference_prompt(legislation_text: str) -> str:
        """Prompt for inferring primary impacted role from legislation text."""
        return f"""
        Based on the following legislation text, identify the PRIMARY role most impacted by the requirements:

        Text: {legislation_text}

        Analyze the text and determine which role has the most significant obligations or is most directly addressed:
        - controller: Data controllers who determine purposes and means of processing
        - processor: Data processors who process data on behalf of controllers  
        - joint_controller: Joint data controllers who jointly determine purposes and means
        - data_subject: Individual data subjects whose data is being processed

        Return ONLY one of these four values based on which role is most prominently featured or has the most obligations in this specific text.
        If multiple roles are equally prominent, choose "controller" as the default.
        """

    @staticmethod
    def data_category_inference_prompt(legislation_text: str) -> str:
        """Prompt for inferring data categories from legislation text."""
        return f"""
        Based on the following legislation text, identify which data categories are mentioned or implied:

        Text: {legislation_text}

        Identify any of these data categories that are mentioned or clearly implied in the text:
        - personal_data: General personal data
        - sensitive_data: Special categories of personal data
        - biometric_data: Biometric identifiers
        - health_data: Health and medical data
        - financial_data: Financial and payment data
        - location_data: Location and tracking data
        - behavioral_data: Behavioral profiling data
        - identification_data: Identity verification data

        Return a JSON array with the categories that are mentioned in the text.
        If no specific categories are mentioned but the text refers to "personal data" generally, return ["personal_data"].
        If no data categories can be identified, return ["personal_data"] as the default.

        Example response: ["personal_data", "sensitive_data"]
        """

@staticmethod
def odrl_comprehensive_guidance_analysis(
    guidance_text: str,
    rule_name: str,
    framework_type: str,
    restriction_condition: str
) -> str:
    """
    Stage 1: Comprehensive analysis of guidance text for ODRL extraction.
    Similar to comprehensive_document_analysis_prompt but focused on ODRL requirements.
    """
    return f"""
    You are a legal and data protection expert analyzing regulatory guidance for ODRL policy creation.
    
    RULE CONTEXT:
    - Rule Name: {rule_name}
    - Framework: {framework_type}
    - Type: {restriction_condition}
    
    GUIDANCE TEXT TO ANALYZE (READ COMPLETELY):
    {guidance_text}
    
    COMPREHENSIVE ANALYSIS REQUIREMENTS:
    
    1. OVERALL UNDERSTANDING:
       - What is the main objective of this rule?
       - What problem or risk does it address?
       - What is the scope of applicability (who, what, when, where)?
       - Are there any exceptions or exemptions?
    
    2. IDENTIFY KEY OBLIGATIONS:
       - What MUST be done (mandatory actions)?
       - What MUST NOT be done (prohibitions)?
       - What SHOULD be done (recommendations)?
       - What CAN be done (permissions with conditions)?
    
    3. IDENTIFY CONDITIONS AND CONSTRAINTS:
       - Under what circumstances does this apply?
       - What are the limitations or restrictions?
       - Are there temporal constraints (time limits, deadlines, durations)?
       - Are there spatial constraints (geographic, jurisdictional)?
       - Are there quantitative constraints (limits, thresholds)?
       - Are there qualitative constraints (purpose, context, recipient type)?
    
    4. IDENTIFY DATA ASPECTS:
       - What types of data are involved?
       - Who does the data concern (data subjects)?
       - What operations can be performed on the data?
       - Are there special data categories requiring enhanced protection?
    
    5. IDENTIFY PARTIES AND ROLES:
       - Who is responsible for compliance (assigner)?
       - Who is affected by this rule (assignee)?
       - Are there controllers, processors, joint controllers?
       - Are data subjects mentioned as active parties?
       - Are there third parties involved?
    
    6. IDENTIFY EVIDENCE AND VERIFICATION:
       - What evidence is needed to demonstrate compliance?
       - How can compliance be verified or audited?
       - What documentation must be maintained?
       - What records are required?
    
    7. IDENTIFY PURPOSES AND LEGAL BASIS:
       - What is the stated purpose of data processing?
       - What legal basis is mentioned or implied?
       - Are there purpose limitations?
    
    CRITICAL REQUIREMENTS:
    - Provide a comprehensive, structured analysis in clear English
    - Focus on extracting actionable, machine-readable information
    - Be precise and base EVERYTHING on the actual guidance text
    - Do not infer beyond what is directly stated or clearly implied
    - Identify ambiguities or areas requiring clarification
    - Use simple, clear language without legal jargon
    
    Your analysis should enable precise ODRL policy creation in subsequent stages.
    """


@staticmethod
def odrl_component_extraction(
    guidance_text: str,
    rule_name: str,
    initial_analysis: str
) -> str:
    """
    Stage 2: Extract ODRL-specific components (permissions, prohibitions, duties, constraints).
    Follows the focused_analysis_prompt pattern with ODRL terminology.
    """
    return f"""
    Based on the guidance text and comprehensive analysis, extract ODRL policy components.
    
    RULE: {rule_name}
    
    INITIAL COMPREHENSIVE ANALYSIS:
    {initial_analysis}
    
    ORIGINAL GUIDANCE TEXT (reference as needed):
    {guidance_text}
    
    ODRL COMPONENT EXTRACTION:
    
    Extract information using ODRL terminology and structure:
    
    1. ACTIONS (use ODRL standard actions where possible):
       Standard ODRL actions: use, transfer, distribute, reproduce, modify, delete, 
       read, write, execute, play, display, print, stream, sell, give, lend, share, 
       derive, annotate, archive
       
       Custom actions: collect, store, process, anonymize, pseudonymize, profile, etc.
       
       - What specific actions are mentioned in the guidance?
       - Use standard ODRL action vocabulary when applicable
       - Define custom actions when standard ones don't fit
    
    2. PERMISSIONS (what is ALLOWED):
       - What actions are explicitly permitted?
       - Under what conditions are they permitted?
       - Are there duties that must be fulfilled to exercise the permission?
       - Who grants the permission (assigner)?
       - Who receives the permission (assignee)?
       - What asset/target does the permission apply to?
       
       Structure each permission with:
       - Action(s) permitted
       - Target (what the action applies to)
       - Constraints (conditions that must be met)
       - Duties (obligations for exercising the permission)
       - Parties (assigner, assignee)
    
    3. PROHIBITIONS (what is FORBIDDEN):
       - What actions are explicitly prohibited?
       - Under what circumstances are they prohibited?
       - Are there exceptions to the prohibitions?
       - Who sets the prohibition (assigner)?
       - Who is subject to the prohibition (assignee)?
       - What asset/target does the prohibition apply to?
       
       Structure each prohibition with:
       - Action(s) prohibited
       - Target (what the action applies to)
       - Constraints (conditions under which prohibition applies)
       - Parties (assigner, assignee)
    
    4. CONSTRAINTS (conditions on permissions/prohibitions):
       Types of constraints to identify:
       
       a) TEMPORAL CONSTRAINTS:
          - dateTime: specific date/time
          - delayPeriod: delay before action
          - elapsedTime: time since event
          - timeInterval: recurring time period
       
       b) SPATIAL CONSTRAINTS:
          - spatial: geographic location
          - jurisdiction: legal jurisdiction
       
       c) QUANTITATIVE CONSTRAINTS:
          - count: number of times/items
          - percentage: percentage limit
          - fileSize: size limit
       
       d) QUALITATIVE CONSTRAINTS:
          - purpose: intended use
          - industry: industry sector
          - recipient: type of recipient
          - deliveryChannel: method of delivery
       
       For each constraint, identify:
       - leftOperand (what is being constrained)
       - operator (eq, neq, gt, lt, gteq, lteq, isPartOf, etc.)
       - rightOperand (the value/condition)
    
    5. DUTIES AND OBLIGATIONS:
       - What must be done BEFORE an action can be performed (pre-conditions)?
       - What must be done AFTER an action is performed (post-conditions)?
       - What ongoing obligations exist?
       - How are duties linked to permissions?
       
       Examples: provide attribution, obtain consent, compensate, notify, 
       delete after use, report usage, etc.
    
    6. PARTIES AND ROLES:
       - Assigner: entity that grants permission or sets prohibition
       - Assignee: entity that receives permission or is subject to prohibition
       - Controller: determines purposes and means of processing
       - Processor: processes data on behalf of controller
       - Data Subject: individual whose data is processed
       - Third Party: any other relevant party
       
       Identify specific parties mentioned in guidance or role types.
    
    CRITICAL EXTRACTION REQUIREMENTS:
    - Extract ONLY what is explicitly stated in the guidance text
    - Use ODRL standard terminology precisely
    - Provide specific references to guidance text for each extraction
    - If information is ambiguous, note the ambiguity
    - Focus on creating machine-readable, structured output
    - Maintain clear distinction between permissions and prohibitions
    - Link constraints to the specific rules they affect
    
    Provide detailed extraction with specific text references to support each component.
    """


@staticmethod
def odrl_constraint_analysis(
    guidance_text: str,
    rule_name: str,
    odrl_extraction: str
) -> str:
    """
    Stage 3: Detailed constraint analysis with ODRL-compliant structure.
    Similar to expert_verification_prompt but specialized for constraints.
    """
    return f"""
    Perform detailed constraint analysis for ODRL policy creation.
    
    RULE: {rule_name}
    
    ODRL COMPONENT EXTRACTION:
    {odrl_extraction}
    
    ORIGINAL GUIDANCE TEXT (verify against):
    {guidance_text}
    
    DETAILED CONSTRAINT ANALYSIS:
    
    For EACH constraint identified in the ODRL extraction, create a precise,
    machine-readable structure following ODRL 2.2 specification:
    
    1. CONSTRAINT TYPE CLASSIFICATION:
       
       TEMPORAL CONSTRAINTS (time-related):
       - dateTime: absolute date/time (ISO 8601 format)
         Example: "must be completed by 2025-12-31T23:59:59Z"
       - delayPeriod: delay before action (ISO 8601 duration)
         Example: "wait 30 days after request" → P30D
       - elapsedTime: time since event (ISO 8601 duration)
         Example: "within 72 hours of collection" → PT72H
       - timeInterval: recurring period (ISO 8601)
         Example: "every 6 months" → R/P6M
       
       SPATIAL CONSTRAINTS (location/jurisdiction):
       - spatial: geographic constraint
         Example: "only within EU" → leftOperand: spatial, rightOperand: EU
       - jurisdiction: legal jurisdiction
         Example: "under GDPR jurisdiction"
       
       QUANTITATIVE CONSTRAINTS (numerical):
       - count: number of times/items
         Example: "maximum 5 copies" → leftOperand: count, operator: lteq, rightOperand: 5
       - percentage: percentage constraint
         Example: "no more than 10%" → leftOperand: percentage, operator: lteq, rightOperand: 10
       
       QUALITATIVE CONSTRAINTS (purpose/context):
       - purpose: intended purpose
         Example: "only for research" → leftOperand: purpose, operator: eq, rightOperand: research
       - recipient: type of recipient
         Example: "only to affiliates" → leftOperand: recipient, operator: isPartOf, rightOperand: affiliates
    
    2. CONSTRAINT STRUCTURE (ODRL format):
       For each constraint, provide:
       
       {{
         "leftOperand": "ODRL left operand URI or custom operand",
         "operator": "eq|neq|gt|lt|gteq|lteq|isPartOf|isA|isAllOf|isAnyOf|isNoneOf",
         "rightOperand": "value (string, number, URI, or list)",
         "description": "clear explanation of constraint in simple English",
         "scope": "permission|prohibition|duty - what rule this constraint applies to"
       }}
       
       CRITICAL: Each component must be precise and machine-readable
    
    3. CONSTRAINT OPERATORS (use correctly):
       - eq (equal): exact match required
       - neq (not equal): must not match
       - gt (greater than): numerical comparison, exclusive
       - lt (less than): numerical comparison, exclusive
       - gteq (greater than or equal): numerical comparison, inclusive
       - lteq (less than or equal): numerical comparison, inclusive
       - isPartOf: value must be part of specified set/region
       - isA: value must be instance of specified type
       - isAllOf: value must match all of specified set
       - isAnyOf: value must match any of specified set
       - isNoneOf: value must match none of specified set
    
    4. CONSTRAINT SCOPE AND APPLICATION:
       - Does this constraint apply to a permission, prohibition, or duty?
       - Is the constraint mandatory (MUST) or optional (SHOULD)?
       - What happens if the constraint is violated?
       - Are there any exceptions to the constraint?
    
    5. CONSTRAINT RELATIONSHIPS:
       - Do multiple constraints apply together (AND logic)?
       - Are constraints alternatives (OR logic)?
       - Are there hierarchical constraints (constraint on constraint)?
       - How do constraints interact with each other?
    
    EXAMPLES OF WELL-STRUCTURED CONSTRAINTS:
    
    Example 1: "Data can only be used for educational purposes"
    {{
      "leftOperand": "purpose",
      "operator": "eq",
      "rightOperand": "education",
      "description": "Data usage restricted to educational purposes only",
      "scope": "permission"
    }}
    
    Example 2: "Processing must occur within the EU"
    {{
      "leftOperand": "spatial",
      "operator": "isPartOf",
      "rightOperand": "EU",
      "description": "Data processing limited to European Union territories",
      "scope": "permission"
    }}
    
    Example 3: "Data must be deleted after 30 days"
    {{
      "leftOperand": "elapsedTime",
      "operator": "gt",
      "rightOperand": "P30D",
      "description": "Data retention limited to maximum 30 days",
      "scope": "duty"
    }}
    
    Example 4: "Transfer prohibited to countries without adequacy decision"
    {{
      "leftOperand": "recipient",
      "operator": "isNoneOf",
      "rightOperand": ["countries_without_adequacy"],
      "description": "Data transfer forbidden to jurisdictions lacking adequacy decisions",
      "scope": "prohibition"
    }}
    
    VERIFICATION REQUIREMENTS:
    - Verify each constraint against original guidance text
    - Ensure constraint structure is complete and valid
    - Confirm operator is appropriate for the operands
    - Check that rightOperand format matches leftOperand type
    - Validate that scope correctly identifies affected rule
    
    Provide comprehensive constraint analysis with ODRL-compliant structure
    for ALL constraints identified in the guidance text.
    """


@staticmethod
def odrl_data_category_identification(
    guidance_text: str,
    rule_name: str,
    constraint_analysis: str
) -> str:
    """
    Stage 4: Comprehensive data category identification.
    Extends data_category_inference_prompt for ODRL context.
    """
    return f"""
    Identify ALL data categories mentioned or reasonably implied in the guidance.
    
    RULE: {rule_name}
    
    CONSTRAINT ANALYSIS:
    {constraint_analysis}
    
    ORIGINAL GUIDANCE TEXT:
    {guidance_text}
    
    COMPREHENSIVE DATA CATEGORY IDENTIFICATION:
    
    Identify all types of data with precision and completeness:
    
    1. GENERAL PERSONAL DATA CATEGORIES:
       - Personal data (any information relating to identified/identifiable person)
       - Non-personal data (anonymized, aggregated, non-identifying)
       - Pseudonymized data (indirectly identifiable with additional information)
       - Anonymized data (cannot be re-identified)
    
    2. SPECIAL CATEGORIES (SENSITIVE DATA) - GDPR Article 9:
       - Health data (physical/mental health, medical records)
       - Biometric data (unique identification: fingerprints, facial, iris, voice)
       - Genetic data (inherited/acquired genetic characteristics)
       - Racial or ethnic origin data
       - Political opinions data
       - Religious or philosophical beliefs data
       - Trade union membership data
       - Data concerning sex life or sexual orientation
       - Criminal conviction and offences data
    
    3. SPECIFIC DATA TYPE CATEGORIES:
       
       FINANCIAL & ECONOMIC:
       - Financial data (banking, transactions, assets)
       - Payment data (credit cards, payment methods)
       - Credit data (credit history, scores, reports)
       - Economic data (income, wealth, financial status)
       
       LOCATION & MOVEMENT:
       - Location data (GPS, geolocation, positioning)
       - Tracking data (movement patterns, travel history)
       - Geographic data (addresses, coordinates)
       
       BEHAVIORAL & PROFILING:
       - Behavioral data (patterns, preferences, habits)
       - Profiling data (analyzed characteristics, predictions)
       - Analytics data (usage patterns, engagement metrics)
       - Preference data (choices, settings, interests)
       
       CONTACT & COMMUNICATION:
       - Contact data (email, phone, address, social media)
       - Communication data (messages, emails, call logs)
       - Correspondence data (letters, communications)
       
       IDENTIFICATION & CREDENTIALS:
       - Identification data (ID numbers, passports, licenses)
       - Authentication data (passwords, biometrics for auth)
       - Credential data (certifications, qualifications)
       
       TRANSACTIONAL & OPERATIONAL:
       - Transactional data (purchases, orders, invoices)
       - Operational data (system logs, operations)
       - Usage data (service usage, consumption)
       
       DEVICE & TECHNICAL:
       - Device data (IP addresses, device IDs, MAC addresses)
       - Cookie data (tracking cookies, session data)
       - Technical data (browser info, OS, device specs)
       - Log data (access logs, error logs, system logs)
       
       DEMOGRAPHIC & SOCIAL:
       - Demographic data (age, gender, nationality)
       - Socioeconomic data (education, occupation, income level)
       - Family data (marital status, dependents)
       
       EMPLOYMENT & PROFESSIONAL:
       - Employment data (job history, employer, position)
       - Professional data (skills, experience, performance)
       - HR data (salary, benefits, evaluations)
       
       EDUCATIONAL & ACADEMIC:
       - Educational data (grades, transcripts, courses)
       - Academic data (research, publications, degrees)
       - Student data (enrollment, attendance)
    
    4. DATA CATEGORIZED BY PURPOSE/USE:
       - Marketing data (data used for marketing/advertising)
       - Research data (data used for research purposes)
       - Statistical data (data used for statistics)
       - Operational data (data for service operation)
       - Archival data (historical/archived data)
       - Training data (data for ML/AI training)
    
    5. DATA CATEGORIZED BY STATE:
       - Active data (currently in use)
       - Archived data (stored for retention)
       - Backup data (copies for recovery)
       - Temporary data (session/cache data)
    
    IDENTIFICATION METHODOLOGY:
    
    For EACH data category identified:
    
    {{
      "category_name": "Precise category name",
      "description": "Brief description based on guidance context",
      "sensitivity_level": "normal|sensitive|highly_sensitive",
      "evidence": "Exact text from guidance that indicates this category",
      "reasoning": "Why this category was identified",
      "confidence": "high|medium|low"
    }}
    
    IDENTIFICATION RULES:
    
    - EXPLICIT: Category directly mentioned in text
    - IMPLICIT: Category reasonably implied by context
    - DERIVATIVE: Category derived from described operations
    
    Examples:
    - "patient records" → Health Data (EXPLICIT)
    - "processing for medical research" → Health Data (IMPLICIT)
    - "DNA analysis" → Genetic Data, Health Data (EXPLICIT + DERIVATIVE)
    - "location tracking for delivery" → Location Data (EXPLICIT)
    - "IP address logging" → Device Data, Location Data (EXPLICIT + IMPLICIT)
    
    CRITICAL REQUIREMENTS:
    - Be COMPREHENSIVE - identify ALL categories mentioned or implied
    - Be PRECISE - use correct category names
    - Be JUSTIFIED - explain why each category was identified
    - Be CONSERVATIVE - don't over-infer categories not supported by text
    - PRIORITIZE explicit mentions over implicit ones
    - NOTE when multiple categories overlap
    
    Provide a complete list of ALL data categories with supporting evidence.
    """


@staticmethod
def odrl_synthesis_prompt(
    guidance_text: str,
    rule_name: str,
    framework_type: str,
    restriction_condition: str,
    initial_analysis: str,
    odrl_extraction: str,
    constraint_analysis: str,
    data_categories: str
) -> str:
    """
    Stage 5: Final synthesis into structured ODRL components.
    Combines synthesis_prompt_template pattern with ODRL specificity.
    """
    return f"""
    Synthesize all previous analyses into comprehensive, structured ODRL components.
    
    RULE CONTEXT:
    - Rule Name: {rule_name}
    - Framework: {framework_type}
    - Type: {restriction_condition}
    
    ORIGINAL GUIDANCE TEXT:
    {guidance_text}
    
    ANALYSIS STAGES COMPLETED:
    
    STAGE 1 - COMPREHENSIVE ANALYSIS:
    {initial_analysis}
    
    STAGE 2 - ODRL COMPONENT EXTRACTION:
    {odrl_extraction}
    
    STAGE 3 - CONSTRAINT ANALYSIS:
    {constraint_analysis}
    
    STAGE 4 - DATA CATEGORY IDENTIFICATION:
    {data_categories}
    
    SYNTHESIS TASK:
    
    Create a COMPLETE, COMPREHENSIVE JSON structure with ALL extracted information:
    
    {{
      "actions": [
        "list ALL actions identified - use ODRL standard actions where possible",
        "include both standard (use, transfer, etc.) and custom actions"
      ],
      
      "permissions": [
        {{
          "action": "specific ODRL action",
          "target": "what the action applies to (asset description)",
          "assigner": "who grants permission (if specified in guidance)",
          "assignee": "who receives permission (if specified in guidance)",
          "constraints": [
            {{
              "leftOperand": "ODRL left operand",
              "operator": "ODRL operator (eq, neq, gt, lt, etc.)",
              "rightOperand": "constraint value",
              "description": "clear explanation in simple English"
            }}
          ],
          "duties": [
            "any duties that must be fulfilled to exercise this permission"
          ],
          "description": "clear description of this permission in simple English"
        }}
      ],
      
      "prohibitions": [
        {{
          "action": "specific ODRL action",
          "target": "what the action applies to (asset description)",
          "assigner": "who sets prohibition (if specified in guidance)",
          "assignee": "who is prohibited (if specified in guidance)",
          "constraints": [
            {{
              "leftOperand": "ODRL left operand",
              "operator": "ODRL operator",
              "rightOperand": "constraint value",
              "description": "clear explanation in simple English"
            }}
          ],
          "description": "clear description of this prohibition in simple English"
        }}
      ],
      
      "constraints": [
        {{
          "leftOperand": "what is being constrained",
          "operator": "eq|neq|gt|lt|gteq|lteq|isPartOf|isA|isAllOf|isAnyOf|isNoneOf",
          "rightOperand": "value or condition (string, number, array, or URI)",
          "description": "what this constraint means in simple English",
          "scope": "permission|prohibition|duty"
        }}
      ],
      
      "data_categories": [
        "complete list of ALL data categories identified",
        "use precise category names",
        "include both explicit and implicit categories"
      ],
      
      "data_subjects": [
        "who the data is about (individuals, customers, employees, patients, etc.)"
      ],
      
      "parties": {{
        "assigners": ["who grants permissions or sets prohibitions"],
        "assignees": ["who receives permissions or is subject to prohibitions"],
        "controllers": ["data controllers if specified"],
        "processors": ["data processors if specified"],
        "third_parties": ["any other relevant parties mentioned"]
      }},
      
      "purpose": "primary purpose of data processing if specified",
      "legal_basis": "legal basis for processing if specified",
      "geographic_scope": [
        "jurisdictions, regions, or countries where this rule applies"
      ],
      
      "evidence_requirements": [
        "what evidence is needed to demonstrate compliance"
      ],
      
      "verification_methods": [
        "how compliance can be verified or audited"
      ],
      
      "confidence_score": 0.0-1.0,
      "extraction_reasoning": "detailed explanation of how you extracted and structured this information, including any assumptions or interpretations made"
    }}
    
    CRITICAL SYNTHESIS REQUIREMENTS:
    
    1. COMPLETENESS:
       - Include EVERY component identified in all analysis stages
       - Do not omit any permissions, prohibitions, constraints, or data categories
       - If information is uncertain, include it with lower confidence score
    
    2. CONSISTENCY:
       - Ensure constraints are properly linked to their permissions/prohibitions
       - Verify parties are consistently identified across components
       - Check that actions use consistent terminology
    
    3. ACCURACY:
       - Base ALL extractions on actual guidance text
       - Use exact ODRL terminology for standard components
       - Provide clear descriptions in simple English for user understanding
    
    4. STRUCTURE:
       - Follow ODRL 2.2 specification precisely
       - Use correct operators with appropriate operands
       - Format rightOperand values correctly (strings, numbers, arrays, URIs)
    
    5. FRAMEWORK-SPECIFIC LOGIC:
       - If {restriction_condition} is "restriction":
         Focus on PROHIBITIONS with clear forbidden actions
         Permissions should be minimal or conditional
       
       - If {restriction_condition} is "condition":
         Focus on PERMISSIONS with constraints
         Include all duties required for permissions
         Prohibitions should be exceptions or edge cases
    
    6. MACHINE-READABILITY:
       - All constraint operators must be valid ODRL operators
       - All values must be properly formatted for automated processing
       - Use URIs where standard ODRL vocabulary applies
    
    7. HUMAN-READABILITY:
       - Every permission/prohibition/constraint must have clear description
       - Use simple, clear English without legal jargon
       - Descriptions should enable non-experts to understand requirements
    
    8. CONFIDENCE SCORING:
       - 0.9-1.0: Information explicitly stated in guidance
       - 0.7-0.9: Information clearly implied by guidance
       - 0.5-0.7: Information reasonably inferred from context
       - Below 0.5: Uncertain or speculative (include with caveat)
    
    9. REASONING:
       - Explain how each major component was derived
       - Note any ambiguities in guidance text
       - Identify gaps where additional clarification would help
       - Document any assumptions made during synthesis
    
    VALIDATION CHECKS BEFORE OUTPUT:
    ✓ All permissions have valid actions and targets
    ✓ All prohibitions have valid actions and targets
    ✓ All constraints have leftOperand, operator, rightOperand
    ✓ Constraint operators match operand types
    ✓ Data categories are comprehensive and accurate
    ✓ Parties are identified where possible
    ✓ Descriptions are clear and in simple English
    ✓ Confidence score reflects extraction certainty
    ✓ Extraction reasoning is detailed and justified
    
    RETURN ONLY VALID JSON - NO OTHER TEXT OR MARKDOWN
    
    The output must be a single, valid, parseable JSON object following
    the structure specified above.
    """