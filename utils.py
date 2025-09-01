"""
Utility functions and classes for the legislation rules converter.
"""

import json
import logging
import re
from typing import Dict, Any, Optional

from .config import Config  # Added Config import

logger = logging.getLogger(__name__)

class SafeJsonParser:
    """Safe JSON parsing with error handling and validation."""
    
    @staticmethod
    def parse_json_response(response: str) -> Dict[str, Any]:
        """Safely parse JSON response from LLM."""
        try:
            # Clean the response
            cleaned = response.strip()
            
            # Handle code blocks
            if "```json" in cleaned:
                start = cleaned.find("```json") + 7
                end = cleaned.find("```", start)
                if end != -1:
                    cleaned = cleaned[start:end].strip()
            elif "```" in cleaned:
                start = cleaned.find("```") + 3
                end = cleaned.find("```", start)
                if end != -1:
                    cleaned = cleaned[start:end].strip()
            
            # Try to parse JSON
            parsed = json.loads(cleaned)
            return parsed
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}. Attempting to fix...")
            
            # Try to fix common JSON issues
            try:
                # Remove trailing commas
                fixed = re.sub(r',(\s*[}\]])', r'\1', cleaned)
                # Fix unescaped quotes in strings
                fixed = re.sub(r'(?<!\\)"(?=[^"]*"[^"]*$)', r'\"', fixed)
                parsed = json.loads(fixed)
                return parsed
            except Exception:
                logger.error(f"Could not parse JSON response: {cleaned[:200]}...")
                return {"error": "Failed to parse JSON", "raw_response": cleaned}
    
    @staticmethod
    def validate_rule_structure(data: Dict[str, Any]) -> bool:
        """Validate that parsed data follows expected rule structure."""
        required_fields = ['id', 'name', 'description', 'conditions', 'event']
        return all(field in data for field in required_fields)

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    import logging.config
    
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': log_level,
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'file': {
                'level': log_level,
                'formatter': 'standard',
                'class': 'logging.FileHandler',
                'filename': Config.LOGS_PATH / 'legislation_converter.log',  # Fixed Config usage
                'mode': 'a',
            },
        },
        'loggers': {
            '': {
                'handlers': ['default', 'file'],
                'level': log_level,
                'propagate': False
            }
        }
    }
    
    Config.LOGS_PATH.mkdir(parents=True, exist_ok=True)  # Fixed Config usage
    logging.config.dictConfig(log_config)

def validate_environment():
    """Validate environment setup."""
    errors = []
    warnings = []
    
    # Check API key
    if not Config.API_KEY:  # Fixed Config usage
        errors.append("OPENAI_API_KEY environment variable is required")
    
    # Check required directories
    required_dirs = [
        Config.LEGISLATION_PDF_PATH,  # Fixed Config usage
        Config.RULES_OUTPUT_PATH,  # Fixed Config usage
        Config.STANDARDS_OUTPUT_PATH,  # Fixed Config usage
        Config.LOGS_PATH  # Fixed Config usage
    ]
    
    for directory in required_dirs:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create directory {directory}: {e}")
    
    # Check optional dependencies
    try:
        import pymupdf
        import pdfplumber
    except ImportError:
        warnings.append("PDF processing libraries not available. Install PyMuPDF or pdfplumber.")
    
    try:
        import rdflib
    except ImportError:
        warnings.append("RDFLib not available. TTL generation will be limited.")
    
    try:
        import watchdog
    except ImportError:
        warnings.append("Watchdog not available. File monitoring will be disabled.")
    
    return errors, warnings

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

class ProgressTracker:
    """Simple progress tracking utility."""
    
    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.start_time = None
    
    def start(self):
        """Start tracking progress."""
        import time
        self.start_time = time.time()
    
    def update(self, increment: int = 1):
        """Update progress."""
        self.current += increment
    
    def get_progress(self) -> float:
        """Get progress percentage."""
        if self.total == 0:
            return 100.0
        return min(100.0, (self.current / self.total) * 100.0)
    
    def get_eta(self) -> Optional[float]:
        """Get estimated time to completion."""
        if self.start_time is None or self.current == 0:
            return None
        
        import time
        elapsed = time.time() - self.start_time
        rate = self.current / elapsed
        remaining = self.total - self.current
        
        if rate > 0:
            return remaining / rate
        return None