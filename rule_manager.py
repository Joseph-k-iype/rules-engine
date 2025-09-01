"""
Rule management system for storing, retrieving, and managing legislation rules.
Handles rule persistence, versioning, and change tracking.
"""

import json
import logging
import asyncio
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
from pathlib import Path
import uuid
import shutil

from .config import Config
from .models import LegislationRule, RuleChangeEvent, ProcessingStatus
from .event_system import Event, event_bus

logger = logging.getLogger(__name__)

class RuleManager:
    """Manages legislation rules with versioning and change tracking."""
    
    def __init__(self, rules_file: Path = None):
        self.rules_file = rules_file or Config.EXISTING_RULES_FILE
        self.rules_backup_dir = self.rules_file.parent / "backups"
        self.existing_rules: List[LegislationRule] = []
        self.rule_versions: Dict[str, List[Dict[str, Any]]] = {}
        self.rule_index: Dict[str, int] = {}  # rule_id -> index in existing_rules
        
        # Ensure directories exist
        self.rules_file.parent.mkdir(parents=True, exist_ok=True)
        self.rules_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing rules
        asyncio.create_task(self._load_existing_rules())
    
    async def _load_existing_rules(self):
        """Load existing rules from file."""
        try:
            if self.rules_file.exists():
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                
                for rule_data in rules_data:
                    try:
                        rule = LegislationRule(**rule_data)
                        self.existing_rules.append(rule)
                        # Build index
                        self.rule_index[rule.id] = len(self.existing_rules) - 1
                    except Exception as e:
                        logger.warning(f"Skipping invalid existing rule: {e}")
                
                logger.info(f"Loaded {len(self.existing_rules)} existing rules")
            else:
                logger.info("No existing rules file found. Starting fresh.")
        except Exception as e:
            logger.error(f"Error loading existing rules: {e}")
            self.existing_rules = []
            self.rule_index = {}
    
    async def add_rule(self, rule: LegislationRule) -> bool:
        """Add a new rule."""
        try:
            # Check if rule already exists
            if rule.id in self.rule_index:
                logger.warning(f"Rule {rule.id} already exists. Use update_rule instead.")
                return False
            
            # Add to collections
            self.existing_rules.append(rule)
            self.rule_index[rule.id] = len(self.existing_rules) - 1
            
            # Save to file
            await self._save_rules()
            
            # Publish event
            await event_bus.publish_event(Event(
                event_type="rule_created",
                data={
                    "rule": rule.model_dump(),
                    "rule_id": rule.id
                },
                source="rule_manager"
            ))
            
            logger.info(f"Added rule: {rule.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding rule {rule.id}: {e}")
            return False
    
    async def update_rule(self, rule: LegislationRule) -> bool:
        """Update an existing rule."""
        try:
            if rule.id not in self.rule_index:
                logger.warning(f"Rule {rule.id} does not exist. Use add_rule instead.")
                return False
            
            # Get old rule for versioning
            rule_index = self.rule_index[rule.id]
            old_rule = self.existing_rules[rule_index]
            
            # Store version
            await self._store_rule_version(rule.id, old_rule.model_dump())
            
            # Update rule
            self.existing_rules[rule_index] = rule
            
            # Save to file
            await self._save_rules()
            
            # Publish event
            await event_bus.publish_event(Event(
                event_type="rule_updated",
                data={
                    "rule": rule.model_dump(),
                    "old_rule": old_rule.model_dump(),
                    "rule_id": rule.id
                },
                source="rule_manager"
            ))
            
            logger.info(f"Updated rule: {rule.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating rule {rule.id}: {e}")
            return False
    
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule."""
        try:
            if rule_id not in self.rule_index:
                logger.warning(f"Rule {rule_id} does not exist.")
                return False
            
            # Get rule index
            rule_index = self.rule_index[rule_id]
            old_rule = self.existing_rules[rule_index]
            
            # Store final version
            await self._store_rule_version(rule_id, old_rule.model_dump())
            
            # Remove from collections
            del self.existing_rules[rule_index]
            del self.rule_index[rule_id]
            
            # Rebuild index (indices shifted after deletion)
            self._rebuild_index()
            
            # Save to file
            await self._save_rules()
            
            # Publish event
            await event_bus.publish_event(Event(
                event_type="rule_deleted",
                data={
                    "rule_id": rule_id,
                    "deleted_rule": old_rule.model_dump()
                },
                source="rule_manager"
            ))
            
            logger.info(f"Deleted rule: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting rule {rule_id}: {e}")
            return False
    
    async def get_rule(self, rule_id: str) -> Optional[LegislationRule]:
        """Get a rule by ID."""
        if rule_id in self.rule_index:
            return self.existing_rules[self.rule_index[rule_id]]
        return None
    
    async def get_all_rules(self) -> List[LegislationRule]:
        """Get all rules."""
        return self.existing_rules.copy()
    
    async def search_rules(self, query: str, field: str = None) -> List[LegislationRule]:
        """Search rules by query."""
        results = []
        query_lower = query.lower()
        
        for rule in self.existing_rules:
            match = False
            
            if field is None:
                # Search all text fields
                searchable_text = f"{rule.name} {rule.description} {rule.source_article} {rule.source_file}".lower()
                match = query_lower in searchable_text
            elif field == "name":
                match = query_lower in rule.name.lower()
            elif field == "description":
                match = query_lower in rule.description.lower()
            elif field == "source_file":
                match = query_lower in rule.source_file.lower()
            elif field == "source_article":
                match = query_lower in rule.source_article.lower()
            
            if match:
                results.append(rule)
        
        return results
    
    async def get_rules_by_source(self, source_file: str) -> List[LegislationRule]:
        """Get all rules from a specific source file."""
        return [rule for rule in self.existing_rules if rule.source_file == source_file]
    
    async def get_rules_by_role(self, role: str) -> List[LegislationRule]:
        """Get all rules affecting a specific role."""
        results = []
        for rule in self.existing_rules:
            if (rule.primary_impacted_role and rule.primary_impacted_role.value == role) or \
               (rule.secondary_impacted_role and rule.secondary_impacted_role.value == role):
                results.append(rule)
        return results
    
    async def save_new_rules(self, new_rules: List[LegislationRule]) -> int:
        """Save new rules, avoiding duplicates."""
        added_count = 0
        
        for rule in new_rules:
            if rule.id not in self.rule_index:
                await self.add_rule(rule)
                added_count += 1
            else:
                logger.debug(f"Skipping duplicate rule: {rule.id}")
        
        if added_count > 0:
            # Publish batch event
            await event_bus.publish_event(Event(
                event_type="rules_batch_updated",
                data={
                    "rules": [rule.model_dump() for rule in new_rules],
                    "added_count": added_count
                },
                source="rule_manager"
            ))
        
        logger.info(f"Saved {added_count} new rules ({len(new_rules)} total provided)")
        return added_count
    
    async def load_rules_from_file(self, file_path: Path) -> List[LegislationRule]:
        """Load rules from a specific file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            rules = []
            for rule_data in rules_data:
                try:
                    rule = LegislationRule(**rule_data)
                    rules.append(rule)
                except Exception as e:
                    logger.warning(f"Skipping invalid rule from {file_path}: {e}")
            
            return rules
            
        except Exception as e:
            logger.error(f"Error loading rules from {file_path}: {e}")
            return []
    
    async def export_rules(self, file_path: Path, format: str = "json") -> bool:
        """Export rules to file in specified format."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(
                        [rule.model_dump() for rule in self.existing_rules],
                        f,
                        indent=2,
                        default=str,
                        ensure_ascii=False
                    )
            elif format == "csv":
                await self._export_to_csv(file_path)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
            
            logger.info(f"Exported {len(self.existing_rules)} rules to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting rules to {file_path}: {e}")
            return False
    
    async def backup_rules(self) -> Path:
        """Create a backup of current rules."""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = self.rules_backup_dir / f"rules_backup_{timestamp}.json"
            
            await self.export_rules(backup_file, "json")
            logger.info(f"Created rules backup: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    async def restore_rules(self, backup_file: Path) -> bool:
        """Restore rules from backup."""
        try:
            # Create current backup before restore
            await self.backup_rules()
            
            # Load rules from backup
            restored_rules = await self.load_rules_from_file(backup_file)
            
            if not restored_rules:
                logger.error("No valid rules found in backup file")
                return False
            
            # Replace current rules
            self.existing_rules = restored_rules
            self._rebuild_index()
            
            # Save to main file
            await self._save_rules()
            
            # Publish event
            await event_bus.publish_event(Event(
                event_type="rules_restored",
                data={
                    "backup_file": str(backup_file),
                    "restored_count": len(restored_rules)
                },
                source="rule_manager"
            ))
            
            logger.info(f"Restored {len(restored_rules)} rules from {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring rules from {backup_file}: {e}")
            return False
    
    def get_context_summary(self) -> str:
        """Get a summary of existing rules for context."""
        if not self.existing_rules:
            return "No existing rules found."
        
        summary = f"Existing Rules Context ({len(self.existing_rules)} rules):\n\n"
        
        # Group by source
        sources = {}
        for rule in self.existing_rules:
            source = rule.source_article
            if source not in sources:
                sources[source] = []
            sources[source].append(rule)
        
        for source, rules in sources.items():
            summary += f"Source: {source} ({len(rules)} rules)\n"
            for rule in rules[:3]:  # Show first 3 rules per source
                summary += f"  - {rule.name}: {rule.description[:100]}...\n"
            if len(rules) > 3:
                summary += f"  ... and {len(rules) - 3} more rules\n"
            summary += "\n"
        
        return summary
    
    def get_processed_files(self) -> Set[str]:
        """Get set of already processed PDF files."""
        processed = set()
        for rule in self.existing_rules:
            if hasattr(rule, 'source_file'):
                processed.add(rule.source_file)
        return processed
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rule statistics."""
        if not self.existing_rules:
            return {
                "total_rules": 0,
                "sources": 0,
                "avg_confidence": 0.0
            }
        
        sources = set()
        roles = {}
        categories = {}
        total_confidence = 0.0
        
        for rule in self.existing_rules:
            sources.add(rule.source_file)
            total_confidence += rule.confidence_score
            
            # Count roles
            if rule.primary_impacted_role:
                role_name = rule.primary_impacted_role.value
                roles[role_name] = roles.get(role_name, 0) + 1
            
            # Count categories
            for category in rule.data_category:
                cat_name = category.value
                categories[cat_name] = categories.get(cat_name, 0) + 1
        
        return {
            "total_rules": len(self.existing_rules),
            "sources": len(sources),
            "avg_confidence": total_confidence / len(self.existing_rules),
            "roles_distribution": roles,
            "categories_distribution": categories,
            "backup_count": len(list(self.rules_backup_dir.glob("*.json")))
        }
    
    async def _save_rules(self):
        """Save rules to file."""
        try:
            # Create backup before saving
            if self.rules_file.exists():
                backup_file = self.rules_file.with_suffix(f".backup.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
                shutil.copy2(self.rules_file, backup_file)
            
            # Save current rules
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [rule.model_dump() for rule in self.existing_rules],
                    f,
                    indent=2,
                    default=str,
                    ensure_ascii=False
                )
            
            logger.debug(f"Saved {len(self.existing_rules)} rules to {self.rules_file}")
            
        except Exception as e:
            logger.error(f"Error saving rules: {e}")
            raise
    
    def _rebuild_index(self):
        """Rebuild the rule index after changes."""
        self.rule_index = {}
        for i, rule in enumerate(self.existing_rules):
            self.rule_index[rule.id] = i
    
    async def _store_rule_version(self, rule_id: str, rule_data: Dict[str, Any]):
        """Store a version of a rule."""
        if rule_id not in self.rule_versions:
            self.rule_versions[rule_id] = []
        
        version_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": rule_data
        }
        
        self.rule_versions[rule_id].append(version_data)
        
        # Keep only last 10 versions per rule
        if len(self.rule_versions[rule_id]) > 10:
            self.rule_versions[rule_id] = self.rule_versions[rule_id][-10:]
    
    async def get_rule_versions(self, rule_id: str) -> List[Dict[str, Any]]:
        """Get version history for a rule."""
        return self.rule_versions.get(rule_id, [])
    
    async def _export_to_csv(self, file_path: Path):
        """Export rules to CSV format."""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            headers = [
                'id', 'name', 'description', 'source_article', 'source_file',
                'primary_impacted_role', 'secondary_impacted_role', 'data_category',
                'applicable_countries', 'adequacy_countries',
                'conditions_count', 'event_type', 'priority', 'confidence_score',
                'extraction_method', 'extracted_at'
            ]
            writer.writerow(headers)
            
            # Write data rows
            for rule in self.existing_rules:
                primary_role = rule.primary_impacted_role.value if rule.primary_impacted_role else ""
                secondary_role = rule.secondary_impacted_role.value if rule.secondary_impacted_role else ""
                data_categories = ", ".join([cat.value for cat in rule.data_category])
                conditions_count = sum(len(conditions) for conditions in rule.conditions.values())
                
                writer.writerow([
                    rule.id,
                    rule.name,
                    rule.description,
                    rule.source_article,
                    rule.source_file,
                    primary_role,
                    secondary_role,
                    data_categories,
                    ", ".join(rule.applicable_countries),
                    ", ".join(rule.adequacy_countries),
                    conditions_count,
                    rule.event.type,
                    rule.priority,
                    rule.confidence_score,
                    rule.extraction_method,
                    rule.extracted_at.isoformat()
                ])

# Global rule manager instance
rule_manager = None

async def initialize_rule_manager() -> RuleManager:
    """Initialize the global rule manager."""
    global rule_manager
    rule_manager = RuleManager()
    await rule_manager._load_existing_rules()
    logger.info("Rule manager initialized successfully")
    return rule_manager

def get_rule_manager() -> RuleManager:
    """Get the global rule manager instance."""
    return rule_manager