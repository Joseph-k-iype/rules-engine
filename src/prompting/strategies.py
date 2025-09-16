"""
Anti-hallucination prompting strategies focused on dual action inference and whole document analysis.
"""


class PromptingStrategies:
    """Anti-hallucination prompting strategies focused on dual action inference and whole document analysis."""

    @staticmethod
    def comprehensive_document_analysis_prompt(legislation_text: str, existing_context: str = "", level: str = "level_1", chunk_info: str = "") -> str:
        """Comprehensive document analysis prompt that ensures the entire document is understood."""
        context_section = f"\n\nEXISTING RULES CONTEXT:\n{existing_context}\n" if existing_context else ""
        chunk_section = f"\n\nCHUNK INFORMATION:\n{chunk_info}\n" if chunk_info else ""

        return f"""
        Perform a comprehensive analysis of this {level} legislation text with strict adherence to what is stated.
        Read and understand the ENTIRE document before extracting any rules or conditions.
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

        CRITICAL: Analyze the ENTIRE document as a whole. Do not focus on individual sections in isolation.
        Extract information present throughout the complete legislation text. Do not infer beyond what is directly stated.
        Ensure your analysis reflects understanding of the full document context.
        """

    @staticmethod
    def focused_analysis_prompt(legislation_text: str, existing_context: str = "", level: str = "level_1", chunk_info: str = "") -> str:
        """Focused analysis prompt that minimizes hallucination."""
        context_section = f"\n\nEXISTING RULES CONTEXT:\n{existing_context}\n" if existing_context else ""
        chunk_section = f"\n\nCHUNK INFORMATION:\n{chunk_info}\n" if chunk_info else ""

        return f"""
        Analyze this {level} legislation text with strict adherence to what is stated.
        {context_section}{chunk_section}

        LEGISLATION TEXT TO ANALYZE:
        {legislation_text}

        ANALYSIS REQUIREMENTS:

        1. IDENTIFY EXPLICIT OBLIGATIONS:
        - Extract only obligations stated in the text
        - Identify who has each obligation (controller, processor, joint_controller, data_subject)
        - Note the exact text that creates each obligation
        - Use simple, clear English - avoid legal jargon

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
        - Use simple, clear English - avoid legal jargon

        Extract information present in the legislation text. Do not infer beyond what is directly stated.
        """

    @staticmethod
    def expert_verification_prompt(legislation_text: str, preliminary_analysis: str, level: str = "level_1") -> str:
        """Expert verification prompt to validate findings against source text."""

        return f"""
        Verify the preliminary analysis against the source legislation.

        SOURCE LEGISLATION ({level}):
        {legislation_text}

        PRELIMINARY ANALYSIS TO VERIFY:
        {preliminary_analysis}

        VERIFICATION TASKS:

        1. ACCURACY CHECK:
        - Verify each identified obligation exists in the source text
        - Confirm conditions and triggers are accurately extracted
        - Validate data categories and processing operations mentioned
        - Ensure language is simple and clear

        2. COMPLETENESS REVIEW:
        - Identify any explicit obligations that were missed
        - Check for data-specific requirements not captured
        - Verify all relevant roles and responsibilities are identified

        3. DUAL ACTION VALIDATION:
        - Confirm each proposed rule action is supported by the legislation text
        - Confirm each proposed user action is practical and based on legislation
        - Verify actions are specific to data handling requirements
        - Ensure actions can be performed by appropriate entities
        - Check that language is in simple English

        4. REMOVE UNSUPPORTED ELEMENTS:
        - Flag any elements not supported by the source text
        - Remove elements that cannot be traced to specific legislative language

        Provide corrected analysis that adheres to the source legislation text.
        Use simple, clear English throughout.
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
        comprehensive_analysis: str
    ) -> str:
        """Template for synthesis prompt with all analyses."""

        chunk_context = f"\nCHUNK REFERENCE: {chunk_reference}\n" if chunk_reference else ""

        return f"""
        Based on the analyses below, create machine-readable rules with MAXIMUM COMPREHENSIVENESS.
        Extract EVERY possible rule, obligation, condition, and requirement from the legislation text.
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
        
        SYNTHESIS REQUIREMENTS:
        1. Create rules in json-rules-engine format
        2. Each condition must reference the document level: "{document_level}"
        3. Each condition must include chunk_reference if applicable: {chunk_reference}
        4. MANDATORY: Each rule MUST have primary_impacted_role and data_category fields populated
        5. Actions must reference specific articles and be in simple English
        6. Actions must focus on practical data operations (encryption, masking, access controls, etc.)
        7. User actions must be practical tasks individuals can perform
        8. Use exact enum values for all structured fields
        9. Timeline is optional - include only if mentioned in legislation
        10. Include detailed reasoning for each rule showing exactly which part of the text supports it

        CRITICAL FIELD REQUIREMENTS:
        - primary_impacted_role: MUST be one of: "controller", "processor", "joint_controller", "data_subject"
        - secondary_impacted_role: Optional, same values as above
        - data_category: MUST be array with values like: "personal_data", "sensitive_data", "biometric_data", "health_data", "financial_data", "location_data", "behavioral_data", "identification_data"

        REASONING REQUIREMENTS:
        Each rule must include in its description or metadata exactly which part of the legislation text it was derived from and why.
        
        COMPREHENSIVE RULE CREATION:
        Create multiple rules rather than trying to combine everything into one rule.
        If the text mentions different obligations for controllers vs processors, create separate rules.
        If the text mentions different requirements for different data types, create separate rules.
        If the text has both immediate and long-term requirements, create separate rules.
        
        CRITICAL: Return ONLY a valid JSON array of rules. Create as many rules as necessary to comprehensively cover all obligations in the text.

        [
          {{
            "id": "unique_rule_id_1",
            "name": "Rule Name for Specific Obligation",
            "description": "Specific rule description derived from [exact text reference]",
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
            "rule_derivation_reasoning": "This rule was derived from the text that states '[exact quote]' which creates an obligation for [role] to [action]",
            "conditions": {{
              "all": [
                {{
                  "fact": "specific_condition_fact",
                  "operator": "equal",
                  "value": "condition_value",
                  "description": "Condition based on specific legislative requirement",
                  "data_domain": ["data_usage"],
                  "role": "controller",
                  "reasoning": "This condition derived from article text: '[specific text]' which establishes requirement for [specific scenario]",
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
                "description": "Implement specific data protection measure as required by {article_reference}: [specific requirement]",
                "priority": "medium",
                "data_specific_steps": ["Specific step 1", "Specific step 2", "Specific step 3"],
                "responsible_role": "controller",
                "legislative_requirement": "Exact requirement from {article_reference}: '[quoted text]'",
                "data_impact": "Specific impact on data processing",
                "verification_method": ["Method 1", "Method 2"],
                "timeline": "optional timeline if specified",
                "derived_from_text": "Exact text from {article_reference} that requires this action",
                "applicable_countries": {applicable_countries},
                "confidence_score": 0.8
              }}
            ],
            "user_actions": [
              {{
                "id": "user_action_id_1",
                "action_type": "user_specific_data_operation",
                "title": "User Data Protection Task",
                "description": "Specific task users must perform based on {article_reference}: [specific requirement]",
                "priority": "medium",
                "user_data_steps": ["User step 1", "User step 2", "User step 3"],
                "affected_data_categories": ["personal_data", "sensitive_data"],
                "user_role_context": "data_subject",
                "legislative_requirement": "Exact requirement from {article_reference}: '[quoted text]'",
                "compliance_outcome": "Specific compliance outcome achieved",
                "user_verification_steps": ["Verification 1", "Verification 2"],
                "timeline": "optional timeline if specified",
                "derived_from_text": "Exact text from {article_reference} that requires this user action",
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
        - Create MULTIPLE rules to comprehensively cover all obligations
        - Each rule should focus on a specific obligation or requirement
        - Include detailed reasoning and text references for each rule
        - primary_impacted_role and data_category fields are MANDATORY
        - ALL list fields MUST be arrays, never strings
        - Actions must reference the specific article: {article_reference}
        - Actions must be in simple English, no legal jargon
        - Focus on practical data operations
        - Return ONLY the JSON array, no other text or markdown

        Be comprehensive - it's better to create more specific rules than to miss obligations.
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