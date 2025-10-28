"""
Global configuration for the legislation rules converter.
"""
import os
from openai import OpenAI


class Config:
    """Global configuration for the legislation rules converter."""
    BASE_URL = "https://api.openai.com/v1"
    API_KEY = os.getenv("OPENAI_API_KEY")
    CHAT_MODEL = "o3-mini-2025-01-31"
    EMBEDDING_MODEL = "text-embedding-3-large"

    # Paths
    LEGISLATION_PDF_PATH = "./legislation_pdfs/"
    RULES_OUTPUT_PATH = "./extracted_rules/"
    EMBEDDINGS_PATH = "./embeddings/"
    LOGS_PATH = "./logs/"
    EXISTING_RULES_FILE = "./extracted_rules/all_rules.json"
    METADATA_CONFIG_FILE = "./config/legislation_metadata.json"

    # Combined Standards Output Path
    STANDARDS_OUTPUT_PATH = "./standards_output/"

    # Updated Standard Namespaces - Latest DPV v2.1
    DPV_NAMESPACE = "https://w3id.org/dpv#"
    DPV_PD_NAMESPACE = "https://w3id.org/dpv/dpv-pd#"
    DPV_TECH_NAMESPACE = "https://w3id.org/dpv/tech#"
    DPV_LEGAL_NAMESPACE = "https://w3id.org/dpv/legal/"
    ODRL_NAMESPACE = "http://www.w3.org/ns/odrl/2/"
    DPVCG_NAMESPACE = "https://w3id.org/dpv/"
    ACTION_NAMESPACE = "https://w3id.org/dpv/actions#"

    # PDF Processing Configuration
    CHUNK_SIZE = 4000  # Characters per chunk for large documents
    OVERLAP_SIZE = 200  # Character overlap between chunks
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB threshold for chunking


# Export module-level variables for backward compatibility
OPENAI_MODEL = Config.CHAT_MODEL
API_KEY = Config.API_KEY
BASE_URL = Config.BASE_URL
EMBEDDING_MODEL = Config.EMBEDDING_MODEL


def get_openai_client() -> OpenAI:
    """
    Get OpenAI client instance with API key from environment.
    
    Returns:
        OpenAI: Configured OpenAI client
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    if not Config.API_KEY:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Please set it using: export OPENAI_API_KEY='your-api-key'"
        )
    
    return OpenAI(
        api_key=Config.API_KEY,
        base_url=Config.BASE_URL
    )