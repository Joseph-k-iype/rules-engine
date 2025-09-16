"""
Metadata management for legislation configurations.
"""
import json
import os
import logging
from typing import Dict, List, Tuple, Optional, Any

from ..models.base_models import CountryMetadata
from ..config import Config

logger = logging.getLogger(__name__)


class MetadataManager:
    """Manages legislation metadata configuration."""

    def __init__(self, config_file: str = Config.METADATA_CONFIG_FILE):
        self.config_file = config_file
        self.metadata: Dict[str, Any] = {}
        self.load_metadata()

    def load_metadata(self):
        """Load metadata from config file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded metadata for {len(self.metadata)} configurations")
            else:
                logger.warning(f"Metadata config file not found: {self.config_file}")
                logger.warning("Please create legislation_metadata.json with your legislation configuration")
                self.metadata = {}
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            self.metadata = {}

    def get_country_metadata(self, entry_id: str) -> Optional[CountryMetadata]:
        """Get metadata for a specific entry."""
        if entry_id in self.metadata:
            try:
                return CountryMetadata(**self.metadata[entry_id])
            except Exception as e:
                logger.error(f"Error parsing metadata for {entry_id}: {e}")
                return None
        return None

    def get_all_processing_entries(self) -> List[Tuple[str, CountryMetadata]]:
        """Get all processing entries."""
        entries = []
        for entry_id, data in self.metadata.items():
            try:
                metadata = CountryMetadata(**data)
                entries.append((entry_id, metadata))
            except Exception as e:
                logger.warning(f"Skipping invalid entry {entry_id}: {e}")
        return entries

    def save_metadata(self, new_metadata: Dict[str, Any]):
        """Save metadata to config file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(new_metadata, f, indent=2, ensure_ascii=False)
            self.metadata = new_metadata
            logger.info(f"Saved metadata for {len(new_metadata)} configurations")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            raise

    def add_entry(self, entry_id: str, metadata: CountryMetadata):
        """Add or update a metadata entry."""
        try:
            self.metadata[entry_id] = metadata.model_dump()
            self.save_metadata(self.metadata)
            logger.info(f"Added/updated metadata entry: {entry_id}")
        except Exception as e:
            logger.error(f"Error adding metadata entry {entry_id}: {e}")
            raise

    def remove_entry(self, entry_id: str):
        """Remove a metadata entry."""
        if entry_id in self.metadata:
            del self.metadata[entry_id]
            self.save_metadata(self.metadata)
            logger.info(f"Removed metadata entry: {entry_id}")
        else:
            logger.warning(f"Entry {entry_id} not found in metadata")

    def validate_all_entries(self) -> Dict[str, bool]:
        """Validate all metadata entries."""
        validation_results = {}
        for entry_id, data in self.metadata.items():
            try:
                CountryMetadata(**data)
                validation_results[entry_id] = True
            except Exception as e:
                logger.error(f"Invalid metadata for {entry_id}: {e}")
                validation_results[entry_id] = False
        return validation_results