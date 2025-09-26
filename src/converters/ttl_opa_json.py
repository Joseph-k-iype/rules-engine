#!/usr/bin/env python3
"""
TTL to JSON Converter for Legislation Rules - Query-Focused Version
Converts Turtle (TTL) ontology files to JSON format suitable for OPA rule querying.
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys
import argparse


@dataclass
class Condition:
    fact: str
    operator: str
    value: str
    description: Optional[str] = None


@dataclass
class ConditionLogic:
    logic_type: str
    conditions: List[Condition]


@dataclass
class Action:
    id: str
    action_category: str
    action_type: str
    title: str
    description: str
    confidence_score: float
    responsible_role: Optional[str] = None
    legislative_requirement: Optional[str] = None
    timeline: Optional[str] = None
    data_specific_steps: List[str] = None
    user_data_steps: List[str] = None


@dataclass
class LegislationRule:
    id: str
    title: str
    description: str
    source_article: str
    source_file: str
    confidence_score: float
    primary_impacted_role: str
    data_categories: List[str]
    processing_purposes: List[str]
    applicable_countries: List[str]
    adequacy_countries: List[str]
    extracted_at: str
    extraction_method: str
    actions: List[Action]
    condition_logic: ConditionLogic = None
    tags: List[str] = None
    legal_basis: List[str] = None
    risk_level: str = None


class TTLParser:
    def __init__(self):
        self.prefixes = {}
        self.rules = []
        self.actions = {}
        self.condition_logic = {}
        self.conditions = {}
        
    def parse_prefixes(self, content: str) -> None:
        """Extract namespace prefixes from TTL content"""
        prefix_pattern = r'@prefix\s+(\w+):\s+<([^>]+)>\s+\.'
        matches = re.findall(prefix_pattern, content)
        
        for prefix, uri in matches:
            self.prefixes[prefix] = uri
            
    def expand_uri(self, short_uri: str) -> str:
        """Expand prefixed URI to full URI"""
        if ':' in short_uri and not short_uri.startswith('http'):
            prefix, local = short_uri.split(':', 1)
            if prefix in self.prefixes:
                return self.prefixes[prefix] + local
        return short_uri
    
    def extract_literal_value(self, value: str) -> Any:
        """Extract value from RDF literal"""
        # Handle string literals with quotes
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        
        # Handle typed literals
        if '^^' in value:
            literal_value, datatype = value.split('^^', 1)
            literal_value = literal_value.strip('"')
            
            if 'xsd:float' in datatype:
                return float(literal_value)
            elif 'xsd:int' in datatype or 'xsd:integer' in datatype:
                return int(literal_value)
            elif 'xsd:dateTime' in datatype:
                return literal_value
            elif 'xsd:boolean' in datatype:
                return literal_value.lower() == 'true'
        
        # Handle simple values
        if value.replace('.', '').replace('-', '').isdigit():
            return float(value) if '.' in value else int(value)
        
        return value
    
    def parse_property_values(self, content: str, subject: str) -> Dict[str, Any]:
        """Parse properties for a given subject"""
        properties = {}
        
        # Find the subject block - more flexible pattern
        patterns = [
            rf'{re.escape(subject)}\s+a\s+[^;]+;(.*?)(?=\n\s*\w+:|\.|\Z)',
            rf'{re.escape(subject)}\s+[^;]*;(.*?)(?=\n\s*\w+:|\.|\Z)'
        ]
        
        property_block = None
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                property_block = match.group(1)
                break
        
        if not property_block:
            return properties
        
        # Parse individual properties - handle multi-line better
        lines = property_block.split(';')
        current_property = ""
        
        for line in lines:
            line = line.strip()
            if not line or line == '.':
                continue
            
            # Check if this line starts a new property or continues the previous one
            if re.match(r'^\s*\w+:', line):
                # Process previous property if exists
                if current_property:
                    self._process_property_line(current_property, properties)
                current_property = line
            else:
                # Continue previous property
                current_property += " " + line
        
        # Process the last property
        if current_property:
            self._process_property_line(current_property, properties)
                
        return properties
    
    def _process_property_line(self, line: str, properties: Dict[str, Any]):
        """Process a single property line"""
        parts = re.split(r'\s+', line.strip(), 1)
        if len(parts) < 2:
            return
            
        property_name = parts[0]
        values_str = parts[1]
        
        # Handle multiple values (comma separated)
        values = []
        if ',' in values_str:
            value_parts = [v.strip() for v in values_str.split(',')]
            for part in value_parts:
                clean_part = part.rstrip('.,').strip()
                if clean_part:
                    values.append(self.extract_literal_value(clean_part))
        else:
            clean_value = values_str.rstrip('.,').strip()
            if clean_value:
                values.append(self.extract_literal_value(clean_value))
        
        # Store property values
        short_prop = property_name.split(':')[-1] if ':' in property_name else property_name
        
        if len(values) == 1:
            properties[short_prop] = values[0]
        elif len(values) > 1:
            properties[short_prop] = values
    
    def parse_actions(self, content: str) -> None:
        """Parse action instances from TTL content"""
        action_pattern = r'(instances:\w+_action_\d+)\s+a\s+rules:Action'
        matches = re.findall(action_pattern, content)
        
        for action_id in matches:
            properties = self.parse_property_values(content, action_id)
            
            # Handle step arrays
            data_steps = properties.get('dataSpecificStep', [])
            if isinstance(data_steps, str):
                data_steps = [data_steps]
            elif data_steps is None:
                data_steps = []
                
            user_steps = properties.get('userDataStep', [])
            if isinstance(user_steps, str):
                user_steps = [user_steps]
            elif user_steps is None:
                user_steps = []
            
            action = Action(
                id=action_id,
                action_category=properties.get('actionCategory', 'both'),
                action_type=properties.get('actionType', 'unknown'),
                title=properties.get('title', ''),
                description=properties.get('description', ''),
                confidence_score=float(properties.get('confidenceScore', 0.0)),
                responsible_role=properties.get('responsibleRole'),
                legislative_requirement=properties.get('legislativeRequirement'),
                timeline=properties.get('timeline'),
                data_specific_steps=data_steps,
                user_data_steps=user_steps
            )
            
            self.actions[action_id] = action
    
    def parse_conditions(self, content: str) -> None:
        """Parse condition instances from TTL content"""
        condition_pattern = r'(instances:\w+_condition_\w+_\d+)\s+a\s+rules:Condition'
        matches = re.findall(condition_pattern, content)
        
        for condition_id in matches:
            properties = self.parse_property_values(content, condition_id)
            
            condition = Condition(
                fact=properties.get('fact', ''),
                operator=properties.get('operator', 'equal'),
                value=str(properties.get('value', '')),
                description=properties.get('description')
            )
            
            self.conditions[condition_id] = condition
    
    def parse_condition_logic(self, content: str) -> None:
        """Parse condition logic instances from TTL content"""
        logic_pattern = r'(instances:\w+_logic_\w+)\s+a\s+rules:ConditionLogic'
        matches = re.findall(logic_pattern, content)
        
        for logic_id in matches:
            properties = self.parse_property_values(content, logic_id)
            
            # Find associated conditions
            condition_refs = []
            if 'hasCondition' in properties:
                refs = properties['hasCondition']
                if isinstance(refs, list):
                    condition_refs = refs
                else:
                    condition_refs = [refs]
            
            conditions = []
            for ref in condition_refs:
                if ref in self.conditions:
                    conditions.append(self.conditions[ref])
            
            logic = ConditionLogic(
                logic_type=properties.get('logicType', 'all'),
                conditions=conditions
            )
            
            self.condition_logic[logic_id] = logic
    
    def parse_rules(self, content: str) -> None:
        """Parse legislation rule instances from TTL content"""
        rule_pattern = r'(instances:\w+_rule_\d+)\s+a\s+rules:LegislationRule'
        matches = re.findall(rule_pattern, content)
        
        for rule_id in matches:
            properties = self.parse_property_values(content, rule_id)
            
            # Find associated actions
            action_refs = []
            if 'hasAction' in properties:
                refs = properties['hasAction']
                if isinstance(refs, list):
                    action_refs = refs
                else:
                    action_refs = [refs]
            
            rule_actions = []
            for ref in action_refs:
                if ref in self.actions:
                    rule_actions.append(self.actions[ref])
            
            # Find associated condition logic
            condition_logic = None
            if 'hasConditionLogic' in properties:
                logic_ref = properties['hasConditionLogic']
                if logic_ref in self.condition_logic:
                    condition_logic = self.condition_logic[logic_ref]
            
            # Handle list properties with better type checking
            def ensure_list(value):
                if value is None:
                    return []
                elif isinstance(value, list):
                    return value
                else:
                    return [value]
            
            data_categories = ensure_list(properties.get('dataCategory'))
            processing_purposes = ensure_list(properties.get('processingPurpose', properties.get('purpose')))
            applicable_countries = ensure_list(properties.get('applicableCountry'))
            adequacy_countries = ensure_list(properties.get('adequacyCountry'))
            tags = ensure_list(properties.get('tags'))
            legal_basis = ensure_list(properties.get('legalBasis'))
            
            # Infer processing purposes if not explicitly provided
            if not processing_purposes:
                # Try to infer from other properties
                if 'transfer' in rule_id.lower() or 'cross' in properties.get('description', '').lower():
                    processing_purposes = ['transfer']
                elif 'marketing' in properties.get('description', '').lower():
                    processing_purposes = ['marketing']
                elif 'analytics' in properties.get('description', '').lower():
                    processing_purposes = ['analytics']
                else:
                    processing_purposes = ['general_processing']
            
            rule = LegislationRule(
                id=rule_id,
                title=properties.get('title', properties.get('label', '')),
                description=properties.get('description', ''),
                source_article=properties.get('sourceArticle', ''),
                source_file=properties.get('sourceFile', ''),
                confidence_score=float(properties.get('confidenceScore', 0.0)),
                primary_impacted_role=properties.get('primaryImpactedRole', 'unknown'),
                data_categories=data_categories,
                processing_purposes=processing_purposes,
                applicable_countries=applicable_countries,
                adequacy_countries=adequacy_countries,
                extracted_at=properties.get('extractedAt', ''),
                extraction_method=properties.get('extractionMethod', ''),
                actions=rule_actions,
                condition_logic=condition_logic,
                tags=tags if tags else ['legislation'],
                legal_basis=legal_basis,
                risk_level=properties.get('riskLevel', 'medium')
            )
            
            self.rules.append(rule)
    
    def parse(self, ttl_content: str) -> List[LegislationRule]:
        """Main parsing method"""
        # Clean content
        content = re.sub(r'#.*$', '', ttl_content, flags=re.MULTILINE)
        
        # Parse components in order
        self.parse_prefixes(ttl_content)
        self.parse_conditions(content)
        self.parse_condition_logic(content)
        self.parse_actions(content)
        self.parse_rules(content)
        
        return self.rules


class JSONConverter:
    @staticmethod
    def convert_to_opa_input(rules: List[LegislationRule], query: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Convert parsed rules to OPA input format optimized for querying"""
        
        # Convert rules to dictionaries
        rules_dict = []
        for rule in rules:
            rule_dict = asdict(rule)
            
            # Convert nested objects
            if rule_dict['condition_logic']:
                rule_dict['condition_logic'] = asdict(rule.condition_logic)
                rule_dict['condition_logic']['conditions'] = [
                    asdict(cond) for cond in rule.condition_logic.conditions
                ]
            
            rule_dict['actions'] = [asdict(action) for action in rule.actions]
            
            rules_dict.append(rule_dict)
        
        opa_input = {
            'rules': rules_dict,
            'metadata': {
                'total_rules': len(rules_dict),
                'conversion_timestamp': datetime.now().isoformat(),
                'format_version': '2.0',
                'query_optimized': True
            }
        }
        
        # Add query parameters if provided
        if query:
            opa_input['query'] = query
            
        # Add context if provided
        if context:
            opa_input['context'] = context
        
        return opa_input
    
    @staticmethod
    def create_query_examples() -> Dict[str, Dict[str, Any]]:
        """Create example queries for different use cases"""
        return {
            'by_country': {
                'country': 'EU'
            },
            'by_data_category': {
                'data_category': 'personal_data'
            },
            'by_purpose': {
                'purpose': 'transfer'
            },
            'by_action_category': {
                'action_category': 'organizational'
            },
            'by_action_type': {
                'action_type': 'implement_adequacy_safeguards'
            },
            'combined_country_and_data': {
                'country': 'EU',
                'data_category': 'personal_data'
            },
            'combined_purpose_and_action': {
                'purpose': 'marketing',
                'action_category': 'individual'
            },
            'multi_criteria': {
                'country': 'EU',
                'data_category': 'personal_data',
                'purpose': 'transfer',
                'action_category': 'organizational'
            }
        }


def main():
    parser = argparse.ArgumentParser(description='Convert TTL legislation rules to JSON for OPA querying')
    parser.add_argument('input_file', help='Input TTL file path')
    parser.add_argument('output_file', help='Output JSON file path')
    parser.add_argument('--query-file', help='Optional query JSON file')
    parser.add_argument('--context-file', help='Optional context JSON file')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    parser.add_argument('--generate-examples', action='store_true', help='Generate example query files')
    
    args = parser.parse_args()
    
    try:
        # Read TTL content
        with open(args.input_file, 'r', encoding='utf-8') as f:
            ttl_content = f.read()
        
        # Parse TTL
        ttl_parser = TTLParser()
        rules = ttl_parser.parse(ttl_content)
        
        # Load query if provided
        query = None
        if args.query_file:
            with open(args.query_file, 'r', encoding='utf-8') as f:
                query = json.load(f)
        
        # Load context if provided
        context = None
        if args.context_file:
            with open(args.context_file, 'r', encoding='utf-8') as f:
                context = json.load(f)
        
        # Convert to JSON
        converter = JSONConverter()
        opa_input = converter.convert_to_opa_input(rules, query, context)
        
        # Write output
        with open(args.output_file, 'w', encoding='utf-8') as f:
            if args.pretty:
                json.dump(opa_input, f, indent=2, ensure_ascii=False)
            else:
                json.dump(opa_input, f, ensure_ascii=False)
        
        print(f"Successfully converted {len(rules)} rules from {args.input_file} to {args.output_file}")
        
        # Generate example files if requested
        if args.generate_examples:
            examples = converter.create_query_examples()
            for name, example_query in examples.items():
                example_file = f"example_query_{name}.json"
                with open(example_file, 'w', encoding='utf-8') as f:
                    json.dump(example_query, f, indent=2, ensure_ascii=False)
                print(f"Generated example: {example_file}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()