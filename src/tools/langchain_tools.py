"""
LangChain tools for rule extraction and action inference.
"""
from openai import OpenAI
from langchain_core.tools import tool

from ..config import Config


@tool
def extract_rule_conditions(legislation_text: str, focus_area: str) -> str:
    """Extract specific rule conditions from legislation text."""

    prompt = f"""
    Extract rule conditions from the following legislation text, focusing on {focus_area}.

    Return conditions in json-rules-engine format based on explicit requirements in the text.

    Text: {legislation_text}

    Focus on identifying:
    - Specific facts that can be evaluated from the legislation
    - Comparison operators based on legal language
    - Values to compare against as stated in the text
    - Data domains and roles mentioned

    Return valid JSON only. Base conditions on explicit legislative language.
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
def analyze_data_domains(legislation_text: str) -> str:
    """Analyze and identify relevant data domains in legislation."""

    prompt = f"""
    Analyze the following legislation text and identify which data domains are mentioned:
    - data_transfer
    - data_usage
    - data_storage
    - data_collection
    - data_deletion

    Text: {legislation_text}

    Return a JSON object mapping each identified domain to its relevance and the specific text that indicates it.
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
def identify_roles_responsibilities(legislation_text: str) -> str:
    """Identify roles and responsibilities in legislation."""

    prompt = f"""
    Identify the roles and responsibilities mentioned in this legislation:
    - controller
    - processor 
    - joint_controller
    - data_subject

    Text: {legislation_text}

    For each role mentioned, identify their specific obligations and responsibilities as stated in the text.
    Return a JSON object with role mappings based on what is stated.
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
def infer_data_processing_actions(legislation_text: str, data_categories: str, processing_context: str) -> str:
    """Infer specific data processing actions from legislation text."""

    prompt = f"""
    Based on the following legislation text, identify specific organizational actions that must be taken regarding data processing.

    Legislation Text: {legislation_text}
    Data Categories Mentioned: {data_categories}
    Processing Context: {processing_context}

    Extract only actions that are:
    1. Explicitly required by the legislation text
    2. Related to data handling, processing, storage, transfer, or deletion
    3. Actionable by data controllers or processors at organizational level
    4. Have clear data-specific outcomes
    5. Focus on practical data operations like:
       - Data encryption and security measures
       - Data masking and anonymization
       - Access controls and authentication
       - Data retention and deletion procedures
       - Consent management systems
       - Data transfer protocols
       - Audit logging and monitoring
       - Backup and recovery procedures
    6. Described in simple, clear English - avoid legal jargon

    For each action, provide:
    - action_type: Brief descriptive name focused on data operations
    - title: Clear action title in simple English
    - description: What must be done with data in simple English
    - priority: Extract from legislative language (urgent/immediate/high/medium/low)
    - data_specific_steps: Concrete steps related to data handling
    - legislative_requirement: Exact requirement from legislation
    - data_impact: How this affects data processing
    - verification_method: How to confirm compliance
    - derived_from_text: Exact legislative text that requires this action

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
def infer_compliance_verification_actions(legislation_text: str, obligations: str, roles: str) -> str:
    """Infer compliance verification actions from legislation."""

    prompt = f"""
    Based on the legislation text and identified obligations, extract verification and compliance actions.

    Legislation Text: {legislation_text}
    Identified Obligations: {obligations}
    Affected Roles: {roles}

    Focus only on actions that:
    1. Are explicitly required for compliance verification
    2. Involve documentation, reporting, or demonstration of data handling
    3. Are mentioned in the legislation text
    4. Can be performed by the specified roles
    5. Focus on practical data verification like:
       - Data audit procedures
       - Compliance monitoring systems
       - Data processing records
       - Privacy impact assessments
       - Data breach notification procedures
       - Regular security reviews
       - Third-party data processor audits
    6. Described in simple, clear English - avoid legal jargon

    For each verification action:
    - action_type: Type of verification required (focused on data aspects)
    - title: What needs to be verified in simple English
    - description: How to demonstrate compliance in simple English
    - data_specific_steps: Steps involving data or data processes
    - legislative_requirement: Specific legal requirement
    - verification_method: How compliance is verified
    - derived_from_text: Exact text requiring this verification

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
def infer_data_subject_rights_actions(legislation_text: str, rights_mentioned: str, data_domains: str) -> str:
    """Infer actions required to handle data subject rights."""

    prompt = f"""
    Analyze the legislation for requirements related to data subject rights and extract required actions.

    Legislation Text: {legislation_text}
    Rights Mentioned: {rights_mentioned}
    Data Domains: {data_domains}

    Extract actions that:
    1. Are required to facilitate data subject rights
    2. Involve handling, processing, or responding to data subject requests
    3. Are explicitly mentioned in the legislation
    4. Have clear data-handling implications
    5. Focus on practical data rights implementation like:
       - Data access systems and procedures
       - Data rectification workflows
       - Data erasure and deletion procedures
       - Data portability tools and formats
       - Consent withdrawal mechanisms
       - Objection handling processes
       - Automated decision-making controls
    6. Described in simple, clear English - avoid legal jargon

    For each rights-related action:
    - action_type: Type of rights handling required (focused on data operations)
    - title: Rights-related obligation in simple English
    - description: What must be done to support data subject rights in simple English
    - data_specific_steps: Specific data handling steps
    - legislative_requirement: Legal basis for the action
    - data_impact: How this affects data and data processing
    - verification_method: How to confirm rights are being respected
    - derived_from_text: Legislative text requiring this action

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
def infer_user_actionable_tasks(legislation_text: str, data_context: str, user_roles: str) -> str:
    """Infer practical tasks that users can perform based on legislation."""

    prompt = f"""
    Analyze the following legislation text to identify specific tasks that individual users can perform.

    Legislation Text: {legislation_text}
    Data Context: {data_context}
    User Roles: {user_roles}

    Extract ONLY tasks that are:
    1. Explicitly required by the legislation text
    2. Actionable by individual users with commonly available tools/systems
    3. Related to data operations users can control
    4. Have clear compliance outcomes
    5. Can be practically implemented by users
    6. Focus on individual data actions like:
       - Encrypting personal files and communications
       - Using privacy settings on platforms
       - Managing consent preferences
       - Securing personal data with passwords
       - Backing up important data securely
       - Deleting unnecessary personal data
       - Reviewing data sharing permissions
       - Using secure communication tools
    7. Described in simple, clear English - avoid legal jargon

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
def infer_user_compliance_tasks(legislation_text: str, compliance_obligations: str, data_domains: str) -> str:
    """Infer compliance-related tasks users can perform."""

    prompt = f"""
    Based on the legislation and compliance obligations, identify specific tasks users can perform.

    Legislation Text: {legislation_text}
    Compliance Obligations: {compliance_obligations}
    Data Domains: {data_domains}

    Extract tasks that users can perform to achieve compliance, focusing on:
    1. Documentation and record-keeping for their own data processing
    2. Implementing data protection measures they can control
    3. Handling data subject requests they receive
    4. Conducting self-assessments and audits
    5. Establishing processes and procedures within their control
    6. Individual data compliance actions like:
       - Maintaining personal data inventories
       - Implementing data retention schedules
       - Setting up automatic data deletion
       - Creating data backup procedures
       - Establishing secure data sharing practices
       - Using privacy-focused tools and services
       - Regular security updates and patches
    7. Described in simple, clear English - avoid legal jargon

    For each user compliance task:
    - action_type: Type of compliance task (focused on data)
    - title: What users need to accomplish in simple English
    - description: Specific compliance task for users in simple English
    - user_data_steps: Steps involving actual data
    - legislative_requirement: Legal basis for the task
    - compliance_outcome: Compliance goal achieved
    - user_verification_steps: How to confirm compliance
    - derived_from_text: Legislative text requiring this

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
def infer_user_rights_support_tasks(legislation_text: str, rights_context: str, processing_activities: str) -> str:
    """Infer tasks users can perform to support data subject rights."""

    prompt = f"""
    Analyze the legislation for tasks users can perform to facilitate data subject rights.

    Legislation Text: {legislation_text}
    Rights Context: {rights_context}
    Processing Activities: {processing_activities}

    Identify tasks users can perform to support data subject rights:
    1. Setting up systems they control to handle rights requests
    2. Implementing processes for data access, rectification, erasure they can manage
    3. Ensuring data portability capabilities within their systems
    4. Managing consent and withdrawal mechanisms
    5. Handling objections and restrictions
    6. Individual rights support actions like:
       - Creating personal data access tools
       - Setting up data export capabilities
       - Implementing consent tracking systems
       - Creating data correction workflows
       - Setting up automated deletion triggers
       - Maintaining contact preferences
       - Using privacy-preserving technologies
    7. Described in simple, clear English - avoid legal jargon

    For each rights-support task:
    - action_type: Type of rights support task (focused on data)
    - title: User-facing task title in simple English
    - description: What users must implement in simple English
    - user_data_steps: Specific data operations required
    - affected_data_categories: Data types involved
    - legislative_requirement: Rights provision requiring this
    - compliance_outcome: Rights facilitation achieved
    - derived_from_text: Text mandating this task

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