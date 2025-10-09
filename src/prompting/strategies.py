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

        2. ANALYZE DECISION CONDITIONS:
        - What conditions lead to "YES" (permission granted)?
        - What conditions lead to "NO" (permission denied)?
        - What conditions lead to "MAYBE" (additional review needed)?
        - What are the transition conditions from "MAYBE" to "YES"?
        - What actions are required for each outcome?

        3. EXTRACT DECISION CONTEXT:
        - Identify the type of decision (data_transfer, data_processing, consent, access, etc.)
        - Determine the context (cross_border_transfer, internal_processing, etc.)
        - Note applicable data categories
        - Identify affected roles
        - Determine if cross-border operations are involved

        OUTPUT FORMAT:
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
        10. Create rich, detailed conditions that can be programmatically evaluated
        11. Decisions must have clear outcomes and action mappings
        12. Cross-reference between rules, actions, and decisions

        OUTPUT FORMAT:
        Return a JSON array of rule objects. Each rule must have:
        - id: Unique identifier
        - name: Clear, descriptive name in simple English
        - description: Full description without document references
        - source_article: Article reference
        - source_file: Source file path
        - conditions: Comprehensive json-rules-engine conditions
        - event: Event triggered when conditions met
        - actions: Array of rule actions (organizational level)
        - user_actions: Array of user actions (individual level)
        - decisions: Array of decision objects (if applicable)
        - priority: Priority level
        - primary_impacted_role: Primary role affected
        - secondary_impacted_role: Secondary role (if applicable)
        - data_category: Array of applicable data categories
        - applicable_countries: {applicable_countries}
        - adequacy_countries: {adequacy_countries}

        CRITICAL: Return ONLY valid JSON. No additional text or explanations outside the JSON structure.
        """

    @staticmethod
    def data_role_inference_prompt(legislation_text: str) -> str:
        """Prompt for inferring primary data role from legislation text."""
        return f"""
        Based on the following legislation text, identify the primary impacted data role:

        Text: {legislation_text}

        Identify which role is primarily addressed or impacted in this text:
        - controller: Determines purposes and means of processing
        - processor: Processes data on behalf of controller
        - joint_controller: Jointly determines purposes and means with others
        - data_subject: Individual whose personal data is processed

        Return only the role name that best fits.
        If the text mentions multiple roles, identify which one has the PRIMARY obligations or is MOST impacted.
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
        
        4. DUTIES (what MUST be done):
           - What obligations must be fulfilled?
           - Are duties independent or linked to permissions?
           - Who is responsible for the duty (assignee)?
           - What is the consequence of not fulfilling the duty?
           
           Structure each duty with:
           - Action(s) required
           - Target (what the action applies to)
           - Constraints (conditions and timing)
           - Parties (assigner, assignee)
        
        5. CONSTRAINTS (conditions and limitations):
           - Temporal: time-based restrictions
           - Spatial: location/jurisdiction restrictions
           - Purpose: purpose-based restrictions
           - Party: recipient-based restrictions
           - Quantitative: count/amount restrictions
           - Qualitative: quality/type restrictions
           
           For each constraint, identify:
           - leftOperand (what is being constrained)
           - operator (comparison operator)
           - rightOperand (constraint value)
           - description (plain English explanation)
        
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
        
        1. CONSTRAINT IDENTIFICATION:
           - What is being constrained? (leftOperand)
           - What is the comparison/test? (operator)
           - What is the constraint value? (rightOperand)
           - How does this constraint limit or enable actions?
        
        2. ODRL LEFT OPERANDS (standardized):
           Common leftOperands:
           - dateTime: specific date/time
           - delayPeriod: delay before action
           - elapsedTime: time since event
           - event: triggering event
           - count: number of times
           - purpose: processing purpose
           - recipient: who receives data
           - spatial: geographic location
           - industry: industry sector
           - language: language requirement
           - version: version requirement
           - virtualLocation: online location
           
           Custom leftOperands when needed:
           - dataCategory: type of data
           - processingContext: context of processing
           - consentStatus: consent state
           - etc.
        
        3. ODRL OPERATORS:
           - eq: equal to
           - neq: not equal to
           - gt: greater than
           - lt: less than
           - gteq: greater than or equal
           - lteq: less than or equal
           - isA: is instance of type
           - isPartOf: is part of collection
           - isAllOf: matches all of set
           - isAnyOf: matches any of set
           - isNoneOf: matches none of set
        
        4. RIGHT OPERAND FORMAT:
           - String: "value"
           - Number: 123
           - Date/Time: ISO 8601 format
           - Duration: ISO 8601 duration (P30D, PT2H)
           - Array: ["value1", "value2"]
           - URI: reference to external resource
        
        5. CONSTRAINT SCOPE AND APPLICATION:
           - Does this constraint apply to a permission, prohibition, or duty?
           - Is the constraint mandatory (MUST) or optional (SHOULD)?
           - What happens if the constraint is violated?
           - Are there any exceptions to the constraint?
        
        6. CONSTRAINT RELATIONSHIPS:
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
        
        1. STANDARD DATA CATEGORIES:
           - Personal Data: any information relating to identified/identifiable person
           - Sensitive Data: special categories (racial origin, political opinions, etc.)
           - Biometric Data: unique biological characteristics
           - Genetic Data: inherited or acquired genetic characteristics
           - Health Data: physical or mental health information
           - Financial Data: payment, banking, financial information
           - Location Data: geographic position data
           - Behavioral Data: behavioral patterns, profiling data
           - Identification Data: identity documents, credentials
           - Contact Data: email, phone, address
           - Demographic Data: age, gender, nationality
           - Professional Data: employment, education, qualifications
           - Transactional Data: purchase history, service usage
           - Communication Data: emails, messages, call logs
           - Device Data: IP address, device ID, cookies
           - Biographic Data: life events, relationships
        
        2. DOMAIN-SPECIFIC DATA:
           - Medical Records (health domain)
           - Patient Data (health domain)
           - Student Records (education domain)
           - Employee Data (employment domain)
           - Customer Data (commercial domain)
           - Research Data (research domain)
        
        3. DATA CATEGORIZED BY SENSITIVITY:
           - Public Data (publicly available)
           - Internal Data (organizational use)
           - Confidential Data (restricted access)
           - Restricted Data (highly sensitive)
        
        4. DATA CATEGORIZED BY PURPOSE/USE:
           - Marketing Data (data used for marketing/advertising)
           - Research Data (data used for research purposes)
           - Statistical Data (data used for statistics)
           - Operational Data (data for service operation)
           - Archival Data (historical/archived data)
           - Training Data (data for ML/AI training)
        
        5. DATA CATEGORIZED BY STATE:
           - Active Data (currently in use)
           - Archived Data (stored for retention)
           - Backup Data (copies for recovery)
           - Temporary Data (session/cache data)
        
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

# Add this new method to PromptingStrategies class in strategies.py

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
    Stage 5: Final synthesis into structured ODRL components with logical consistency checking.
    
    This prompt instructs the LLM to:
    1. Avoid creating duplicate constraints in permissions and prohibitions
    2. Use logical reasoning to determine correct constraint placement
    3. Prefer positive framing (permissions) over negative framing
    4. Ensure each constraint appears only once
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
    
    ═══════════════════════════════════════════════════════════════════════════════
    CRITICAL LOGICAL CONSISTENCY REQUIREMENTS
    ═══════════════════════════════════════════════════════════════════════════════
    
    1. AVOID DUPLICATION: A constraint should appear in EITHER permissions OR prohibitions, NOT both.
       
       ❌ WRONG:
       Permission:   requestor eq "UK NCA"     (allowed if UK NCA)
       Prohibition:  requestor neq "UK NCA"    (forbidden if not UK NCA)
       → These are logically the SAME rule expressed differently!
       
       ✅ CORRECT:
       Permission:   requestor eq "UK NCA"     (allowed if UK NCA)
       Prohibition:  [empty]
       → Single, clear rule
    
    2. LOGICAL REASONING FRAMEWORK:
       
       When you see: "Data sharing IS PERMITTED if requestor is X"
       → Create: PERMISSION with constraint (leftOperand eq X)
       → Do NOT create: PROHIBITION with constraint (leftOperand neq X)
       
       When you see: "Data sharing IS PROHIBITED if requestor is NOT X"
       → Reframe as: PERMISSION with constraint (leftOperand eq X)
       → This is clearer for enforcement systems
       
       When you see: "Action Y is absolutely PROHIBITED for all cases"
       → Create: PROHIBITION without inverse permission
       → Example: "Data selling is prohibited" → Prohibition only
    
    3. OPERATOR CORRECTNESS:
       
       PERMISSION with "eq" operator means: "allowed IF condition matches"
       PROHIBITION with "neq" operator means: "forbidden IF condition does NOT match"
       → These express the SAME rule differently - choose ONE
       
       PERMISSION with "isAnyOf" means: "allowed IF entity is in list"
       PROHIBITION with "isNoneOf" means: "forbidden IF entity is NOT in list"
       → These also express the SAME rule - choose ONE
       
       Prefer: PERMISSION with positive operators (eq, isAnyOf, isPartOf)
       Avoid: Creating both permission and its logical inverse as prohibition
    
    4. DECISION TREE FOR AVOIDING DUPLICATION:
       
       For each constraint you identify, ask:
       
       Q1: Does this constraint already exist in permissions?
       → If YES: DON'T add to prohibitions
       
       Q2: Does the inverse/complement of this constraint exist in prohibitions?
       → If YES: DON'T add to permissions
       
       Q3: Is this constraint about WHO can do something?
       → Prefer: PERMISSION with positive constraint (eq, isAnyOf)
       → Avoid: PROHIBITION with negative constraint (neq, isNoneOf)
       
       Q4: Is this constraint about WHO cannot do something?
       → Convert to: PERMISSION with positive constraint for allowed entities
       
       Q5: Is this constraint about WHAT is absolutely forbidden?
       → Use: PROHIBITION (e.g., "selling data is prohibited")
       → Don't create inverse permission
    
    5. REASONING PROCESS (must follow):
       
       Step 1: Extract all constraints from guidance
       
       Step 2: Group constraints by what they control:
               - requestor/recipient constraints
               - purpose constraints
               - temporal constraints
               - action constraints
       
       Step 3: For each group, determine if naturally a permission or prohibition:
               • "Data CAN be shared with X" → PERMISSION
               • "Data CANNOT be shared except with X" → PERMISSION (reframe positively)
               • "Action Y is PROHIBITED" → PROHIBITION (absolute prohibition)
               • "Data MUST be used for purpose Z" → PERMISSION with purpose constraint
       
       Step 4: Verify no logical contradictions exist
       
       Step 5: Ensure each constraint appears only once across all rules
    
    ═══════════════════════════════════════════════════════════════════════════════
    EXAMPLES OF CORRECT HANDLING
    ═══════════════════════════════════════════════════════════════════════════════
    
    Example 1 - Simple Requestor Constraint
    ────────────────────────────────────────
    Guidance: "Data sharing is permitted if the disclosure request originates from 
               either the UK's National Crime Agency or a credit/financial institution."
    
    ❌ WRONG (duplication):
    {{
      "permissions": [{{
        "constraint": [{{
          "leftOperand": "requestor",
          "operator": "isAnyOf",
          "rightOperand": ["UK National Crime Agency", "credit/financial institution"]
        }}]
      }}],
      "prohibitions": [{{
        "constraint": [{{
          "leftOperand": "requestor",
          "operator": "isNoneOf",
          "rightOperand": ["UK National Crime Agency", "credit/financial institution"]
        }}]
      }}]
    }}
    → Problem: Same constraint with inverse operators!
    
    ✅ CORRECT:
    {{
      "permissions": [{{
        "action": "distribute",
        "constraint": [{{
          "leftOperand": "requestor",
          "operator": "isAnyOf",
          "rightOperand": ["UK National Crime Agency", "credit/financial institution"],
          "description": "Requestor must be from approved list"
        }}],
        "description": "Data sharing permitted only if disclosure request originates from UK National Crime Agency or credit/financial institution"
      }}],
      "prohibitions": []
    }}
    → Clear: Single permission defines who can access
    
    Example 2 - Purpose Constraint
    ────────────────────────────────
    Guidance: "Personal data can only be processed for fraud prevention purposes."
    
    ❌ WRONG:
    {{
      "permissions": [{{
        "constraint": [{{"leftOperand": "purpose", "operator": "eq", "rightOperand": "fraud_prevention"}}]
      }}],
      "prohibitions": [{{
        "constraint": [{{"leftOperand": "purpose", "operator": "neq", "rightOperand": "fraud_prevention"}}]
      }}]
    }}
    
    ✅ CORRECT:
    {{
      "permissions": [{{
        "action": "use",
        "constraint": [{{
          "leftOperand": "purpose",
          "operator": "eq",
          "rightOperand": "fraud_prevention",
          "description": "Processing limited to fraud prevention"
        }}],
        "description": "Data processing permitted exclusively for fraud prevention purposes"
      }}],
      "prohibitions": []
    }}
    
    Example 3 - Absolute Prohibition (Correct Usage)
    ─────────────────────────────────────────────────
    Guidance: "The sale of personal data is strictly prohibited under all circumstances."
    
    ✅ CORRECT:
    {{
      "permissions": [],
      "prohibitions": [{{
        "action": "sell",
        "constraint": [],
        "description": "Sale of personal data is absolutely prohibited"
      }}]
    }}
    → This is an absolute prohibition, no permission equivalent exists
    
    Example 4 - Mixed Rules (Both Valid)
    ────────────────────────────────────
    Guidance: "Data may be shared with partner organizations for research purposes,
               but selling data is prohibited."
    
    ✅ CORRECT:
    {{
      "permissions": [{{
        "action": "distribute",
        "constraint": [
          {{"leftOperand": "recipient", "operator": "eq", "rightOperand": "partner_organization"}},
          {{"leftOperand": "purpose", "operator": "eq", "rightOperand": "research"}}
        ],
        "description": "Sharing permitted with partners for research"
      }}],
      "prohibitions": [{{
        "action": "sell",
        "constraint": [],
        "description": "Selling data is absolutely prohibited"
      }}]
    }}
    → Different constraints controlling different things - both needed
    
    ═══════════════════════════════════════════════════════════════════════════════
    SYNTHESIS TASK
    ═══════════════════════════════════════════════════════════════════════════════
    
    First, provide your reasoning about permissions vs prohibitions:
    - List all constraints you identified from the guidance
    - For EACH constraint, explain whether it should be in permission or prohibition
    - Explain why no duplications exist in your output
    - Verify operators are correct for the rule type
    
    Then create the complete JSON structure following this format:
    
    {{
      "reasoning": "
        Constraint Analysis:
        1. [Constraint description] → Classified as PERMISSION because [reason]
        2. [Constraint description] → Classified as PROHIBITION because [reason]
        
        Verification:
        - No duplicate constraints exist ✓
        - No inverse operator pairs exist ✓
        - Each constraint appears exactly once ✓
        - Operators are semantically correct ✓
      ",
      
      "actions": [
        "List ALL actions identified - use ODRL standard actions where possible",
        "Examples: use, transfer, distribute, read, modify, delete, sell"
      ],
      
      "permissions": [
        {{
          "action": "specific ODRL action (e.g., 'distribute', 'use', 'transfer')",
          "target": "what the action applies to (asset description)",
          "assigner": "who grants permission (if specified in guidance)",
          "assignee": "who receives permission (if specified in guidance)",
          "constraints": [
            {{
              "leftOperand": "ODRL left operand (e.g., 'requestor', 'purpose', 'recipient', 'spatial')",
              "operator": "eq|isAnyOf|isPartOf|gt|lt|etc (choose appropriate POSITIVE operator)",
              "rightOperand": "value or list of allowed values",
              "description": "Clear explanation - use phrases like 'permitted if', 'allowed when', 'authorized for'"
            }}
          ],
          "duties": [
            "any obligations that must be fulfilled to exercise this permission"
          ],
          "description": "Clear description of this permission in simple English using permissive language"
        }}
      ],
      
      "prohibitions": [
        {{
          "action": "specific ODRL action",
          "target": "what the action applies to",
          "assigner": "who sets prohibition (if specified)",
          "assignee": "who is prohibited (if specified)",
          "constraints": [
            {{
              "leftOperand": "ODRL left operand",
              "operator": "eq|isAnyOf|etc (for absolute prohibitions, NOT inverses of permissions)",
              "rightOperand": "prohibited value",
              "description": "Clear explanation - use phrases like 'prohibited when', 'forbidden if', 'not allowed for'"
            }}
          ],
          "description": "Clear description using prohibitive language - ONLY for constraints NOT already in permissions"
        }}
      ],
      
      "constraints": [
        {{
          "leftOperand": "what is being constrained",
          "operator": "appropriate ODRL operator",
          "rightOperand": "value or condition",
          "description": "clear explanation in simple English",
          "scope": "permission|prohibition|duty"
        }}
      ],
      
      "data_categories": [
        "complete list of ALL data categories identified in guidance",
        "use precise category names from guidance text"
      ],
      
      "data_subjects": [
        "who the data is about (individuals, customers, employees, patients, etc.)"
      ],
      
      "parties": {{
        "controllers": ["data controllers identified"],
        "processors": ["data processors identified"],
        "assigners": ["entities granting permissions"],
        "assignees": ["entities receiving permissions"],
        "third_parties": ["other relevant parties"]
      }},
      
      "extraction_reasoning": "Brief summary of extraction approach and key decisions made to avoid duplication"
    }}
    
    ═══════════════════════════════════════════════════════════════════════════════
    FINAL VERIFICATION CHECKLIST
    ═══════════════════════════════════════════════════════════════════════════════
    
    Before submitting your response, verify:
    
    [ ] Each constraint appears in only ONE place (permissions OR prohibitions)
    [ ] No inverse/complement constraints exist across permissions and prohibitions
    [ ] Operators are semantically correct for the rule type
    [ ] Comments clearly indicate the rule's intent without contradiction
    [ ] Downstream systems can unambiguously enforce the policy
    [ ] All constraints from guidance have been extracted
    [ ] Reasoning section explains classification decisions
    [ ] No logical contradictions within same rule
    
    ═══════════════════════════════════════════════════════════════════════════════
    
    Return ONLY the JSON structure with actual extracted data from the guidance.
    Do NOT include template instructions or placeholder text in the JSON.
    Ensure all fields contain real, extracted information.
    """