"""
Data Category Manager - Manages scalable data categories with UUID, name, and description.
Supports dynamic addition of new categories discovered during processing.

Location: src/managers/data_category_manager.py
"""
import json
import logging
import uuid
from typing import List, Dict, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from ..services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class DataCategory(BaseModel):
    """Model for a data category with UUID."""
    
    uuid: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Category name")
    description: str = Field(..., description="Detailed description")
    aliases: List[str] = Field(default_factory=list, description="Alternative names/synonyms")
    parent_category: Optional[str] = Field(None, description="Parent category UUID if hierarchical")
    sensitivity_level: str = Field("normal", description="Sensitivity: normal, sensitive, highly_sensitive")
    examples: List[str] = Field(default_factory=list, description="Example data items")
    regulatory_references: List[str] = Field(default_factory=list, description="Related regulations")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class DataCategoryManager:
    """
    Manages data categories with persistent storage.
    Supports dynamic category discovery and enrichment using LLM.
    """
    
    def __init__(self, categories_file: str = "./config/data_categories.json"):
        """
        Initialize data category manager.
        
        Args:
            categories_file: Path to JSON file storing categories
        """
        self.categories_file = Path(categories_file)
        self.categories: Dict[str, DataCategory] = {}
        self.name_to_uuid: Dict[str, str] = {}  # Quick lookup by name
        self.openai_service = OpenAIService()
        
        # Ensure config directory exists
        self.categories_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing categories
        self.load_categories()
        
        # Initialize with base categories if empty
        if not self.categories:
            self._initialize_base_categories()
    
    def load_categories(self):
        """Load categories from JSON file."""
        if not self.categories_file.exists():
            logger.info(f"Categories file not found, will create: {self.categories_file}")
            return
        
        try:
            with open(self.categories_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for cat_data in data:
                category = DataCategory(**cat_data)
                self.categories[category.uuid] = category
                self.name_to_uuid[category.name.lower()] = category.uuid
                
                # Index aliases
                for alias in category.aliases:
                    self.name_to_uuid[alias.lower()] = category.uuid
            
            logger.info(f"Loaded {len(self.categories)} data categories")
        
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
    
    def save_categories(self):
        """Save categories to JSON file."""
        try:
            categories_list = [cat.model_dump() for cat in self.categories.values()]
            
            with open(self.categories_file, 'w', encoding='utf-8') as f:
                json.dump(categories_list, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.categories)} data categories to {self.categories_file}")
        
        except Exception as e:
            logger.error(f"Error saving categories: {e}")
            raise
    
    def add_category(
        self, 
        name: str, 
        description: str,
        aliases: List[str] = None,
        parent_category: str = None,
        sensitivity_level: str = "normal",
        examples: List[str] = None,
        regulatory_references: List[str] = None
    ) -> str:
        """
        Add a new data category.
        
        Args:
            name: Category name
            description: Detailed description
            aliases: Alternative names
            parent_category: Parent category UUID
            sensitivity_level: Sensitivity level
            examples: Example data items
            regulatory_references: Related regulations
            
        Returns:
            UUID of the created category
        """
        from datetime import datetime
        
        # Check if category already exists
        existing_uuid = self.find_category_by_name(name)
        if existing_uuid:
            logger.info(f"Category '{name}' already exists with UUID: {existing_uuid}")
            return existing_uuid
        
        # Create new category
        cat_uuid = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        category = DataCategory(
            uuid=cat_uuid,
            name=name,
            description=description,
            aliases=aliases or [],
            parent_category=parent_category,
            sensitivity_level=sensitivity_level,
            examples=examples or [],
            regulatory_references=regulatory_references or [],
            created_at=timestamp,
            updated_at=timestamp
        )
        
        self.categories[cat_uuid] = category
        self.name_to_uuid[name.lower()] = cat_uuid
        
        for alias in category.aliases:
            self.name_to_uuid[alias.lower()] = cat_uuid
        
        logger.info(f"Added new category: {name} ({cat_uuid})")
        
        return cat_uuid
    
    def find_category_by_name(self, name: str) -> Optional[str]:
        """
        Find category UUID by name or alias.
        
        Args:
            name: Category name or alias (case-insensitive)
            
        Returns:
            Category UUID if found, None otherwise
        """
        return self.name_to_uuid.get(name.lower())
    
    def get_category(self, cat_uuid: str) -> Optional[DataCategory]:
        """Get category by UUID."""
        return self.categories.get(cat_uuid)
    
    def get_category_by_name(self, name: str) -> Optional[DataCategory]:
        """Get category by name."""
        cat_uuid = self.find_category_by_name(name)
        if cat_uuid:
            return self.categories[cat_uuid]
        return None
    
    async def enrich_category_with_llm(self, category_name: str) -> Optional[DataCategory]:
        """
        Use LLM to enrich a category with better description, examples, etc.
        
        Args:
            category_name: Name of category to enrich
            
        Returns:
            Enriched category or None if failed
        """
        cat_uuid = self.find_category_by_name(category_name)
        if not cat_uuid:
            logger.warning(f"Category not found: {category_name}")
            return None
        
        category = self.categories[cat_uuid]
        
        prompt = f"""
        Enrich the following data category with comprehensive information:
        
        Category: {category.name}
        Current Description: {category.description}
        
        Provide enriched information in JSON format:
        {{
          "description": "Comprehensive, clear description of this data category",
          "aliases": ["list of alternative names and synonyms"],
          "examples": ["specific examples of data items in this category"],
          "sensitivity_level": "normal|sensitive|highly_sensitive",
          "regulatory_references": ["relevant regulations like GDPR, CCPA, etc."]
        }}
        
        Make the description clear, comprehensive, and useful for compliance purposes.
        Return ONLY valid JSON.
        """
        
        try:
            messages = [
                SystemMessage(content="You are a data classification expert. Provide comprehensive, accurate information about data categories for compliance purposes. Return only valid JSON."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.openai_service.chat_completion(messages)
            
            # Parse response
            from ..utils.json_parser import SafeJsonParser
            parser = SafeJsonParser()
            enriched_data = parser.parse_json_response(response)
            
            if "error" in enriched_data:
                logger.error(f"Failed to enrich category: {enriched_data}")
                return category
            
            # Update category
            from datetime import datetime
            category.description = enriched_data.get("description", category.description)
            category.aliases = enriched_data.get("aliases", category.aliases)
            category.examples = enriched_data.get("examples", category.examples)
            category.sensitivity_level = enriched_data.get("sensitivity_level", category.sensitivity_level)
            category.regulatory_references = enriched_data.get("regulatory_references", category.regulatory_references)
            category.updated_at = datetime.utcnow().isoformat()
            
            logger.info(f"Enriched category: {category.name}")
            
            return category
        
        except Exception as e:
            logger.error(f"Error enriching category {category_name}: {e}")
            return category
    
    async def discover_and_add_categories(self, category_names: List[str]) -> Dict[str, str]:
        """
        Discover and add multiple new categories using LLM.
        
        Args:
            category_names: List of category names to add
            
        Returns:
            Dictionary mapping category names to UUIDs
        """
        results = {}
        
        for name in category_names:
            # Check if already exists
            existing_uuid = self.find_category_by_name(name)
            if existing_uuid:
                results[name] = existing_uuid
                continue
            
            # Use LLM to create comprehensive category
            try:
                prompt = f"""
                Create a comprehensive data category definition for: {name}
                
                Provide information in JSON format:
                {{
                  "name": "standardized name",
                  "description": "comprehensive description",
                  "aliases": ["alternative names"],
                  "sensitivity_level": "normal|sensitive|highly_sensitive",
                  "examples": ["specific examples"],
                  "regulatory_references": ["related regulations"]
                }}
                
                Return ONLY valid JSON.
                """
                
                messages = [
                    SystemMessage(content="You are a data classification expert. Create comprehensive data category definitions. Return only valid JSON."),
                    HumanMessage(content=prompt)
                ]
                
                response = await self.openai_service.chat_completion(messages)
                
                from ..utils.json_parser import SafeJsonParser
                parser = SafeJsonParser()
                cat_data = parser.parse_json_response(response)
                
                if "error" not in cat_data:
                    cat_uuid = self.add_category(
                        name=cat_data.get("name", name),
                        description=cat_data.get("description", f"Data category: {name}"),
                        aliases=cat_data.get("aliases", []),
                        sensitivity_level=cat_data.get("sensitivity_level", "normal"),
                        examples=cat_data.get("examples", []),
                        regulatory_references=cat_data.get("regulatory_references", [])
                    )
                    results[name] = cat_uuid
                else:
                    # Fallback: create basic category
                    cat_uuid = self.add_category(name, f"Data category: {name}")
                    results[name] = cat_uuid
            
            except Exception as e:
                logger.error(f"Error discovering category {name}: {e}")
                # Create basic category as fallback
                cat_uuid = self.add_category(name, f"Data category: {name}")
                results[name] = cat_uuid
        
        return results
    
    def _initialize_base_categories(self):
        """Initialize with base data categories."""
        base_categories = [
            {
                "name": "Personal Data",
                "description": "Any information relating to an identified or identifiable natural person",
                "aliases": ["personal information", "PII", "personally identifiable information"],
                "sensitivity_level": "normal",
                "examples": ["name", "email address", "phone number", "address"],
                "regulatory_references": ["GDPR Article 4(1)", "CCPA"]
            },
            {
                "name": "Sensitive Personal Data",
                "description": "Special categories of personal data requiring enhanced protection",
                "aliases": ["special category data", "sensitive data"],
                "sensitivity_level": "highly_sensitive",
                "examples": ["racial origin", "health data", "biometric data", "genetic data"],
                "regulatory_references": ["GDPR Article 9", "CCPA sensitive personal information"]
            },
            {
                "name": "Health Data",
                "description": "Personal data related to physical or mental health",
                "aliases": ["medical data", "healthcare data"],
                "sensitivity_level": "highly_sensitive",
                "examples": ["medical records", "prescriptions", "health insurance", "diagnosis"],
                "regulatory_references": ["GDPR Article 9(1)", "HIPAA"]
            },
            {
                "name": "Financial Data",
                "description": "Personal data related to financial transactions and accounts",
                "aliases": ["banking data", "payment data"],
                "sensitivity_level": "sensitive",
                "examples": ["bank account", "credit card", "transaction history", "income"],
                "regulatory_references": ["PCI DSS", "GDPR", "GLBA"]
            },
            {
                "name": "Location Data",
                "description": "Data about geographic position of an individual or device",
                "aliases": ["geolocation data", "GPS data", "tracking data"],
                "sensitivity_level": "sensitive",
                "examples": ["GPS coordinates", "IP address", "cell tower data"],
                "regulatory_references": ["GDPR", "ePrivacy Directive"]
            },
            {
                "name": "Biometric Data",
                "description": "Data from physical, physiological or behavioral characteristics",
                "aliases": ["biometric identifiers"],
                "sensitivity_level": "highly_sensitive",
                "examples": ["fingerprints", "facial recognition", "iris scans", "voice prints"],
                "regulatory_references": ["GDPR Article 9", "BIPA"]
            },
            {
                "name": "Behavioral Data",
                "description": "Data about online and offline behavior patterns",
                "aliases": ["usage data", "activity data", "profiling data"],
                "sensitivity_level": "normal",
                "examples": ["browsing history", "purchase patterns", "app usage", "preferences"],
                "regulatory_references": ["GDPR", "ePrivacy"]
            },
            {
                "name": "Contact Data",
                "description": "Data used for communication and contact purposes",
                "aliases": ["contact information", "communication data"],
                "sensitivity_level": "normal",
                "examples": ["email", "phone number", "mailing address", "social media handles"],
                "regulatory_references": ["GDPR", "CAN-SPAM"]
            }
        ]
        
        for cat_info in base_categories:
            self.add_category(**cat_info)
        
        self.save_categories()
        logger.info(f"Initialized {len(base_categories)} base data categories")
    
    def get_all_categories(self) -> List[DataCategory]:
        """Get all categories."""
        return list(self.categories.values())
    
    def search_categories(self, search_term: str) -> List[DataCategory]:
        """
        Search categories by name, alias, or description.
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of matching categories
        """
        search_lower = search_term.lower()
        matches = []
        
        for category in self.categories.values():
            if (search_lower in category.name.lower() or
                search_lower in category.description.lower() or
                any(search_lower in alias.lower() for alias in category.aliases)):
                matches.append(category)
        
        return matches
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about data categories."""
        total = len(self.categories)
        by_sensitivity = {}
        
        for category in self.categories.values():
            level = category.sensitivity_level
            by_sensitivity[level] = by_sensitivity.get(level, 0) + 1
        
        return {
            "total_categories": total,
            "by_sensitivity": by_sensitivity,
            "categories_file": str(self.categories_file)
        }