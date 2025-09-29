"""
CSV processor for reading and validating rule framework input files.
Handles DSS and DataVISA rule frameworks with restriction/condition types.

Location: src/processors/csv_processor.py
"""
import csv
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class RuleFrameworkEntry(BaseModel):
    """Model for a single rule framework entry from CSV."""
    
    id: str = Field(..., description="Unique identifier for the rule")
    rule_framework: str = Field(..., description="Framework type: DSS or DataVISA")
    restriction_condition: str = Field(..., description="Type: restriction or condition")
    rule_name: str = Field(..., description="Title/name of the rule")
    guidance: str = Field(..., description="Complete guidance text with details, actions, evidence")
    
    @field_validator('rule_framework')
    @classmethod
    def validate_framework(cls, v):
        """Validate framework type."""
        valid_frameworks = ['DSS', 'DataVISA', 'dss', 'datavisa']
        if v not in valid_frameworks:
            logger.warning(f"Unknown framework type: {v}. Expected DSS or DataVISA.")
        return v.upper() if v.lower() in ['dss', 'datavisa'] else v
    
    @field_validator('restriction_condition')
    @classmethod
    def validate_type(cls, v):
        """Validate restriction/condition type."""
        valid_types = ['restriction', 'condition', 'Restriction', 'Condition']
        if v not in valid_types:
            logger.warning(f"Unknown type: {v}. Expected restriction or condition.")
        return v.lower()
    
    @field_validator('guidance')
    @classmethod
    def validate_guidance(cls, v):
        """Ensure guidance is not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Guidance text cannot be empty")
        return v.strip()


class CSVProcessor:
    """Processor for CSV input files containing rule framework data."""
    
    def __init__(self):
        """Initialize CSV processor."""
        self.entries: List[RuleFrameworkEntry] = []
        self.statistics = {
            'total_entries': 0,
            'dss_count': 0,
            'datavisa_count': 0,
            'restriction_count': 0,
            'condition_count': 0,
            'validation_errors': 0
        }
    
    def read_csv(self, filepath: str, encoding: str = 'utf-8') -> List[RuleFrameworkEntry]:
        """
        Read CSV file and parse entries.
        
        Expected CSV columns:
        - id: Unique identifier
        - rule_framework: DSS or DataVISA
        - restriction_condition: restriction or condition
        - rule_name: Title of the rule
        - guidance: Complete guidance text
        
        Args:
            filepath: Path to CSV file
            encoding: File encoding (default: utf-8)
            
        Returns:
            List of validated RuleFrameworkEntry objects
        """
        logger.info(f"Reading CSV file: {filepath}")
        
        if not Path(filepath).exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        
        entries = []
        
        try:
            with open(filepath, 'r', encoding=encoding, newline='') as csvfile:
                # Try to detect delimiter
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                sniffer = csv.Sniffer()
                try:
                    delimiter = sniffer.sniff(sample).delimiter
                except:
                    delimiter = ','
                    logger.warning("Could not detect delimiter, using comma")
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                # Validate headers
                expected_headers = {'id', 'rule_framework', 'restriction_condition', 'rule_name', 'guidance'}
                actual_headers = set(reader.fieldnames) if reader.fieldnames else set()
                
                if not expected_headers.issubset(actual_headers):
                    missing = expected_headers - actual_headers
                    raise ValueError(f"Missing required CSV columns: {missing}")
                
                logger.info(f"CSV columns detected: {reader.fieldnames}")
                
                # Process each row
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                    try:
                        # Create entry with exact column names
                        entry = RuleFrameworkEntry(
                            id=row.get('id', '').strip(),
                            rule_framework=row.get('rule_framework', '').strip(),
                            restriction_condition=row.get('restriction_condition', '').strip(),
                            rule_name=row.get('rule_name', '').strip(),
                            guidance=row.get('guidance', '').strip()
                        )
                        
                        entries.append(entry)
                        
                        # Update statistics
                        self.statistics['total_entries'] += 1
                        
                        if entry.rule_framework.upper() == 'DSS':
                            self.statistics['dss_count'] += 1
                        elif entry.rule_framework.upper() == 'DATAVISA':
                            self.statistics['datavisa_count'] += 1
                        
                        if entry.restriction_condition == 'restriction':
                            self.statistics['restriction_count'] += 1
                        elif entry.restriction_condition == 'condition':
                            self.statistics['condition_count'] += 1
                        
                    except Exception as e:
                        logger.error(f"Error parsing row {row_num}: {e}")
                        logger.error(f"Row data: {row}")
                        self.statistics['validation_errors'] += 1
                        continue
        
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
        
        self.entries = entries
        logger.info(f"Successfully loaded {len(entries)} entries from CSV")
        
        return entries
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.statistics
    
    def filter_by_framework(self, framework: str) -> List[RuleFrameworkEntry]:
        """Filter entries by rule framework."""
        framework_upper = framework.upper()
        return [e for e in self.entries if e.rule_framework.upper() == framework_upper]
    
    def filter_by_type(self, entry_type: str) -> List[RuleFrameworkEntry]:
        """Filter entries by restriction/condition type."""
        type_lower = entry_type.lower()
        return [e for e in self.entries if e.restriction_condition == type_lower]
    
    def get_entry_by_id(self, entry_id: str) -> Optional[RuleFrameworkEntry]:
        """Get specific entry by ID."""
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
    
    def validate_all_entries(self) -> Dict[str, List[str]]:
        """
        Validate all entries and return validation report.
        
        Returns:
            Dictionary with 'valid' and 'invalid' lists of IDs
        """
        validation_report = {
            'valid': [],
            'invalid': [],
            'warnings': []
        }
        
        for entry in self.entries:
            try:
                # Check for potential issues
                if len(entry.guidance) < 50:
                    validation_report['warnings'].append(
                        f"{entry.id}: Guidance text is very short ({len(entry.guidance)} chars)"
                    )
                
                if not entry.id:
                    validation_report['invalid'].append("Empty ID found")
                    continue
                
                validation_report['valid'].append(entry.id)
                
            except Exception as e:
                validation_report['invalid'].append(f"{entry.id}: {str(e)}")
        
        return validation_report
    
    def export_to_dict(self) -> List[Dict[str, Any]]:
        """Export entries as list of dictionaries."""
        return [entry.model_dump() for entry in self.entries]
    
    def print_statistics(self):
        """Print processing statistics."""
        print("\n" + "="*60)
        print("CSV PROCESSING STATISTICS")
        print("="*60)
        print(f"Total Entries:        {self.statistics['total_entries']}")
        print(f"DSS Framework:        {self.statistics['dss_count']}")
        print(f"DataVISA Framework:   {self.statistics['datavisa_count']}")
        print(f"Restrictions:         {self.statistics['restriction_count']}")
        print(f"Conditions:           {self.statistics['condition_count']}")
        print(f"Validation Errors:    {self.statistics['validation_errors']}")
        print("="*60)