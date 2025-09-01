"""
Configuration module for the Legislation Rules Converter.
Handles all configuration settings, environment variables, and constants.
"""

import os
from pathlib import Path
from typing import Dict, Any
import logging

class Config:
    """Global configuration for the legislation rules converter."""
    
    # API Configuration
    BASE_URL = "https://api.openai.com/v1"
    API_KEY = os.getenv("OPENAI_API_KEY")
    CHAT_MODEL = "o3-mini-2025-01-31"
    EMBEDDING_MODEL = "text-embedding-3-large"
    
    # Directory Paths
    PROJECT_ROOT = Path(__file__).parent
    LEGISLATION_PDF_PATH = PROJECT_ROOT / "data" / "legislation_pdfs"
    RULES_OUTPUT_PATH = PROJECT_ROOT / "data" / "extracted_rules"
    EMBEDDINGS_PATH = PROJECT_ROOT / "data" / "embeddings"
    LOGS_PATH = PROJECT_ROOT / "logs"
    EXISTING_RULES_FILE = RULES_OUTPUT_PATH / "all_rules.json"
    METADATA_CONFIG_FILE = PROJECT_ROOT / "config" / "legislation_metadata.json"
    
    # Standards Output Path
    STANDARDS_OUTPUT_PATH = PROJECT_ROOT / "data" / "standards_output"
    
    # Ontology Watching
    WATCH_DIRECTORIES = [RULES_OUTPUT_PATH, STANDARDS_OUTPUT_PATH]
    ONTOLOGY_AUTO_UPDATE = True
    
    # Standard Namespaces
    DPV_NAMESPACE = "https://w3id.org/dpv#"
    ODRL_NAMESPACE = "http://www.w3.org/ns/odrl/2/"
    DPVCG_NAMESPACE = "https://w3id.org/dpv/"
    ODRE_NAMESPACE = "https://w3id.org/def/odre#"
    
    # Processing Configuration
    MAX_CONCURRENT_PROCESSES = 3
    RETRY_ATTEMPTS = 3
    TIMEOUT_SECONDS = 300
    
    # Logging Configuration
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings."""
        if not cls.API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Ensure directories exist
        for path in [cls.LEGISLATION_PDF_PATH, cls.RULES_OUTPUT_PATH, 
                     cls.EMBEDDINGS_PATH, cls.LOGS_PATH, cls.STANDARDS_OUTPUT_PATH]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Ensure config directory exists
        cls.METADATA_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Get logging configuration dictionary."""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': cls.LOG_FORMAT
                },
            },
            'handlers': {
                'default': {
                    'level': cls.LOG_LEVEL,
                    'formatter': 'standard',
                    'class': 'logging.StreamHandler',
                },
                'file': {
                    'level': cls.LOG_LEVEL,
                    'formatter': 'standard',
                    'class': 'logging.FileHandler',
                    'filename': cls.LOGS_PATH / 'legislation_converter.log',
                    'mode': 'a',
                },
            },
            'loggers': {
                '': {
                    'handlers': ['default', 'file'],
                    'level': cls.LOG_LEVEL,
                    'propagate': False
                }
            }
        }

class ModelConfig:
    """Configuration for Pydantic models."""
    use_enum_values = True
    validate_assignment = True
    arbitrary_types_allowed = True

class ProcessingConfig:
    """Configuration for processing strategies."""
    
    # Prompting Strategy Weights
    CHAIN_OF_THOUGHT_WEIGHT = 0.25
    MIXTURE_OF_EXPERTS_WEIGHT = 0.25
    MIXTURE_OF_THOUGHT_WEIGHT = 0.25
    MIXTURE_OF_REASONING_WEIGHT = 0.25
    
    # Confidence Thresholds
    MIN_CONFIDENCE_THRESHOLD = 0.7
    HIGH_CONFIDENCE_THRESHOLD = 0.9
    
    # Extraction Limits
    MAX_RULES_PER_DOCUMENT = 50
    MAX_CONDITIONS_PER_RULE = 20