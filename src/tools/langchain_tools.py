"""
LangChain tools for rule extraction, action inference, and decision-making capabilities.
"""
from openai import OpenAI
from langchain_core.tools import tool

from ..config import Config


@tool
def extract_rule_conditions_with_decisions(legislation_text: str, focus_area: str) -> str:
    """Extract specific rule conditions from legislation text with decision impact analysis."""

    prompt = f"""
    Extract rule conditions from the following legislation text, focusing on {focus_area}, including decision-making implications.

    Return conditions in json-rules-engine format based on explicit requirements in the text.

    Text: {legislation_text}

    Focus on identifying:
    - Specific facts that can be evaluated from the legislation
    - Comparison operators based on legal language
    - Values to compare against as stated in the text
    - Data domains and roles mentioned
    - Decision impact of each condition (does it enable yes/no/maybe decisions?)
    - Actions required when conditions are met or not met

    For each condition, also determine:
    - decision_impact: "yes", "no", "maybe", or "unknown" based on legislative language
    - conditional_requirement: specific action required if condition triggers a "maybe" decision
    - Examples:
      * "if data is masked" -> decision_impact: "maybe", conditional_requirement: "data_masking"  
      * "consent must be obtained" -> decision_impact: "maybe", conditional_requirement: "consent_obtainment"
      * "is prohibited" -> decision_impact: "no", conditional_requirement: null

    Return valid JSON only. Base conditions on explicit legislative language and their decision implications.
    """

    try:
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )

        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error extracting conditions: {str(e)}"


@tool
def analyze_data_domains_with_decision_context(legislation_text: str) -> str:
    """Analyze and identify relevant data domains in legislation with decision contexts."""

    prompt = f"""
    Analyze the following legislation text and identify which data domains are mentioned along with their decision contexts:
    - data_transfer: Moving data between locations/entities
    - data_usage: Using data for specific purposes
    - data_storage: Storing data in specific ways/locations
    - data_collection: Collecting data from individuals
    - data_deletion: Deleting or erasing data

    Text: {legislation_text}

    For each identified domain, also determine:
    - Decision scenarios it relates to (e.g., "Can data be transferred?", "Is processing allowed?")
    - Permission level: "permitted", "prohibited", "conditional" based on legislative language
    - Required actions for conditional scenarios (data masking, consent, etc.)

    Return a JSON object mapping each identified domain to:
    - relevance: how relevant it is to the text
    - decision_context: what decisions it relates to
    - permission_level: permitted/prohibited/conditional
    - required_actions: actions needed for conditional permissions
    - supporting_text: specific text that indicates the domain

    Include only domains that are mentioned in the legislation text.
    """

    try:
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )

        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing domains: {str(e)}"


@tool
def identify_roles_responsibilities_with_decision_authority(legislation_text: str) -> str:
    """Identify roles and responsibilities in legislation with decision-making authority."""

    prompt = f"""
    Identify the roles and responsibilities mentioned in this legislation, including their decision-making authority:
    - controller: Data controller with decision authority
    - processor: Data processor with limited decision authority  
    - joint_controller: Joint controllers with shared decision authority
    - data_subject: Data subjects with rights-based decision authority

    Text: {legislation_text}

    For each role mentioned, identify:
    - Specific obligations and responsibilities as stated in the text
    - Decision-making authority (what decisions can they make?)
    - Conditions under which they can make decisions
    - Actions they must take for compliance
    - Actions they can require from others

    Return a JSON object with role mappings that includes:
    - obligations: list of specific obligations
    - decision_authority: what decisions they can make
    - required_actions: actions they must perform
    - conditional_permissions: actions they can do under certain conditions
    - prohibited_actions: actions they cannot do

    Base analysis only on what is explicitly stated in the legislation.
    """

    try:
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )

        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error identifying roles: {str(e)}"


@tool
def infer_decision_enabling_actions(legislation_text: str, decision_context: str, conditional_scenarios: str) -> str:
    """Infer actions that enable or change decision outcomes in legislation."""

    prompt = f"""
    Based on the legislation text and decision context, identify specific actions that enable decision outcomes.

    Legislation Text: {legislation_text}
    Decision Context: {decision_context}
    Conditional Scenarios: {conditional_scenarios}

    Focus on actions that:
    1. Change a "no" decision to "yes" (enabling actions)
    2. Change a "maybe" decision to "yes" (fulfilling conditions)
    3. Are required for conditional permissions
    4. Enable compliance with legislative requirements

    Look for decision-enabling actions like:
    - data_masking: Actions that mask, pseudonymize, or anonymize data
    - data_encryption: Actions that encrypt data in transit or at rest  
    - consent_obtainment: Actions to obtain valid, informed consent
    - consent_verification: Actions to verify existing consent
    - adequacy_verification: Actions to verify adequacy decisions
    - safeguards_implementation: Actions to implement appropriate safeguards
    - documentation_completion: Actions to complete required documentation
    - impact_assessment: Actions to conduct privacy/data protection impact assessments
    - approval_obtainment: Actions to obtain regulatory or supervisory approvals
    - notification_completion: Actions to complete required notifications

    For each decision-enabling action, provide:
    - action_type: Type of enabling action from the list above
    - title: Clear action title in simple English
    - description: What must be done to enable the decision
    - decision_impact: How this action changes the decision (no->yes, maybe->yes, etc.)
    - required_for_context: Which decision context requires this action
    - legislative_requirement: Exact text requiring this action
    - verification_method: How to confirm the action was completed
    - derived_from_text: Exact legislative text requiring this enabling action

    Return valid JSON array. Only include actions explicitly required by the legislation.
    If no decision-enabling actions can be inferred, return empty array.
    """

    try:
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )

        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error inferring decision-enabling actions: {str(e)}"


@tool
def infer_data_processing_actions_with_decisions(legislation_text: str, data_categories: str, processing_context: str) -> str:
    """Infer specific data processing actions from legislation text with decision implications."""

    prompt = f"""
    Based on the following legislation text, identify specific organizational actions that must be taken regarding data processing, including their decision implications.

    Legislation Text: {legislation_text}
    Data Categories Mentioned: {data_categories}
    Processing Context: {processing_context}

    Extract only actions that are:
    1. Explicitly required by the legislation text
    2. Related to data handling, processing, storage, transfer, or deletion
    3. Actionable by data controllers or processors at organizational level
    4. Have clear data-specific outcomes
    5. Impact decision-making scenarios (enable, restrict, or condition decisions)
    6. Focus on practical data operations like:
       - Data encryption and security measures
       - Data masking and anonymization
       - Access controls and authentication
       - Data retention and deletion procedures
       - Consent management systems
       - Data transfer protocols
       - Audit logging and monitoring
       - Backup and recovery procedures
    7. Described in simple, clear English - avoid legal jargon

    For each action, provide:
    - action_type: Brief descriptive name focused on data operations
    - title: Clear action title in simple English
    - description: What must be done with data in simple English
    - priority: Extract from legislative language (urgent/immediate/high/medium/low)
    - data_specific_steps: Concrete steps related to data handling
    - responsible_role: Who is responsible for this action
    - legislative_requirement: Exact requirement from legislation
    - data_impact: How this affects data processing
    - verification_method: How to confirm compliance
    - timeline: Timeline if specified in legislation
    - derived_from_text: Exact legislative text that requires this action
    - enables_decision: What decision outcome this action enables (yes/no/maybe)
    - decision_context: What decision scenario this action affects
    - required_for_decision: What decision type requires this action (for conditional scenarios)

    Return valid JSON array. Only include actions explicitly stated or clearly implied by the legislation.
    If no actions can be inferred, return empty array.
    """

    try:
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )

        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error inferring data processing actions: {str(e)}"


@tool
def infer_compliance_verification_actions_with_decisions(legislation_text: str, obligations: str, roles: str) -> str:
    """Infer compliance verification actions from legislation with decision-making implications."""

    prompt = f"""
    Based on the legislation text and identified obligations, extract verification and compliance actions with decision implications.

    Legislation Text: {legislation_text}
    Identified Obligations: {obligations}
    Affected Roles: {roles}

    Focus only on actions that:
    1. Are explicitly required for compliance verification
    2. Involve documentation, reporting, or demonstration of data handling
    3. Are mentioned in the legislation text
    4. Can be performed by the specified roles
    5. Impact decision outcomes (enable decisions or verify conditions are met)
    6. Focus on practical data verification like:
       - Data audit procedures
       - Compliance monitoring systems
       - Data processing records
       - Privacy impact assessments
       - Data breach notification procedures
       - Regular security reviews
       - Third-party data processor audits
    7. Described in simple, clear English - avoid legal jargon

    For each verification action:
    - action_type: Type of verification required (focused on data aspects)
    - title: What needs to be verified in simple English
    - description: How to demonstrate compliance in simple English
    - data_specific_steps: Steps involving data or data processes
    - legislative_requirement: Specific legal requirement
    - verification_method: How compliance is verified
    - derived_from_text: Exact text requiring this verification
    - enables_decision: What decision this verification enables
    - decision_context: What decision scenario this affects
    - verification_confirms: What condition or requirement this verifies

    Return valid JSON array. Base all actions on explicit legislative requirements only.
    If no actions can be inferred, return empty array.
    """

    try:
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )

        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error inferring compliance verification actions: {str(e)}"


@tool
def infer_data_subject_rights_actions_with_decisions(legislation_text: str, rights_mentioned: str, data_domains: str) -> str:
    """Infer actions required to handle data subject rights with decision-making context."""

    prompt = f"""
    Analyze the legislation for requirements related to data subject rights and extract required actions with decision implications.

    Legislation Text: {legislation_text}
    Rights Mentioned: {rights_mentioned}
    Data Domains: {data_domains}

    Extract actions that:
    1. Are required to facilitate data subject rights
    2. Involve handling, processing, or responding to data subject requests
    3. Are explicitly mentioned in the legislation
    4. Have clear data-handling implications
    5. Enable or affect decision-making about rights exercise
    6. Focus on practical data rights implementation like:
       - Data access systems and procedures
       - Data rectification workflows
       - Data erasure and deletion procedures
       - Data portability tools and formats
       - Consent withdrawal mechanisms
       - Objection handling processes
       - Automated decision-making controls
    7. Described in simple, clear English - avoid legal jargon

    For each rights-related action:
    - action_type: Type of rights handling required (focused on data operations)
    - title: Rights-related obligation in simple English
    - description: What must be done to support data subject rights in simple English
    - data_specific_steps: Specific data handling steps
    - legislative_requirement: Legal basis for the action
    - data_impact: How this affects data and data processing
    - verification_method: How to confirm rights are being respected
    - derived_from_text: Legislative text requiring this action
    - enables_decision: What rights-related decision this action enables
    - decision_context: What rights scenario this action addresses
    - rights_impact: How this action affects the exercise of data subject rights

    Return valid JSON array. Only include actions with clear legislative basis.
    If no actions can be inferred, return empty array.
    """

    try:
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )

        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error inferring data subject rights actions: {str(e)}"


@tool
def infer_user_actionable_tasks_with_decisions(legislation_text: str, data_context: str, user_roles: str) -> str:
    """Infer practical tasks that users can perform based on legislation with decision-making capabilities."""

    prompt = f"""
    Analyze the following legislation text to identify specific tasks that individual users can perform, including decision-making capabilities.

    Legislation Text: {legislation_text}
    Data Context: {data_context}
    User Roles: {user_roles}

    Extract ONLY tasks that are:
    1. Explicitly required by the legislation text
    2. Actionable by individual users with commonly available tools/systems
    3. Related to data operations users can control
    4. Have clear compliance outcomes
    5. Can be practically implemented by users
    6. Enable or affect decision-making about their data
    7. Focus on individual data actions like:
       - Encrypting personal files and communications
       - Using privacy settings on platforms
       - Managing consent preferences
       - Securing personal data with passwords
       - Backing up important data securely
       - Deleting unnecessary personal data
       - Reviewing data sharing permissions
       - Using secure communication tools
    8. Described in simple, clear English - avoid legal jargon

    For each user task, provide:
    - action_type: Specific data operation
    - title: Clear task title for users in simple English
    - description: What users must do in simple English
    - priority: Based on legislative urgency
    - user_data_steps: Concrete steps for user data handling
    - affected_data_categories: Types of data involved
    - legislative_requirement: Exact requirement from legislation
    - compliance_outcome: What compliance goal this achieves
    - user_verification_steps: How users can verify completion
    - derived_from_text: Exact text requiring this task
    - enables_decision: What decision this user action enables about their data
    - decision_context: What decision scenario this affects
    - decision_impact: How this action affects decision outcomes for the user

    Focus on practical, implementable data tasks. Avoid abstract concepts.
    Return valid JSON array based ONLY on explicit legislative requirements.
    If no user actions can be inferred, return empty array.
    """

    try:
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )

        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error inferring user actionable tasks: {str(e)}"


@tool
def infer_user_compliance_tasks_with_decisions(legislation_text: str, compliance_obligations: str, data_domains: str) -> str:
    """Infer compliance-related tasks users can perform with decision-making implications."""

    prompt = f"""
    Based on the legislation and compliance obligations, identify specific tasks users can perform with decision implications.

    Legislation Text: {legislation_text}
    Compliance Obligations: {compliance_obligations}
    Data Domains: {data_domains}

    Extract tasks that users can perform to achieve compliance, focusing on:
    1. Documentation and record-keeping for their own data processing
    2. Implementing data protection measures they can control
    3. Handling data subject requests they receive
    4. Conducting self-assessments and audits
    5. Establishing processes and procedures within their control
    6. Making informed decisions about their data
    7. Individual data compliance actions like:
       - Maintaining personal data inventories
       - Implementing data retention schedules
       - Setting up automatic data deletion
       - Creating data backup procedures
       - Establishing secure data sharing practices
       - Using privacy-focused tools and services
       - Regular security updates and patches
    8. Described in simple, clear English - avoid legal jargon

    For each user compliance task:
    - action_type: Type of compliance task (focused on data)
    - title: What users need to accomplish in simple English
    - description: Specific compliance task for users in simple English
    - user_data_steps: Steps involving actual data
    - legislative_requirement: Legal basis for the task
    - compliance_outcome: Compliance goal achieved
    - user_verification_steps: How to confirm compliance
    - derived_from_text: Legislative text requiring this
    - enables_decision: What decision this task enables for users
    - decision_context: What decision scenario this addresses
    - compliance_impact: How this task affects overall compliance

    Return valid JSON array. Base tasks on explicit legislative requirements.
    If no user compliance tasks can be inferred, return empty array.
    """

    try:
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )

        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error inferring user compliance tasks: {str(e)}"


@tool
def infer_user_rights_support_tasks_with_decisions(legislation_text: str, rights_context: str, processing_activities: str) -> str:
    """Infer tasks users can perform to support data subject rights with decision-making capabilities."""

    prompt = f"""
    Analyze the legislation for tasks users can perform to facilitate data subject rights with decision implications.

    Legislation Text: {legislation_text}
    Rights Context: {rights_context}
    Processing Activities: {processing_activities}

    Identify tasks users can perform to support data subject rights:
    1. Setting up systems they control to handle rights requests
    2. Implementing processes for data access, rectification, erasure they can manage
    3. Ensuring data portability capabilities within their systems
    4. Managing consent and withdrawal mechanisms
    5. Handling objections and restrictions
    6. Making informed decisions about rights exercise
    7. Individual rights support actions like:
       - Creating personal data access tools
       - Setting up data export capabilities
       - Implementing consent tracking systems
       - Creating data correction workflows
       - Setting up automated deletion triggers
       - Maintaining contact preferences
       - Using privacy-preserving technologies
    8. Described in simple, clear English - avoid legal jargon

    For each rights-support task:
    - action_type: Type of rights support task (focused on data)
    - title: User-facing task title in simple English
    - description: What users must implement in simple English
    - user_data_steps: Specific data operations required
    - affected_data_categories: Data types involved
    - legislative_requirement: Rights provision requiring this
    - compliance_outcome: Rights facilitation achieved
    - derived_from_text: Text mandating this task
    - enables_decision: What rights-related decision this enables
    - decision_context: What rights scenario this addresses
    - rights_impact: How this task supports rights exercise

    Return valid JSON array. Focus on practical implementation by users.
    If no user rights support tasks can be inferred, return empty array.
    """

    try:
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )

        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error inferring user rights support tasks: {str(e)}"