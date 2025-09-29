"""
Managers module for CSV to ODRL conversion.
Contains data category and resource management components.

Location: src/managers/__init__.py
"""

from .data_category_manager import DataCategoryManager, DataCategory

__all__ = [
    "DataCategoryManager",
    "DataCategory"
]