"""
CSV to ODRL Converter - Main Script
Converts CSV rule framework entries to machine-readable ODRL policies.

Usage:
    python csv_to_odrl_converter.py input.csv
    python csv_to_odrl_converter.py input.csv --output output.json
    python csv_to_odrl_converter.py input.csv --framework DSS
    python csv_to_odrl_converter.py input.csv --enrich-categories

Location: csv_to_odrl_converter.py (project root)
"""
import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.processors.csv_processor import CSVProcessor, RuleFrameworkEntry
from src.analyzers.guidance_analyzer import GuidanceAnalyzer, ODRLComponents
from src.managers.data_category_manager import DataCategoryManager
from src.generators.odrl_rule_generator import ODRLRuleGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CSVToODRLConverter:
    """Main converter orchestrator."""
    
    def __init__(self):
        """Initialize all components."""
        self.csv_processor = CSVProcessor()
        self.guidance_analyzer = GuidanceAnalyzer()
        self.data_category_manager = DataCategoryManager()
        self.odrl_generator = ODRLRuleGenerator()
        
        self.statistics = {
            'total_entries': 0,
            'successful': 0,
            'failed': 0,
            'processing_time': 0.0
        }
    
    async def convert_csv_to_odrl(
        self,
        csv_filepath: str,
        output_filepath: str = None,
        filter_framework: str = None,
        enrich_categories: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Main conversion process.
        
        Args:
            csv_filepath: Path to input CSV file
            output_filepath: Path for output JSON file
            filter_framework: Filter by framework (DSS or DataVISA)
            enrich_categories: Whether to enrich data categories with LLM
            
        Returns:
            List of ODRL policies
        """
        start_time = datetime.utcnow()
        
        print("\n" + "="*80)
        print("CSV TO ODRL CONVERTER")
        print("="*80)
        print(f"Input CSV: {csv_filepath}")
        print(f"Output: {output_filepath or 'stdout'}")
        if filter_framework:
            print(f"Filter: {filter_framework}")
        print("="*80 + "\n")
        
        # Step 1: Read CSV
        print("📄 Reading CSV file...")
        try:
            entries = self.csv_processor.read_csv(csv_filepath)
            self.csv_processor.print_statistics()
        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            return []
        
        # Filter by framework if specified
        if filter_framework:
            entries = self.csv_processor.filter_by_framework(filter_framework)
            print(f"\n🔍 Filtered to {len(entries)} entries for framework: {filter_framework}")
        
        if not entries:
            print("⚠️  No entries to process!")
            return []
        
        # Step 2: Process each entry
        print(f"\n📝 Processing {len(entries)} entries...")
        print("-"*80)
        
        odrl_policies = []
        self.statistics['total_entries'] = len(entries)
        
        for i, entry in enumerate(entries, 1):
            try:
                print(f"\n[{i}/{len(entries)}] Processing: {entry.rule_name}")
                print(f"    ID: {entry.id}")
                print(f"    Framework: {entry.rule_framework}")
                print(f"    Type: {entry.restriction_condition}")
                
                # Analyze guidance
                print("    🔍 Analyzing guidance...")
                odrl_components = await self.guidance_analyzer.analyze_guidance(
                    guidance_text=entry.guidance,
                    rule_name=entry.rule_name,
                    framework_type=entry.rule_framework,
                    restriction_condition=entry.restriction_condition,
                    rule_id=entry.id
                )
                
                print(f"    ✅ Extracted {len(odrl_components.actions)} actions, "
                      f"{len(odrl_components.permissions)} permissions, "
                      f"{len(odrl_components.prohibitions)} prohibitions, "
                      f"{len(odrl_components.constraints)} constraints")
                
                # Discover and add new data categories
                if odrl_components.data_categories:
                    print(f"    📊 Processing {len(odrl_components.data_categories)} data categories...")
                    category_uuids = await self.data_category_manager.discover_and_add_categories(
                        odrl_components.data_categories
                    )
                else:
                    category_uuids = {}
                
                # Optionally enrich categories
                if enrich_categories and odrl_components.data_categories:
                    print("    🎨 Enriching data categories...")
                    for cat_name in odrl_components.data_categories[:3]:  # Limit to first 3
                        await self.data_category_manager.enrich_category_with_llm(cat_name)
                
                # Generate ODRL policy
                print("    🗂️  Generating ODRL policy...")
                policy = self.odrl_generator.generate_policy(
                    policy_id=entry.id,
                    rule_name=entry.rule_name,
                    odrl_components=odrl_components,
                    framework_type=entry.rule_framework,
                    restriction_condition=entry.restriction_condition,
                    data_category_uuids=category_uuids
                )
                
                # Validate policy
                validation = self.odrl_generator.validate_policy(policy)
                if not validation['valid']:
                    print(f"    ⚠️  Validation issues: {validation['issues']}")
                if validation['warnings']:
                    print(f"    ⚠️  Warnings: {validation['warnings']}")
                
                # Add original CSV data as metadata - NO TRUNCATION
                policy['custom:originalData'] = {
                    'id': entry.id,
                    'rule_name': entry.rule_name,
                    'framework': entry.rule_framework,
                    'type': entry.restriction_condition,
                    'guidance_text': entry.guidance  # FULL TEXT, NOT TRUNCATED
                }
                
                odrl_policies.append(policy)
                self.statistics['successful'] += 1
                print(f"    ✅ Policy generated successfully")
                
            except Exception as e:
                logger.error(f"Error processing entry {entry.id}: {e}")
                print(f"    ❌ Failed: {e}")
                self.statistics['failed'] += 1
                continue
        
        # Save data categories
        print(f"\n💾 Saving data categories...")
        self.data_category_manager.save_categories()
        
        cat_stats = self.data_category_manager.get_statistics()
        print(f"    Total categories: {cat_stats['total_categories']}")
        print(f"    Saved to: {cat_stats['categories_file']}")
        
        # Save ODRL policies
        if output_filepath and odrl_policies:
            print(f"\n💾 Saving ODRL policies to: {output_filepath}")
            try:
                output_path = Path(output_filepath)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    json.dump(odrl_policies, f, indent=2, ensure_ascii=False)
                
                print(f"    ✅ Saved {len(odrl_policies)} policies")
            except Exception as e:
                logger.error(f"Failed to save output: {e}")
        
        # Calculate statistics
        end_time = datetime.utcnow()
        self.statistics['processing_time'] = (end_time - start_time).total_seconds()
        
        # Print summary
        self._print_summary(odrl_policies)
        
        return odrl_policies
    
    def _print_summary(self, policies: List[Dict[str, Any]]):
        """Print conversion summary."""
        print("\n" + "="*80)
        print("CONVERSION SUMMARY")
        print("="*80)
        print(f"Total Entries:      {self.statistics['total_entries']}")
        print(f"Successful:         {self.statistics['successful']}")
        print(f"Failed:             {self.statistics['failed']}")
        print(f"Processing Time:    {self.statistics['processing_time']:.2f}s")
        print()
        
        if policies:
            # Count permissions and prohibitions
            total_permissions = sum(len(p.get('permission', [])) for p in policies)
            total_prohibitions = sum(len(p.get('prohibition', [])) for p in policies)
            
            print(f"Total Permissions:  {total_permissions}")
            print(f"Total Prohibitions: {total_prohibitions}")
            print()
            
            # Framework breakdown
            frameworks = {}
            for policy in policies:
                fw = policy.get('custom:framework', 'Unknown')
                frameworks[fw] = frameworks.get(fw, 0) + 1
            
            print("By Framework:")
            for fw, count in frameworks.items():
                print(f"  {fw}: {count}")
            print()
            
            # Type breakdown
            types = {}
            for policy in policies:
                t = policy.get('custom:type', 'Unknown')
                types[t] = types.get(t, 0) + 1
            
            print("By Type:")
            for t, count in types.items():
                print(f"  {t}: {count}")
        
        print("="*80)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert CSV rule framework entries to ODRL policies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python csv_to_odrl_converter.py rules.csv
    python csv_to_odrl_converter.py rules.csv --output odrl_policies.json
    python csv_to_odrl_converter.py rules.csv --framework DSS
    python csv_to_odrl_converter.py rules.csv --enrich-categories

CSV Format:
    Required columns:
    - id: Unique identifier
    - rule_framework: DSS or DataVISA
    - restriction_condition: restriction or condition
    - rule_name: Title of the rule
    - guidance: Complete guidance text with details, actions, evidence

Output:
    JSON file containing ODRL 2.2 compliant policies
    Data categories saved to: config/data_categories.json
        """
    )
    
    parser.add_argument(
        'input_csv',
        help='Input CSV file path'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output JSON file path (default: stdout)',
        default=None
    )
    parser.add_argument(
        '--framework', '-f',
        choices=['DSS', 'DataVISA', 'dss', 'datavisa'],
        help='Filter by framework type',
        default=None
    )
    parser.add_argument(
        '--enrich-categories',
        action='store_true',
        help='Use LLM to enrich data categories (slower but more detailed)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input file
    if not Path(args.input_csv).exists():
        print(f"❌ Error: Input file not found: {args.input_csv}")
        sys.exit(1)
    
    # Create converter and run
    converter = CSVToODRLConverter()
    
    try:
        policies = await converter.convert_csv_to_odrl(
            csv_filepath=args.input_csv,
            output_filepath=args.output,
            filter_framework=args.framework.upper() if args.framework else None,
            enrich_categories=args.enrich_categories
        )
        
        # If no output file specified, print to stdout
        if not args.output and policies:
            print("\n" + "="*80)
            print("ODRL POLICIES (JSON)")
            print("="*80)
            print(json.dumps(policies, indent=2, ensure_ascii=False))
        
        print("\n✅ Conversion complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Conversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Conversion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())