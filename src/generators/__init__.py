"""
Generators module for CSV to ODRL conversion.
Contains ODRL policy generation components.

Location: src/generators/__init__.py
"""

from .odrl_rule_generator import ODRLRuleGenerator

__all__ = [
    "ODRLRuleGenerator"
]