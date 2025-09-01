"""
Metadata manager for handling legislation document metadata.
Manages country information, adequacy decisions, and file-specific metadata.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from .config import Config
from .event_system import Event, event_bus

logger = logging.getLogger(__name__)

class MetadataManager:
    """Manages legislation metadata configuration."""
    
    def __init__(self, config_file: Path = None):
        self.config_file = config_file or Config.METADATA_CONFIG_FILE
        self.metadata: Dict[str, Any] = {}
        self.load_metadata()
    
    def load_metadata(self):
        """Load metadata from config file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded metadata for {len(self.metadata)} sections")
            else:
                logger.info("No metadata config file found. Creating default structure.")
                self.create_default_config()
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            self.metadata = {}
    
    def create_default_config(self):
        """Create a default metadata configuration file."""
        default_config = {
            "metadata_info": {
                "description": "This file contains metadata for legislation PDFs",
                "version": "1.0",
                "last_updated": datetime.utcnow().isoformat(),
                "format": {
                    "filename.pdf": {
                        "applicable_countries": ["Country1", "Country2"],
                        "adequacy_countries": ["Country3", "Country4"],
                        "effective_date": "YYYY-MM-DD",
                        "jurisdiction": "jurisdiction_name",
                        "regulation_type": "privacy|data_protection|general"
                    }
                }
            },
            "example_files": {
                "gdpr_article_28.pdf": {
                    "applicable_countries": ["Germany", "France", "Italy", "Spain", "Netherlands"],
                    "adequacy_countries": ["Canada", "Japan", "United Kingdom", "Switzerland"],
                    "effective_date": "2018-05-25",
                    "jurisdiction": "EU",
                    "regulation_type": "data_protection"
                },
                "ccpa_regulation.pdf": {
                    "applicable_countries": ["United States", "California"],
                    "adequacy_countries": [],
                    "effective_date": "2020-01-01",
                    "jurisdiction": "California",
                    "regulation_type": "privacy"
                }
            },
            "country_metadata": {
                "adequacy_decisions": {
                    "eu_adequate": ["Andorra", "Argentina", "Canada", "Faroe Islands", "Guernsey", 
                                   "Israel", "Isle of Man", "Japan", "Jersey", "New Zealand", 
                                   "Republic of Korea", "Switzerland", "United Kingdom", "Uruguay"],
                    "last_updated": "2024-01-01"
                }
            }
        }
        
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            self.metadata = default_config
            logger.info(f"Created default metadata config at: {self.config_file}")
        except Exception as e:
            logger.error(f"Error creating default config: {e}")
    
    def get_file_metadata(self, filename: str) -> Dict[str, Any]:
        """Get metadata for a specific PDF file."""
        # Check in example_files and other top-level keys
        for section_name, section_data in self.metadata.items():
            if isinstance(section_data, dict) and filename in section_data:
                file_meta = section_data[filename]
                return {
                    'applicable_countries': file_meta.get('applicable_countries', []),
                    'adequacy_countries': file_meta.get('adequacy_countries', []),
                    'effective_date': file_meta.get('effective_date', ''),
                    'jurisdiction': file_meta.get('jurisdiction', ''),
                    'regulation_type': file_meta.get('regulation_type', '')
                }
        
        # Return empty defaults if no metadata found
        logger.warning(f"No metadata found for {filename}, using empty defaults")
        return {
            'applicable_countries': [],
            'adequacy_countries': [],
            'effective_date': '',
            'jurisdiction': '',
            'regulation_type': ''
        }
    
    async def add_file_metadata(self, filename: str, applicable_countries: List[str], 
                              adequacy_countries: List[str] = None, **kwargs):
        """Add metadata for a new file."""
        if adequacy_countries is None:
            adequacy_countries = []
        
        # Add to example_files section or create new section
        if 'files' not in self.metadata:
            self.metadata['files'] = {}
        
        self.metadata['files'][filename] = {
            'applicable_countries': applicable_countries,
            'adequacy_countries': adequacy_countries,
            'added_at': datetime.utcnow().isoformat(),
            **kwargs
        }
        
        await self.save_metadata()
        
        # Publish event
        await event_bus.publish_event(Event(
            event_type="metadata_updated",
            data={
                "filename": filename,
                "action": "added"
            },
            source="metadata_manager"
        ))
    
    async def save_metadata(self):
        """Save metadata to config file."""
        try:
            self.metadata["metadata_info"]["last_updated"] = datetime.utcnow().isoformat()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            logger.info("Metadata config saved successfully")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def list_configured_files(self) -> List[str]:
        """Get list of files that have metadata configured."""
        configured_files = []
        for section in self.metadata.values():
            if isinstance(section, dict):
                for key in section.keys():
                    if key.endswith('.pdf') or '.' in key:
                        configured_files.append(key)
        return configured_files
    
    def get_adequacy_countries(self) -> List[str]:
        """Get list of countries with adequacy decisions."""
        country_meta = self.metadata.get("country_metadata", {})
        adequacy = country_meta.get("adequacy_decisions", {})
        return adequacy.get("eu_adequate", [])

# Global metadata manager instance
metadata_manager = None

async def initialize_metadata_manager() -> MetadataManager:
    """Initialize the global metadata manager."""
    global metadata_manager
    metadata_manager = MetadataManager()
    logger.info("Metadata manager initialized successfully")
    return metadata_manager

def get_metadata_manager() -> MetadataManager:
    """Get the global metadata manager instance."""
    return metadata_manager