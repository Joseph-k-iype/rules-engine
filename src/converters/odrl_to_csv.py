"""
ODRL JSON to CSV Converter
Converts output.json from ODRL format to various CSV formats for analysis.

Usage:
    python odrl_json_to_csv.py output.json --format wide
    python odrl_json_to_csv.py output.json --format long
    python odrl_json_to_csv.py output.json --format multi
    python odrl_json_to_csv.py output.json --format all
"""
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class ODRLToCSVConverter:
    """Convert ODRL JSON policies to CSV formats."""
    
    def __init__(self, json_filepath: str):
        """Initialize converter with JSON file."""
        self.json_filepath = Path(json_filepath)
        with open(self.json_filepath, 'r', encoding='utf-8') as f:
            self.policies = json.load(f)
        
        print(f"✅ Loaded {len(self.policies)} policies from {json_filepath}")
    
    def convert_to_wide_csv(self, output_path: str = None):
        """
        Convert to WIDE format: One row per policy.
        Permissions/prohibitions are concatenated in columns.
        """
        if output_path is None:
            output_path = self.json_filepath.stem + "_wide.csv"
        
        rows = []
        
        for policy in self.policies:
            row = {
                # Core identifiers
                'policy_uid': policy.get('uid', ''),
                'policy_id': policy.get('dc:identifier', ''),
                'policy_title': policy.get('dc:title', ''),
                'policy_description': policy.get('dc:description', ''),
                'profile': policy.get('profile', ''),
                'created': policy.get('dc:created', ''),
                
                # Data categories and scope
                'data_categories': '; '.join(policy.get('dc:subject', [])),
                'geographic_coverage': '; '.join(policy.get('dc:coverage', [])),
                'purpose': policy.get('dc:purpose', ''),
                
                # Custom metadata
                'framework': policy.get('custom:framework', ''),
                'rule_type': policy.get('custom:type', ''),
                'confidence_score': policy.get('custom:confidenceScore', ''),
                
                # Count of rules
                'num_permissions': len(policy.get('permission', [])),
                'num_prohibitions': len(policy.get('prohibition', [])),
            }
            
            # Flatten permissions
            permissions = policy.get('permission', [])
            if permissions:
                row['permission_actions'] = '; '.join([
                    self._extract_action_name(p.get('action', '')) 
                    for p in permissions
                ])
                row['permission_targets'] = '; '.join([
                    p.get('target', '') for p in permissions if p.get('target')
                ])
                row['permission_constraints'] = '; '.join([
                    self._format_constraint(c) 
                    for p in permissions 
                    for c in p.get('constraint', [])
                ])
                row['permission_comments'] = '; '.join([
                    p.get('rdfs:comment', '') for p in permissions if p.get('rdfs:comment')
                ])
            else:
                row['permission_actions'] = ''
                row['permission_targets'] = ''
                row['permission_constraints'] = ''
                row['permission_comments'] = ''
            
            # Flatten prohibitions
            prohibitions = policy.get('prohibition', [])
            if prohibitions:
                row['prohibition_actions'] = '; '.join([
                    self._extract_action_name(p.get('action', '')) 
                    for p in prohibitions
                ])
                row['prohibition_targets'] = '; '.join([
                    p.get('target', '') for p in prohibitions if p.get('target')
                ])
                row['prohibition_constraints'] = '; '.join([
                    self._format_constraint(c) 
                    for p in prohibitions 
                    for c in p.get('constraint', [])
                ])
                row['prohibition_comments'] = '; '.join([
                    p.get('rdfs:comment', '') for p in prohibitions if p.get('rdfs:comment')
                ])
            else:
                row['prohibition_actions'] = ''
                row['prohibition_targets'] = ''
                row['prohibition_constraints'] = ''
                row['prohibition_comments'] = ''
            
            # Original data
            original = policy.get('custom:originalData', {})
            row['original_id'] = original.get('id', '')
            row['original_rule_name'] = original.get('rule_name', '')
            row['original_guidance_preview'] = original.get('guidance_preview', '')
            
            rows.append(row)
        
        # Write to CSV
        if rows:
            fieldnames = rows[0].keys()
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"✅ Wide format CSV saved to: {output_path}")
            print(f"   Rows: {len(rows)}, Columns: {len(fieldnames)}")
        
        return output_path
    
    def convert_to_long_csv(self, output_path: str = None):
        """
        Convert to LONG format: One row per permission or prohibition.
        Multiple rows per policy if it has multiple rules.
        """
        if output_path is None:
            output_path = self.json_filepath.stem + "_long.csv"
        
        rows = []
        
        for policy in self.policies:
            # Common policy data
            base_data = {
                'policy_uid': policy.get('uid', ''),
                'policy_id': policy.get('dc:identifier', ''),
                'policy_title': policy.get('dc:title', ''),
                'policy_description': policy.get('dc:description', ''),
                'profile': policy.get('profile', ''),
                'created': policy.get('dc:created', ''),
                'data_categories': '; '.join(policy.get('dc:subject', [])),
                'geographic_coverage': '; '.join(policy.get('dc:coverage', [])),
                'purpose': policy.get('dc:purpose', ''),
                'framework': policy.get('custom:framework', ''),
                'rule_type': policy.get('custom:type', ''),
                'confidence_score': policy.get('custom:confidenceScore', ''),
            }
            
            # Add row for each permission
            for i, perm in enumerate(policy.get('permission', []), 1):
                row = base_data.copy()
                row['rule_number'] = i
                row['rule_class'] = 'permission'
                row['action'] = self._extract_action_name(perm.get('action', ''))
                row['action_uri'] = perm.get('action', '')
                row['target'] = perm.get('target', '')
                row['assigner'] = self._extract_party_id(perm.get('assigner', {}))
                row['assignee'] = self._extract_party_id(perm.get('assignee', {}))
                
                # Constraints
                constraints = perm.get('constraint', [])
                row['num_constraints'] = len(constraints)
                if constraints:
                    row['constraint_summary'] = '; '.join([
                        self._format_constraint(c) for c in constraints
                    ])
                    row['constraint_details'] = json.dumps(constraints, ensure_ascii=False)
                else:
                    row['constraint_summary'] = ''
                    row['constraint_details'] = ''
                
                # Duties
                duties = perm.get('duty', [])
                row['num_duties'] = len(duties)
                if duties:
                    row['duty_summary'] = '; '.join([
                        d.get('rdfs:comment', self._extract_action_name(d.get('action', ''))) 
                        for d in duties
                    ])
                else:
                    row['duty_summary'] = ''
                
                row['comment'] = perm.get('rdfs:comment', '')
                
                rows.append(row)
            
            # Add row for each prohibition
            for i, prohib in enumerate(policy.get('prohibition', []), 1):
                row = base_data.copy()
                row['rule_number'] = i
                row['rule_class'] = 'prohibition'
                row['action'] = self._extract_action_name(prohib.get('action', ''))
                row['action_uri'] = prohib.get('action', '')
                row['target'] = prohib.get('target', '')
                row['assigner'] = self._extract_party_id(prohib.get('assigner', {}))
                row['assignee'] = self._extract_party_id(prohib.get('assignee', {}))
                
                # Constraints
                constraints = prohib.get('constraint', [])
                row['num_constraints'] = len(constraints)
                if constraints:
                    row['constraint_summary'] = '; '.join([
                        self._format_constraint(c) for c in constraints
                    ])
                    row['constraint_details'] = json.dumps(constraints, ensure_ascii=False)
                else:
                    row['constraint_summary'] = ''
                    row['constraint_details'] = ''
                
                row['num_duties'] = 0
                row['duty_summary'] = ''
                row['comment'] = prohib.get('rdfs:comment', '')
                
                rows.append(row)
            
            # If no permissions or prohibitions, add one row for the policy
            if not policy.get('permission') and not policy.get('prohibition'):
                row = base_data.copy()
                row['rule_number'] = 0
                row['rule_class'] = 'none'
                row['action'] = ''
                row['action_uri'] = ''
                row['target'] = ''
                row['assigner'] = ''
                row['assignee'] = ''
                row['num_constraints'] = 0
                row['constraint_summary'] = ''
                row['constraint_details'] = ''
                row['num_duties'] = 0
                row['duty_summary'] = ''
                row['comment'] = ''
                rows.append(row)
        
        # Write to CSV
        if rows:
            fieldnames = rows[0].keys()
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"✅ Long format CSV saved to: {output_path}")
            print(f"   Rows: {len(rows)}, Columns: {len(fieldnames)}")
        
        return output_path
    
    def convert_to_multi_csv(self, output_dir: str = None):
        """
        Convert to MULTIPLE CSVs: Separate files for different entities.
        - policies.csv: Policy metadata
        - permissions.csv: All permissions
        - prohibitions.csv: All prohibitions
        - constraints.csv: All constraints
        """
        if output_dir is None:
            output_dir = self.json_filepath.stem + "_multi"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # 1. Policies CSV
        policy_rows = []
        for policy in self.policies:
            policy_rows.append({
                'uid': policy.get('uid', ''),
                'identifier': policy.get('dc:identifier', ''),
                'title': policy.get('dc:title', ''),
                'description': policy.get('dc:description', ''),
                'profile': policy.get('profile', ''),
                'created': policy.get('dc:created', ''),
                'data_categories': '; '.join(policy.get('dc:subject', [])),
                'geographic_coverage': '; '.join(policy.get('dc:coverage', [])),
                'purpose': policy.get('dc:purpose', ''),
                'framework': policy.get('custom:framework', ''),
                'rule_type': policy.get('custom:type', ''),
                'confidence_score': policy.get('custom:confidenceScore', ''),
                'num_permissions': len(policy.get('permission', [])),
                'num_prohibitions': len(policy.get('prohibition', [])),
            })
        
        policies_path = output_dir / 'policies.csv'
        self._write_csv(policies_path, policy_rows)
        print(f"✅ Policies CSV: {policies_path} ({len(policy_rows)} rows)")
        
        # 2. Permissions CSV
        permission_rows = []
        constraint_rows = []
        constraint_id = 1
        
        for policy in self.policies:
            policy_uid = policy.get('uid', '')
            
            for i, perm in enumerate(policy.get('permission', []), 1):
                perm_id = f"{policy_uid}_perm_{i}"
                
                permission_rows.append({
                    'permission_id': perm_id,
                    'policy_uid': policy_uid,
                    'policy_title': policy.get('dc:title', ''),
                    'rule_number': i,
                    'action': self._extract_action_name(perm.get('action', '')),
                    'action_uri': perm.get('action', ''),
                    'target': perm.get('target', ''),
                    'assigner': self._extract_party_id(perm.get('assigner', {})),
                    'assignee': self._extract_party_id(perm.get('assignee', {})),
                    'num_constraints': len(perm.get('constraint', [])),
                    'num_duties': len(perm.get('duty', [])),
                    'comment': perm.get('rdfs:comment', ''),
                })
                
                # Extract constraints for this permission
                for constraint in perm.get('constraint', []):
                    constraint_rows.append({
                        'constraint_id': constraint_id,
                        'rule_id': perm_id,
                        'rule_type': 'permission',
                        'policy_uid': policy_uid,
                        'left_operand': self._extract_operand_name(constraint.get('leftOperand', '')),
                        'left_operand_uri': constraint.get('leftOperand', ''),
                        'operator': self._extract_operator_name(constraint.get('operator', '')),
                        'operator_uri': constraint.get('operator', ''),
                        'right_operand': self._format_right_operand(constraint.get('rightOperand')),
                        'comment': constraint.get('rdfs:comment', ''),
                    })
                    constraint_id += 1
        
        permissions_path = output_dir / 'permissions.csv'
        self._write_csv(permissions_path, permission_rows)
        print(f"✅ Permissions CSV: {permissions_path} ({len(permission_rows)} rows)")
        
        # 3. Prohibitions CSV
        prohibition_rows = []
        
        for policy in self.policies:
            policy_uid = policy.get('uid', '')
            
            for i, prohib in enumerate(policy.get('prohibition', []), 1):
                prohib_id = f"{policy_uid}_prohib_{i}"
                
                prohibition_rows.append({
                    'prohibition_id': prohib_id,
                    'policy_uid': policy_uid,
                    'policy_title': policy.get('dc:title', ''),
                    'rule_number': i,
                    'action': self._extract_action_name(prohib.get('action', '')),
                    'action_uri': prohib.get('action', ''),
                    'target': prohib.get('target', ''),
                    'assigner': self._extract_party_id(prohib.get('assigner', {})),
                    'assignee': self._extract_party_id(prohib.get('assignee', {})),
                    'num_constraints': len(prohib.get('constraint', [])),
                    'comment': prohib.get('rdfs:comment', ''),
                })
                
                # Extract constraints for this prohibition
                for constraint in prohib.get('constraint', []):
                    constraint_rows.append({
                        'constraint_id': constraint_id,
                        'rule_id': prohib_id,
                        'rule_type': 'prohibition',
                        'policy_uid': policy_uid,
                        'left_operand': self._extract_operand_name(constraint.get('leftOperand', '')),
                        'left_operand_uri': constraint.get('leftOperand', ''),
                        'operator': self._extract_operator_name(constraint.get('operator', '')),
                        'operator_uri': constraint.get('operator', ''),
                        'right_operand': self._format_right_operand(constraint.get('rightOperand')),
                        'comment': constraint.get('rdfs:comment', ''),
                    })
                    constraint_id += 1
        
        prohibitions_path = output_dir / 'prohibitions.csv'
        self._write_csv(prohibitions_path, prohibition_rows)
        print(f"✅ Prohibitions CSV: {prohibitions_path} ({len(prohibition_rows)} rows)")
        
        # 4. Constraints CSV
        constraints_path = output_dir / 'constraints.csv'
        self._write_csv(constraints_path, constraint_rows)
        print(f"✅ Constraints CSV: {constraints_path} ({len(constraint_rows)} rows)")
        
        print(f"\n📁 All files saved to: {output_dir}/")
        
        return str(output_dir)
    
    def _write_csv(self, filepath: Path, rows: List[Dict]):
        """Helper to write CSV file."""
        if not rows:
            return
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    def _extract_action_name(self, action_uri: str) -> str:
        """Extract action name from URI."""
        if not action_uri:
            return ''
        if '/' in action_uri:
            return action_uri.split('/')[-1]
        return action_uri
    
    def _extract_operand_name(self, operand_uri: str) -> str:
        """Extract operand name from URI."""
        if not operand_uri:
            return ''
        if '/' in operand_uri:
            return operand_uri.split('/')[-1]
        return operand_uri
    
    def _extract_operator_name(self, operator_uri: str) -> str:
        """Extract operator name from URI."""
        if not operator_uri:
            return ''
        if '/' in operator_uri:
            return operator_uri.split('/')[-1]
        return operator_uri
    
    def _extract_party_id(self, party: Dict) -> str:
        """Extract party identifier from party object."""
        if not party:
            return ''
        if isinstance(party, dict):
            return party.get('uid', '')
        return str(party)
    
    def _format_constraint(self, constraint: Dict) -> str:
        """Format constraint as readable string."""
        left = self._extract_operand_name(constraint.get('leftOperand', ''))
        op = self._extract_operator_name(constraint.get('operator', ''))
        right = self._format_right_operand(constraint.get('rightOperand'))
        
        return f"{left} {op} {right}"
    
    def _format_right_operand(self, right_operand) -> str:
        """Format right operand value."""
        if right_operand is None:
            return ''
        if isinstance(right_operand, list):
            return ', '.join(str(x) for x in right_operand)
        return str(right_operand)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Convert ODRL JSON policies to CSV format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Formats:
    wide  - One row per policy (permissions/prohibitions concatenated)
    long  - One row per permission/prohibition (multiple rows per policy)
    multi - Multiple CSV files (policies, permissions, prohibitions, constraints)
    all   - Generate all formats

Examples:
    python odrl_json_to_csv.py output.json --format wide
    python odrl_json_to_csv.py output.json --format long --output policies_expanded.csv
    python odrl_json_to_csv.py output.json --format multi --output-dir csv_files
    python odrl_json_to_csv.py output.json --format all
        """
    )
    
    parser.add_argument(
        'input_json',
        help='Input JSON file (output.json from ODRL converter)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['wide', 'long', 'multi', 'all'],
        default='wide',
        help='Output format (default: wide)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path (for wide/long) or directory (for multi)',
        default=None
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory for multi format (alternative to --output)',
        default=None
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_json).exists():
        print(f"❌ Error: Input file not found: {args.input_json}")
        return 1
    
    # Create converter
    converter = ODRLToCSVConverter(args.input_json)
    
    # Convert based on format
    print(f"\n🔄 Converting to {args.format.upper()} format...\n")
    
    try:
        if args.format == 'wide':
            converter.convert_to_wide_csv(args.output)
        
        elif args.format == 'long':
            converter.convert_to_long_csv(args.output)
        
        elif args.format == 'multi':
            output_dir = args.output_dir or args.output
            converter.convert_to_multi_csv(output_dir)
        
        elif args.format == 'all':
            print("📊 Generating all formats...\n")
            base_name = Path(args.input_json).stem
            
            print("1️⃣ WIDE FORMAT")
            converter.convert_to_wide_csv(f"{base_name}_wide.csv")
            
            print("\n2️⃣ LONG FORMAT")
            converter.convert_to_long_csv(f"{base_name}_long.csv")
            
            print("\n3️⃣ MULTI FORMAT")
            converter.convert_to_multi_csv(f"{base_name}_multi")
            
            print("\n✅ All formats generated successfully!")
        
        print("\n🎉 Conversion complete!")
        return 0
    
    except Exception as e:
        print(f"\n❌ Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())