"""
Legislation Rules Converter - AI-powered legislation analysis and rule extraction.

A comprehensive system for extracting actionable rules from privacy legislation documents
with dual action inference, semantic web integration, and anti-hallucination measures.
"""

__version__ = "1.0.0"
__author__ = "Legislation Rules Converter Team"
__description__ = "AI-powered legislation analysis and rule extraction system"

from .config import Config
from .analyzer import LegislationAnalyzer

__all__ = [
    "Config",
    "LegislationAnalyzer",
    "__version__",
    "__author__",
    "__description__"
]