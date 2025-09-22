"""
Legislation Rules Converter - AI-powered legislation analysis and rule extraction.

A comprehensive system for extracting actionable rules from privacy legislation documents
with dual action inference, decision-making capabilities (yes/no/maybe), semantic web integration, 
and anti-hallucination measures.
"""

__version__ = "2.0.0"
__author__ = "Legislation Rules Converter Team"
__description__ = "AI-powered legislation analysis and rule extraction system with decision-making capabilities"

from .config import Config
from .analyzer import LegislationAnalyzer

__all__ = [
    "Config",
    "LegislationAnalyzer",
    "__version__",
    "__author__",
    "__description__"
]