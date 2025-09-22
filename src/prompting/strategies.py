"""
Anti-hallucination prompting strategies focused on dual action inference, whole document analysis, and decision inference.
UPDATED VERSION ensuring no references to guidance documents and logical statements only.
"""


class PromptingStrategies:
    """Anti-hallucination prompting strategies focused on dual action inference, whole document analysis, and decision-making with logical statements only."""

    @staticmethod
    def comprehensive_document_analysis_prompt(legislation_text: str, existing_context: str = "", level: str = "level_1", chunk_info: str = "") -> str:
        """Comprehensive document analysis prompt that ensures the entire document is understood with decision inference."""
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
        - Use simple, clear English - avoid legal jargon
        - Write logical, actionable statements without references to document structure

        3. IDENTIFY ALL CONDITIONS AND TRIGGERS:
        - Find all conditions that trigger obligations throughout the document
        - Note data-related triggers (data types, processing activities, transfers)
        - Extract factual conditions that can be evaluated
        - Identify when conditions in one section affect obligations in another
        - Express conditions as logical tests that can be verified

        4. COMPREHENSIVE DECISION INFERENCE:
        - Identify situations where the legislation permits, prohibits, or conditionally allows actions
        - Look for language indicating YES decisions: "may", "is permitted", "is allowed", "can"
        - Look for language indicating NO decisions: "shall not", "is prohibited", "forbidden", "must not"
        - Look for language indicating MAYBE decisions: "provided that", "if", "subject to", "only if", "unless"
        - Identify what actions or conditions are required for conditional permissions
        - Map decision contexts (data transfer, processing, storage, collection, sharing, deletion)
        - Express requirements as logical conditions without referencing document sources

        5. COMPREHENSIVE DATA REQUIREMENTS:
        - Identify all requirements for data handling mentioned anywhere
        - Note all data categories mentioned throughout the text
        - Extract all data processing operations referenced
        - Map data requirements to specific obligations and decisions
        - State requirements as clear operational conditions

        6. COMPREHENSIVE ROLE AND RESPONSIBILITY MAPPING:
        - Identify every role mentioned in the document
        - Map all responsibilities to each role
        - Note how roles interact with each other
        - Identify role-specific obligations throughout the document
        - Express responsibilities as specific, actionable requirements

        7. COMPREHENSIVE DATA CATEGORY IDENTIFICATION:
        - Find every data category mentioned in the document
        - Note specific data types and classifications
        - Identify sensitive data categories
        - Map data categories to processing requirements and decisions

        8. DECISION-ENABLING ACTION IDENTIFICATION:
        - Identify actions that enable or change decision outcomes
        - Note actions required for conditional permissions (data masking, encryption, consent, etc.)
        - Map actions to their decision impact
        - Express actions as specific, implementable operations

        CRITICAL ANALYSIS CONSTRAINTS:
        - Analyze the ENTIRE document as a whole. Do not focus on individual sections in isolation
        - Extract information present throughout the complete legislation text
        - Do not infer beyond what is directly stated
        - Ensure your analysis reflects understanding of the full document context
        - Pay attention to decision-making scenarios
        - Write all statements as logical, verifiable conditions
        - Do not reference document structure, levels, or sources in extracted content
        - Express all requirements as actionable, testable conditions
        - Use precise language that specifies exactly what must be true or what must be done
        - Avoid ambiguous terms like "appropriate", "adequate", "reasonable" unless defined in the legislation
        """

    @staticmethod
    def focused_analysis_with_decision_inference_prompt(legislation_text: str, existing_context: str = "", level: str = "level_1", chunk_info: str = "") -> str:
        """Focused analysis prompt that minimizes hallucination and includes decision inference with logical statements."""
        context_section = f"\n\nEXISTING RULES CONTEXT:\n{existing_context}\n" if existing_context else ""
        chunk_section = f"\n\nCHUNK INFORMATION:\n{chunk_info}\n" if chunk_info else ""

        return f"""
        Analyze this legislation text with strict adherence to what is stated, focusing on decision-making scenarios.
        {context_section}{chunk_section}

        LEGISLATION TEXT TO ANALYZE:
        {legislation_text}

        ANALYSIS REQUIREMENTS:

        1. IDENTIFY EXPLICIT OBLIGATIONS:
        - Extract only obligations stated in the text
        - Identify who has each obligation (controller, processor, joint_controller, data_subject)
        - Note the exact text that creates each obligation
        - Use simple, clear English - avoid legal jargon
        - Express obligations as specific, verifiable requirements

        2. EXTRACT CONDITIONS AND TRIGGERS:
        - Identify conditions that trigger obligations
        - Note data-related triggers (data types, processing activities, transfers)
        - Extract factual conditions that can be evaluated
        - Express conditions as logical tests with specific criteria

        3. DECISION INFERENCE FROM LEGISLATIVE TEXT:
        - For each obligation or requirement, determine if it represents:
          * YES decision: Action is unconditionally permitted ("may", "can", "is allowed")
          * NO decision: Action is prohibited ("shall not", "forbidden", "prohibited")
          * MAYBE decision: Action is conditionally permitted ("if", "provided that", "subject to", "only if")
        - Identify the specific conditions or actions required for MAYBE decisions
        - Map decisions to contexts (data_transfer, data_processing, data_storage, etc.)
        - Express decision logic as clear if-then statements

        4. DETERMINE DATA-SPECIFIC REQUIREMENTS:
        - Identify requirements for data handling
        - Note data categories mentioned in the text
        - Extract data processing operations referenced
        - Map requirements to decision outcomes
        - State requirements as testable conditions

        5. INFER TRIPLE ACTIONS (BASED ON TEXT):
        - For each obligation, identify what rule actions must be taken (organizational/policy level)
        - For each obligation, identify what user actions can be taken (individual/practical level)
        - For each decision scenario, identify what decision-enabling actions are required
        - Focus on actions involving data processing, storage, transfer, or deletion
        - Base actions on requirements in the legislation
        - Ensure actions are practical and implementable
        - Use simple, clear English - avoid legal jargon
        - Express actions as specific operational steps

        6. DECISION-ACTION MAPPING:
        - Map specific actions to the decisions they enable
        - Identify actions required for conditional approvals (data masking, encryption, consent verification, etc.)
        - Note how completion of actions changes decision outcomes
        - Express relationships as logical cause-effect statements

        CRITICAL OUTPUT CONSTRAINTS:
        - Extract information present in the legislation text only
        - Do not infer beyond what is directly stated
        - Focus particularly on conditional language that indicates decision-making scenarios
        - Write all extracted content as logical, actionable statements
        - Do not reference document structure, guidance levels, or document sources
        - Use precise, measurable criteria for all conditions
        - Express all actions as specific, implementable steps
        - Avoid ambiguous language unless explicitly defined in the legislation
        - State requirements as verifiable conditions with clear pass/fail criteria
        """

    @staticmethod
    def decision_inference_prompt(legislation_text: str, context: str = "") -> str:
        """Specialized prompt for inferring decisions from legislative context with logical statements."""
        return f"""
        Analyze the following legislation text specifically to infer decision-making scenarios.
        
        CONTEXT: {context}
        
        LEGISLATION TEXT:
        {legislation_text}
        
        DECISION INFERENCE REQUIREMENTS:
        
        1. IDENTIFY DECISION SCENARIOS:
        - Look for situations where someone needs to make a yes/no decision about data actions
        - Common scenarios: data transfers, data processing, data sharing, consent requirements
        - Identify the specific question being answered (e.g., "Can personal data be transferred to Country X?")
        - Express scenarios as testable conditions
        
        2. ANALYZE LEGISLATIVE LANGUAGE:
        - YES indicators: "may", "can", "is permitted", "is allowed", "has the right to"
        - NO indicators: "shall not", "must not", "is prohibited", "forbidden", "cannot"
        - MAYBE indicators: "provided that", "if", "subject to", "only if", "unless", "where", "when"
        - Extract exact conditions for each decision type
        
        3. EXTRACT CONDITIONAL REQUIREMENTS:
        - For MAYBE decisions, identify exactly what conditions must be met
        - Look for required actions: "data must be masked", "consent must be obtained", "safeguards must be implemented"
        - Identify required verifications: "adequacy must be verified", "impact assessment must be completed"
        - Express requirements as specific, measurable criteria
        
        4. MAP DECISION CONTEXTS:
        - data_transfer: Moving data between locations/countries/entities
        - data_processing: Processing personal data for specific purposes
        - data_storage: Storing data in specific locations or formats
        - data_collection: Collecting personal data from individuals
        - data_sharing: Sharing data with third parties
        - data_deletion: Deleting or erasing personal data
        - consent_management: Obtaining, verifying, or withdrawing consent
        - rights_exercise: Exercising data subject rights
        
        5. IDENTIFY ENABLING ACTIONS:
        - data_masking: Actions that mask or pseudonymize data
        - data_encryption: Actions that encrypt data
        - consent_obtainment: Actions to obtain valid consent
        - adequacy_verification: Actions to verify adequacy decisions
        - safeguards_implementation: Actions to implement appropriate safeguards
        - documentation_completion: Actions to complete required documentation
        - Express actions as specific operational steps
        
        EXAMPLE ANALYSIS:
        Text: "Personal data may be transferred to third countries only if adequate safeguards are implemented"
        Decision: MAYBE
        Context: data_transfer
        Required Actions: safeguards_implementation
        Reasoning: Transfer is conditionally permitted subject to safeguards
        Logical Condition: IF adequate_safeguards_implemented = true THEN data_transfer_permitted = true
        
        CRITICAL OUTPUT REQUIREMENTS:
        - Return analysis in structured format focusing on practical decision-making scenarios
        - Use simple, clear English and base all decisions on explicit legislative language
        - Express all conditions as logical tests that can be programmatically evaluated
        - State requirements as specific, actionable steps
        - Avoid referencing document structure or sources
        - Use precise criteria for all conditional requirements
        - Express decision logic as clear if-then-else statements
        """

    @staticmethod
    def expert_verification_with_decisions_prompt(legislation_text: str, preliminary_analysis: str, level: str = "level_1") -> str:
        """Expert verification prompt to validate findings against source text, including decision logic with logical statements."""

        return f"""
        Verify the preliminary analysis against the source legislation, with special attention to decision-making logic.

        SOURCE LEGISLATION:
        {legislation_text}

        PRELIMINARY ANALYSIS TO VERIFY:
        {preliminary_analysis}

        VERIFICATION TASKS:

        1. ACCURACY CHECK:
        - Verify each identified obligation exists in the source text
        - Confirm conditions and triggers are accurately extracted
        - Validate data categories and processing operations mentioned
        - Ensure language is simple and clear
        - Verify decision inferences match legislative language
        - Check that all statements are logical and actionable

        2. DECISION LOGIC VERIFICATION:
        - Confirm YES decisions are supported by permissive language in the text
        - Confirm NO decisions are supported by prohibitive language in the text
        - Confirm MAYBE decisions are supported by conditional language in the text
        - Verify that required actions for conditional decisions are explicitly stated
        - Check that decision contexts are accurately identified
        - Ensure decision logic is expressed as testable conditions

        3. COMPLETENESS REVIEW:
        - Identify any explicit obligations that were missed
        - Check for data-specific requirements not captured
        - Verify all relevant roles and responsibilities are identified
        - Ensure all decision scenarios in the text are captured
        - Verify all conditions are expressed as logical tests

        4. TRIPLE ACTION VALIDATION:
        - Confirm each proposed rule action is supported by the legislation text
        - Confirm each proposed user action is practical and based on legislation
        - Confirm each proposed decision-enabling action is required by the text
        - Verify actions are specific to data handling requirements
        - Ensure actions can be performed by appropriate entities
        - Check that language is in simple English
        - Verify actions are expressed as specific operational steps

        5. CONDITIONAL LOGIC VALIDATION:
        - Verify that conditional requirements are accurately extracted
        - Confirm that the relationship between conditions and decisions is correct
        - Check that required actions for MAYBE decisions are properly identified
        - Ensure decision contexts match the legislative scenarios
        - Verify conditions are expressed as testable criteria

        6. LOGICAL STATEMENT VALIDATION:
        - Ensure all extracted content uses logical, actionable language
        - Verify no references to document structure or sources appear in extracted content
        - Check that all conditions can be programmatically evaluated
        - Confirm all requirements are expressed as specific, measurable criteria
        - Verify all actions are stated as implementable operational steps

        7. REMOVE UNSUPPORTED ELEMENTS:
        - Flag any elements not supported by the source text
        - Remove elements that cannot be traced to specific legislative language
        - Flag any decision inferences not supported by the text
        - Remove any ambiguous or untestable statements
        - Eliminate references to document structure or sources in extracted content

        CRITICAL VERIFICATION REQUIREMENTS:
        - Provide corrected analysis that adheres to the source legislation text
        - Use simple, clear English throughout
        - Pay special attention to the accuracy of decision-making logic
        - Ensure all extracted content is logical, actionable, and verifiable
        - Express all conditions as specific tests with clear pass/fail criteria
        - State all actions as precise operational steps
        - Remove any ambiguous language unless explicitly defined in legislation
        - Ensure decision logic follows clear if-then-else patterns
        """

    @staticmethod
    def synthesis_with_decisions_prompt_template(
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
        comprehensive_analysis: str
    ) -> str:
        """Template for synthesis prompt with all analyses including decision-making capabilities and logical statements."""

        chunk_context = f"\nCHUNK REFERENCE: {chunk_reference}\n" if chunk_reference else ""

        return f"""
        Based on the analyses below, create machine-readable rules with MAXIMUM COMPREHENSIVENESS including decision-making capabilities.
        Extract EVERY possible rule, obligation, condition, requirement, and DECISION SCENARIO from the legislation text.
        Create multiple rules if the text covers different aspects or scenarios.

        EXISTING RULES CONTEXT:
        {existing_context}

        METADATA CONTEXT:
        {metadata_context}{chunk_context}

        COMPREHENSIVE DOCUMENT ANALYSIS:
        {comprehensive_analysis}

        SOURCE LEGISLATION:
        Article: {article_reference}
        Source Files: {source_files}
        Text: {legislation_text}

        ANALYSIS RESULTS:

        Focused Analysis:
        {focused_analysis}

        Expert Verification:
        {verified_analysis}

        Agent Triple Action Analysis:
        {agent_analysis}

        COMPREHENSIVE EXTRACTION REQUIREMENTS WITH DECISION INFERENCE:
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
        11. IDENTIFY AND EXTRACT DECISION SCENARIOS from the legislation
        12. CREATE DECISION-ENABLING ACTIONS for conditional permissions
        
        DECISION SYNTHESIS REQUIREMENTS:
        1. For each rule, analyze if it enables decision-making scenarios
        2. Identify questions the rule helps answer (e.g., "Can data be transferred?")
        3. Determine decision outcomes: YES (unconditional), NO (prohibited), MAYBE (conditional)
        4. Extract required actions for MAYBE decisions (data masking, encryption, consent, etc.)
        5. Map decisions to contexts (data_transfer, data_processing, data_storage, etc.)
        6. Create decision rules that can be evaluated programmatically
        
        LOGICAL STATEMENT REQUIREMENTS:
        1. Express all conditions as testable logical statements
        2. State all requirements as specific, measurable criteria
        3. Write all actions as precise operational steps
        4. Use clear if-then-else logic for decision scenarios
        5. Avoid ambiguous language unless explicitly defined in legislation
        6. Do not reference document structure or sources in extracted content
        7. Express all obligations as verifiable requirements
        8. State all decision logic as programmable conditions
        
        SYNTHESIS REQUIREMENTS:
        1. Create rules in json-rules-engine format
        2. MANDATORY: Each rule MUST have primary_impacted_role and data_category fields populated
        3. Conditions must be logical tests that can be programmatically evaluated
        4. Actions must be specific operational steps in simple English
        5. Actions must focus on practical data operations (encryption, masking, access controls, etc.)
        6. User actions must be practical tasks individuals can perform
        7. Decision-enabling actions must be specific to the conditional requirements
        8. Use exact enum values for all structured fields
        9. Timeline is optional - include only if mentioned in legislation
        10. Include detailed reasoning for each rule showing exactly which part of the text supports it
        11. Express all extracted content as logical, actionable statements

        CRITICAL FIELD REQUIREMENTS:
        - primary_impacted_role: MUST be one of: "controller", "processor", "joint_controller", "data_subject"
        - secondary_impacted_role: Optional, same values as above
        - data_category: MUST be array with values like: "personal_data", "sensitive_data", "biometric_data", "health_data", "financial_data", "location_data", "behavioral_data", "identification_data"
        - decision_outcomes: MUST include decisions this rule enables with YES/NO/MAYBE values
        - required_actions: MUST include actions required for conditional decisions

        REASONING REQUIREMENTS:
        Each rule must include in its description or metadata exactly which part of the legislation text it was derived from and why.
        
        COMPREHENSIVE RULE CREATION WITH DECISIONS:
        Create multiple rules rather than trying to combine everything into one rule.
        If the text mentions different obligations for controllers vs processors, create separate rules.
        If the text mentions different requirements for different data types, create separate rules.
        If the text has both immediate and long-term requirements, create separate rules.
        If the text has different decision scenarios, create separate decision-enabling rules.
        
        CRITICAL OUTPUT CONSTRAINTS:
        - Return ONLY a valid JSON array of rules
        - Create as many rules as necessary to comprehensively cover all obligations AND decision scenarios
        - Express all conditions as logical tests (e.g., "data_subject_consent_obtained = true")
        - State all actions as specific operational steps (e.g., "implement AES-256 encryption for data at rest")
        - Write all descriptions using factual, testable language
        - Do not include references to document structure or sources in rule content
        - Use precise criteria for all conditional requirements
        - Express decision logic as clear conditional statements

        EXAMPLE LOGICAL CONDITION STRUCTURE:
        {{
          "fact": "cross_border_data_transfer_requested",
          "operator": "equal",
          "value": true,
          "description": "When cross-border data transfer is requested for personal data",
          "decision_impact": "maybe",
          "conditional_requirement": "adequacy_verification"
        }}

        EXAMPLE LOGICAL ACTION STRUCTURE:
        {{
          "action_type": "data_encryption_implementation", 
          "title": "Implement encryption for data in transit and at rest",
          "description": "Apply AES-256 encryption to all personal data during transmission and storage",
          "data_specific_steps": [
            "Configure TLS 1.3 for data transmission",
            "Implement AES-256 encryption for database storage", 
            "Establish key management protocols"
          ],
          "verification_method": [
            "Conduct encryption compliance audit",
            "Verify encryption certificates are valid"
          ]
        }}

        CRITICAL: Return ONLY the JSON array, no other text or markdown.
        Be comprehensive - it's better to create more specific rules than to miss obligations or decision scenarios.
        Pay special attention to conditional language that creates decision-making opportunities.
        Ensure all extracted content uses logical, testable language without document references.
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
    def decision_context_inference_prompt(legislation_text: str) -> str:
        """Prompt for inferring decision contexts from legislation text."""
        return f"""
        Analyze the following legislation text to identify decision-making contexts:

        Text: {legislation_text}

        Identify which decision contexts apply based on the actions or scenarios described:
        - data_transfer: Moving data between locations, countries, or entities
        - data_processing: Processing personal data for specific purposes  
        - data_storage: Storing data in specific locations or formats
        - data_collection: Collecting personal data from individuals
        - data_sharing: Sharing data with third parties
        - data_deletion: Deleting or erasing personal data
        - consent_management: Obtaining, verifying, or withdrawing consent
        - rights_exercise: Exercising data subject rights
        - compliance_verification: Verifying compliance with requirements

        Return a JSON array with the contexts that apply to this text.
        If multiple contexts apply, include all relevant ones.
        If no specific context can be determined, return ["data_processing"] as default.

        Example response: ["data_transfer", "consent_management"]
        """