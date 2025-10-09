#!/usr/bin/env python3
"""
cleanup_duplicates.py

Standalone script to clean up logical duplications in existing ODRL policies.
This script can be run independently to fix policies that were generated
before the validation logic was added.

Usage:
    # Clean a single file
    python cleanup_duplicates.py input.jsonld output.jsonld
    
    # Clean a single file in-place
    python cleanup_duplicates.py input.jsonld
    
    # Clean all files in a directory
    python cleanup_duplicates.py --directory path/to/policies
    
    # Dry run (check without modifying)
    python cleanup_duplicates.py --directory path/to/policies --dry-run

Author: Auto-generated for ODRL Policy System
Date: 2025
"""

import json
import sys
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CleanupStats:
    """Statistics from cleanup operations."""
    policies_processed: int = 0
    policies_modified: int = 0
    duplications_found: int = 0
    duplications_resolved: int = 0
    files_processed: int = 0
    files_modified: int = 0


class ODRLPolicyCleanup:
    """Clean up logical duplications in ODRL policies."""
    
    # Operator pairs that are logical inverses
    INVERSE_OPERATORS = {
        'eq': 'neq',
        'neq': 'eq',
        'isAnyOf': 'isNoneOf',
        'isNoneOf': 'isAnyOf',
        'isAllOf': 'isNoneOf',
        'gt': 'lteq',
        'lt': 'gteq',
        'gteq': 'lt',
        'lteq': 'gt',
        'isPartOf': 'isNotPartOf',
        'isNotPartOf': 'isPartOf'
    }
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize cleanup manager.
        
        Args:
            dry_run: If True, don't modify files, just report what would be done
        """
        self.dry_run = dry_run
        self.stats = CleanupStats()
    
    def process_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """
        Process a single JSONLD file containing ODRL policies.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file (defaults to input_path if not provided)
        
        Returns:
            True if modifications were made (or would be made in dry-run)
        """
        if output_path is None:
            output_path = input_path
        
        logger.info(f"Processing: {input_path}")
        self.stats.files_processed += 1
        
        try:
            # Read input file
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both single policy and array of policies
            if isinstance(data, list):
                policies = data
                file_format = 'array'
            elif '@graph' in data:
                policies = data['@graph']
                file_format = 'graph'
            elif '@type' in data:
                # Single policy object
                policies = [data]
                file_format = 'single'
            else:
                logger.warning(f"Unknown file format in {input_path}")
                return False
            
            # Process each policy
            file_modified = False
            for i, policy in enumerate(policies):
                if self._clean_policy(policy, i):
                    file_modified = True
                    self.stats.policies_modified += 1
                
                self.stats.policies_processed += 1
            
            # Save cleaned data if modifications were made
            if file_modified:
                self.stats.files_modified += 1
                
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would save changes to: {output_path}")
                else:
                    # Write output file
                    with open(output_path, 'w', encoding='utf-8') as f:
                        if file_format == 'array':
                            json.dump(policies, f, indent=2, ensure_ascii=False)
                        elif file_format == 'graph':
                            data['@graph'] = policies
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        else:  # single
                            json.dump(policies[0], f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"✅ Cleaned policy saved to: {output_path}")
            else:
                logger.info(f"✓ No duplications found in {input_path}")
            
            return file_modified
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {input_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error processing {input_path}: {e}")
            logger.exception("Full traceback:")
            return False
    
    def process_directory(self, directory_path: str) -> None:
        """
        Process all .jsonld and .json files in a directory.
        
        Args:
            directory_path: Path to directory containing ODRL policy files
        """
        directory = Path(directory_path)
        
        if not directory.is_dir():
            logger.error(f"Not a directory: {directory_path}")
            return
        
        # Find all JSON/JSONLD files
        jsonld_files = list(directory.glob("*.jsonld")) + list(directory.glob("*.json"))
        
        # Also check subdirectories
        jsonld_files.extend(directory.glob("**/*.jsonld"))
        jsonld_files.extend(directory.glob("**/*.json"))
        
        # Remove duplicates
        jsonld_files = list(set(jsonld_files))
        
        if not jsonld_files:
            logger.warning(f"No .jsonld or .json files found in {directory_path}")
            return
        
        logger.info(f"Found {len(jsonld_files)} file(s) to process")
        logger.info("=" * 60)
        
        # Process each file
        for file_path in sorted(jsonld_files):
            self.process_file(str(file_path))
            logger.info("-" * 60)
        
        # Print summary
        self._print_stats()
    
    def _clean_policy(self, policy: Dict, policy_index: int = 0) -> bool:
        """
        Clean a single ODRL policy by removing duplicate constraints.
        
        Args:
            policy: ODRL policy dictionary
            policy_index: Index of policy in file (for logging)
        
        Returns:
            True if policy was modified
        """
        # Check if policy has both permissions and prohibitions
        if 'permission' not in policy or 'prohibition' not in policy:
            return False
        
        permissions = policy.get('permission', [])
        prohibitions = policy.get('prohibition', [])
        
        if not permissions or not prohibitions:
            return False
        
        # Ensure they are lists
        if not isinstance(permissions, list):
            permissions = [permissions]
            policy['permission'] = permissions
        
        if not isinstance(prohibitions, list):
            prohibitions = [prohibitions]
            policy['prohibition'] = prohibitions
        
        # Find duplications
        duplications = self._find_duplications(permissions, prohibitions)
        
        if not duplications:
            return False
        
        self.stats.duplications_found += len(duplications)
        
        policy_id = policy.get('uid', f'policy_{policy_index}')
        logger.info(f"  Found {len(duplications)} duplication(s) in {policy_id}")
        
        # Log each duplication
        for dup in duplications:
            logger.debug(
                f"    - {dup['type']}: {dup['perm_constraint'].get('leftOperand')} "
                f"[perm: {dup['perm_constraint'].get('operator')}, "
                f"prohib: {dup['prohib_constraint'].get('operator')}]"
            )
        
        # Remove duplicates from prohibitions
        if self.dry_run:
            logger.info(f"  [DRY RUN] Would remove {len(duplications)} constraint(s)")
            self.stats.duplications_resolved += len(duplications)
            return True
        else:
            modified = self._remove_duplicate_constraints(prohibitions, duplications)
            
            # Remove empty prohibitions
            policy['prohibition'] = [
                p for p in prohibitions 
                if (isinstance(p, dict) and (p.get('constraint') or p.get('action')))
            ]
            
            if modified:
                self.stats.duplications_resolved += len(duplications)
                logger.info(f"  ✓ Resolved {len(duplications)} duplication(s)")
            
            return modified
    
    def _find_duplications(
        self, 
        permissions: List[Dict], 
        prohibitions: List[Dict]
    ) -> List[Dict]:
        """
        Find duplicate constraints between permissions and prohibitions.
        
        Returns:
            List of dictionaries describing each duplication
        """
        duplications = []
        
        for perm_idx, permission in enumerate(permissions):
            if not isinstance(permission, dict):
                continue
            
            perm_constraints = permission.get('constraint', [])
            if not isinstance(perm_constraints, list):
                perm_constraints = [perm_constraints] if perm_constraints else []
            
            for prohib_idx, prohibition in enumerate(prohibitions):
                if not isinstance(prohibition, dict):
                    continue
                
                prohib_constraints = prohibition.get('constraint', [])
                if not isinstance(prohib_constraints, list):
                    prohib_constraints = [prohib_constraints] if prohib_constraints else []
                
                for perm_constraint in perm_constraints:
                    if not isinstance(perm_constraint, dict):
                        continue
                    
                    for prohib_constraint in prohib_constraints:
                        if not isinstance(prohib_constraint, dict):
                            continue
                        
                        # Check for exact duplicates or logical inverses
                        is_duplicate = False
                        dup_type = None
                        
                        if self._are_identical(perm_constraint, prohib_constraint):
                            is_duplicate = True
                            dup_type = 'exact_duplicate'
                        elif self._are_logical_inverses(perm_constraint, prohib_constraint):
                            is_duplicate = True
                            dup_type = 'logical_inverse'
                        
                        if is_duplicate:
                            duplications.append({
                                'type': dup_type,
                                'permission_idx': perm_idx,
                                'prohibition_idx': prohib_idx,
                                'perm_constraint': perm_constraint,
                                'prohib_constraint': prohib_constraint
                            })
        
        return duplications
    
    def _are_identical(self, c1: Dict, c2: Dict) -> bool:
        """Check if two constraints are identical."""
        return (
            c1.get('leftOperand') == c2.get('leftOperand') and
            c1.get('operator') == c2.get('operator') and
            self._normalize_value(c1.get('rightOperand')) == 
            self._normalize_value(c2.get('rightOperand'))
        )
    
    def _are_logical_inverses(self, c1: Dict, c2: Dict) -> bool:
        """Check if two constraints are logical inverses."""
        if c1.get('leftOperand') != c2.get('leftOperand'):
            return False
        
        op1 = c1.get('operator')
        op2 = c2.get('operator')
        
        # Check if operators are inverses
        if self.INVERSE_OPERATORS.get(op1) != op2:
            return False
        
        # Check if right operands are the same
        val1 = self._normalize_value(c1.get('rightOperand'))
        val2 = self._normalize_value(c2.get('rightOperand'))
        
        return val1 == val2
    
    def _normalize_value(self, value: Any) -> str:
        """Normalize constraint values for comparison."""
        if value is None:
            return ''
        if isinstance(value, list):
            return str(sorted([str(v).lower().strip() for v in value]))
        return str(value).lower().strip()
    
    def _remove_duplicate_constraints(
        self, 
        prohibitions: List[Dict],
        duplications: List[Dict]
    ) -> bool:
        """
        Remove duplicate constraints from prohibitions.
        
        Args:
            prohibitions: List of prohibition rules (modified in place)
            duplications: List of detected duplications
            
        Returns:
            True if any constraints were removed
        """
        modified = False
        
        # Group duplications by prohibition index
        prohib_constraints_to_remove = {}
        for dup in duplications:
            prohib_idx = dup['prohibition_idx']
            if prohib_idx not in prohib_constraints_to_remove:
                prohib_constraints_to_remove[prohib_idx] = []
            prohib_constraints_to_remove[prohib_idx].append(dup['prohib_constraint'])
        
        # Remove constraints from each prohibition
        for prohib_idx, constraints_to_remove in prohib_constraints_to_remove.items():
            if prohib_idx >= len(prohibitions):
                continue
            
            prohibition = prohibitions[prohib_idx]
            if not isinstance(prohibition, dict):
                continue
            
            original_constraints = prohibition.get('constraint', [])
            if not isinstance(original_constraints, list):
                original_constraints = [original_constraints] if original_constraints else []
            
            # Filter out duplicates
            filtered_constraints = [
                c for c in original_constraints
                if not any(
                    self._are_identical(c, rem)
                    for rem in constraints_to_remove
                )
            ]
            
            if len(filtered_constraints) < len(original_constraints):
                prohibition['constraint'] = filtered_constraints
                modified = True
                removed_count = len(original_constraints) - len(filtered_constraints)
                logger.debug(f"    Removed {removed_count} constraint(s) from prohibition {prohib_idx}")
        
        return modified
    
    def _print_stats(self):
        """Print statistics about the cleanup process."""
        logger.info("\n" + "=" * 60)
        logger.info("CLEANUP SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Files processed:         {self.stats.files_processed}")
        logger.info(f"Files modified:          {self.stats.files_modified}")
        logger.info(f"Policies processed:      {self.stats.policies_processed}")
        logger.info(f"Policies modified:       {self.stats.policies_modified}")
        logger.info(f"Duplications found:      {self.stats.duplications_found}")
        logger.info(f"Duplications resolved:   {self.stats.duplications_resolved}")
        logger.info("=" * 60)
        
        if self.dry_run:
            logger.info("\n[DRY RUN MODE] No files were actually modified.")
            logger.info("Run without --dry-run to apply changes.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Clean up logical duplications in ODRL policies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean a single file in-place
  python cleanup_duplicates.py policy.jsonld
  
  # Clean with specific output
  python cleanup_duplicates.py input.jsonld output.jsonld
  
  # Clean all files in directory
  python cleanup_duplicates.py --directory ./policies/
  
  # Dry run (check without modifying)
  python cleanup_duplicates.py --directory ./policies/ --dry-run
        """
    )
    
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input JSONLD file (or use --directory for batch processing)'
    )
    parser.add_argument(
        'output_file',
        nargs='?',
        help='Output JSONLD file (optional, defaults to input file)'
    )
    parser.add_argument(
        '--directory', '-d',
        help='Process all JSONLD files in directory'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without modifying files'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create cleanup manager
    cleanup = ODRLPolicyCleanup(dry_run=args.dry_run)
    
    # Process files
    if args.directory:
        # Directory mode
        cleanup.process_directory(args.directory)
    elif args.input_file:
        # Single file mode
        if cleanup.process_file(args.input_file, args.output_file):
            logger.info("\n✅ Cleanup complete!")
        else:
            logger.info("\n✓ No changes needed")
    else:
        # No input provided
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()