"""
Rule management service for handling existing legislation rules.
"""
import json
import os
import logging
from typing import List

from ..models.rules import LegislationRule
from ..config import Config

logger = logging.getLogger(__name__)


class RuleManager:
    """Manages existing rules."""

    def __init__(self, rules_file: str = Config.EXISTING_RULES_FILE):
        self.rules_file = rules_file
        self.existing_rules: List[LegislationRule] = []
        self.load_existing_rules()

    def load_existing_rules(self):
        """Load existing rules from file."""
        try:
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)

                for rule_data in rules_data:
                    try:
                        rule = LegislationRule(**rule_data)
                        self.existing_rules.append(rule)
                    except Exception as e:
                        logger.warning(f"Skipping invalid existing rule: {e}")

                logger.info(f"Loaded {len(self.existing_rules)} existing rules")
            else:
                logger.info("No existing rules file found. Starting fresh.")
        except Exception as e:
            logger.error(f"Error loading existing rules: {e}")
            self.existing_rules = []

    def save_rules(self, new_rules: List[LegislationRule]):
        """Save new rules, appending to existing ones."""
        all_rules = self.existing_rules + new_rules

        unique_rules = []
        seen_ids = set()
        for rule in all_rules:
            if rule.id not in seen_ids:
                unique_rules.append(rule)
                seen_ids.add(rule.id)

        os.makedirs(os.path.dirname(self.rules_file), exist_ok=True)
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump(
                [rule.model_dump() for rule in unique_rules], 
                f, 
                indent=2, 
                default=str,
                ensure_ascii=False
            )

        self.existing_rules = unique_rules
        logger.info(f"Saved {len(unique_rules)} total rules ({len(new_rules)} new)")

    def get_context_summary(self) -> str:
        """Get a summary of existing rules for context."""
        if not self.existing_rules:
            return "No existing rules found."

        summary = f"Existing Rules Context ({len(self.existing_rules)} rules):\n\n"

        sources = {}
        for rule in self.existing_rules:
            source = rule.source_article
            if source not in sources:
                sources[source] = []
            sources[source].append(rule)

        for source, rules in sources.items():
            summary += f"Source: {source} ({len(rules)} rules)\n"
            for rule in rules[:3]:
                total_actions = len(rule.actions)
                total_user_actions = len(rule.user_actions)
                summary += f"  - {rule.name}: {rule.description[:100]}... ({total_actions} rule actions, {total_user_actions} user actions)\n"
            if len(rules) > 3:
                summary += f"  ... and {len(rules) - 3} more rules\n"
            summary += "\n"

        return summary

    def find_rules_by_source(self, source_article: str) -> List[LegislationRule]:
        """Find rules by source article."""
        return [rule for rule in self.existing_rules if rule.source_article == source_article]

    def find_rules_by_role(self, role: str) -> List[LegislationRule]:
        """Find rules by primary impacted role."""
        return [rule for rule in self.existing_rules 
                if rule.primary_impacted_role and rule.primary_impacted_role.value == role]

    def find_rules_by_data_category(self, category: str) -> List[LegislationRule]:
        """Find rules by data category."""
        rules = []
        for rule in self.existing_rules:
            for data_cat in rule.data_category:
                if data_cat.value == category:
                    rules.append(rule)
                    break
        return rules

    def find_rules_by_country(self, country: str) -> List[LegislationRule]:
        """Find rules by applicable country."""
        return [rule for rule in self.existing_rules 
                if country in rule.applicable_countries]

    def get_statistics(self) -> dict:
        """Get statistics about existing rules."""
        stats = {
            'total_rules': len(self.existing_rules),
            'total_actions': sum(len(rule.actions) for rule in self.existing_rules),
            'total_user_actions': sum(len(rule.user_actions) for rule in self.existing_rules),
            'sources': set(rule.source_article for rule in self.existing_rules),
            'countries': set(country for rule in self.existing_rules for country in rule.applicable_countries),
            'roles': set(rule.primary_impacted_role.value for rule in self.existing_rules if rule.primary_impacted_role),
            'data_categories': set(cat.value for rule in self.existing_rules for cat in rule.data_category)
        }
        
        # Convert sets to lists for JSON serialization
        stats['sources'] = list(stats['sources'])
        stats['countries'] = list(stats['countries'])
        stats['roles'] = list(stats['roles'])
        stats['data_categories'] = list(stats['data_categories'])
        
        return stats

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule by ID."""
        original_count = len(self.existing_rules)
        self.existing_rules = [rule for rule in self.existing_rules if rule.id != rule_id]
        
        if len(self.existing_rules) < original_count:
            self.save_rules([])  # Save current state
            logger.info(f"Deleted rule {rule_id}")
            return True
        else:
            logger.warning(f"Rule {rule_id} not found")
            return False

    def update_rule(self, updated_rule: LegislationRule) -> bool:
        """Update an existing rule."""
        for i, rule in enumerate(self.existing_rules):
            if rule.id == updated_rule.id:
                self.existing_rules[i] = updated_rule
                self.save_rules([])  # Save current state
                logger.info(f"Updated rule {updated_rule.id}")
                return True
        
        logger.warning(f"Rule {updated_rule.id} not found for update")
        return False