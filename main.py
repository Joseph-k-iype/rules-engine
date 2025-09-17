"""
Main execution script for the legislation rules converter.
"""
import asyncio
import logging
import os
from datetime import datetime

from src.analyzer import LegislationAnalyzer
from src.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main execution function with enhanced processing and improved output display."""

    analyzer = LegislationAnalyzer()

    try:
        print("\n=== ADVANCED LEGISLATION RULES CONVERTER WITH COMPREHENSIVE DOCUMENT ANALYSIS ===")
        print("Processing legislation with dynamic chunking, dual action inference (rule + user), comprehensive document analysis, and anti-hallucination measures...\n")

        # Show metadata configuration
        print("📋 METADATA CONFIGURATION:")
        processing_entries = analyzer.metadata_manager.get_all_processing_entries()
        if processing_entries:
            print(f"✅ Configured entries: {len(processing_entries)}")
            for entry_id, metadata in processing_entries:
                print(f"   📂 {entry_id}:")
                print(f"      🌍 Countries: {', '.join(metadata.country)}")
                if metadata.adequacy_country:
                    print(f"      🤝 Adequacy: {', '.join(metadata.adequacy_country)}")
                if metadata.file_level_1:
                    print(f"      📄 Level 1: {metadata.file_level_1}")
                if metadata.file_level_2:
                    print(f"      📖 Level 2: {metadata.file_level_2}")
                if metadata.file_level_3:
                    print(f"      📘 Level 3: {metadata.file_level_3}")
                print()
        else:
            print("⚠️ No configured entries found in legislation_metadata.json")
            print("Please create config/legislation_metadata.json with your configuration")
            return

        print(f"📁 Config file: {Config.METADATA_CONFIG_FILE}")
        print(f"🔧 Chunk size: {Config.CHUNK_SIZE} chars, Overlap: {Config.OVERLAP_SIZE} chars")
        print(f"📏 Chunking threshold: {Config.MAX_FILE_SIZE / (1024*1024):.1f} MB")
        print()

        # Check PDF processing availability
        try:
            from src.processors.pdf_processor import PDF_AVAILABLE
            if not PDF_AVAILABLE:
                print("⚠️ Warning: PDF processing libraries not available.")
                print("Install with: pip install PyMuPDF pdfplumber")
                return
        except ImportError:
            print("⚠️ Warning: PDF processor not available.")
            return

        # Process configured entries
        print("🔍 Processing configured legislation entries...")
        print("ℹ️ Note: Processing will run regardless of existing rules (no skipping)")
        os.makedirs(Config.LEGISLATION_PDF_PATH, exist_ok=True)

        result = await analyzer.process_legislation_folder()

        # Print results
        print(f"\n=== PROCESSING RESULTS ===")
        print(f"📊 Summary: {result.summary}")
        print(f"📈 Total Rules: {result.total_rules}")
        print(f"🎯 Total Rule Actions: {result.total_actions}")
        print(f"👤 Total User Actions: {result.total_user_actions}")
        print(f"⏱️ Processing Time: {result.processing_time:.2f} seconds")
        print(f"🔗 Integrated Rules: {len(result.integrated_rules)}")
        print(f"📚 Documents Processed: {result.documents_processed}")

        if result.chunking_metadata:
            print(f"🧩 Chunking Applied:")
            for doc_id, chunk_info in result.chunking_metadata.items():
                print(f"   {doc_id}: {chunk_info['chunks']} chunks")

        if result.rules:
            print(f"\n=== EXTRACTED RULES WITH DUAL ACTIONS ===")
            for i, rule in enumerate(result.rules, 1):
                print(f"\n🔍 Rule {i}: {rule.name}")
                print(f"   📝 Description: {rule.description}")
                print(f"   📄 Source: {rule.source_article}")

                # Display roles and data categories properly
                primary_role_display = "not_specified"
                if rule.primary_impacted_role:
                    primary_role_display = rule.primary_impacted_role.value if hasattr(rule.primary_impacted_role, 'value') else str(rule.primary_impacted_role)
                print(f"   🎯 Primary Role: {primary_role_display}")

                secondary_role_display = "not_specified"
                if rule.secondary_impacted_role:
                    secondary_role_display = rule.secondary_impacted_role.value if hasattr(rule.secondary_impacted_role, 'value') else str(rule.secondary_impacted_role)
                    print(f"   🎯 Secondary Role: {secondary_role_display}")

                data_categories_display = []
                if rule.data_category:
                    data_categories_display = [cat.value if hasattr(cat, 'value') else str(cat) for cat in rule.data_category]
                print(f"   📊 Data Categories: {', '.join(data_categories_display) if data_categories_display else 'not_specified'}")

                print(f"   🌍 Countries: {', '.join(rule.applicable_countries) if rule.applicable_countries else 'Not specified'}")
                print(f"   ⭐ Confidence: {rule.confidence_score}")

                # Show processing metadata including chunking
                if rule.processing_metadata:
                    if rule.processing_metadata.get("chunk_reference"):
                        print(f"   🧩 Chunk: {rule.processing_metadata['chunk_reference']}")

                print(f"   📋 Conditions:")
                for logic_type, conditions in rule.conditions.items():
                    print(f"      {logic_type.upper()}:")
                    for condition in conditions:
                        print(f"        - {condition.description}")

                        operator_display = condition.operator.value if hasattr(condition.operator, 'value') else str(condition.operator)
                        role_display = "not_specified"
                        if condition.role:
                            role_display = condition.role.value if hasattr(condition.role, 'value') else str(condition.role)

                        domain_displays = []
                        if condition.data_domain:
                            domain_displays = [d.value if hasattr(d, 'value') else str(d) for d in condition.data_domain]

                        level_display = condition.document_level.value if hasattr(condition.document_level, 'value') else str(condition.document_level)

                        print(f"          Fact: {condition.fact} | Operator: {operator_display} | Value: {condition.value}")
                        print(f"          Role: {role_display} | Domains: {', '.join(domain_displays) if domain_displays else 'not_specified'}")
                        print(f"          Level: {level_display}")
                        if condition.chunk_reference:
                            print(f"          Chunk: {condition.chunk_reference}")

                # Show RULE ACTIONS (Organizational)
                if rule.actions:
                    print(f"   🏢 RULE ACTIONS - Organizational ({len(rule.actions)}):")
                    for action in rule.actions:
                        print(f"      🔧 {action.title} ({action.action_type})")
                        print(f"         Priority: {action.priority}")
                        print(f"         Description: {action.description}")
                        print(f"         Legislative Requirement: {action.legislative_requirement}")
                        print(f"         Data Impact: {action.data_impact}")
                        print(f"         Data-Specific Steps: {', '.join(action.data_specific_steps)}")
                        if action.responsible_role:
                            print(f"         Responsible: {action.responsible_role}")
                        if action.timeline:
                            print(f"         Timeline: {action.timeline}")
                        print(f"         Verification: {', '.join(action.verification_method)}")
                        print(f"         Derived From: {action.derived_from_text[:100]}...")
                        print(f"         Confidence: {action.confidence_score}")
                        print()
                else:
                    print(f"   🏢 RULE ACTIONS - Organizational: None inferred")

                # Show USER ACTIONS (Individual)
                if rule.user_actions:
                    print(f"   👤 USER ACTIONS - Individual ({len(rule.user_actions)}):")
                    for action in rule.user_actions:
                        print(f"      🔧 {action.title} ({action.action_type})")
                        print(f"         Priority: {action.priority}")
                        print(f"         Description: {action.description}")
                        print(f"         Legislative Requirement: {action.legislative_requirement}")
                        print(f"         Compliance Outcome: {action.compliance_outcome}")
                        print(f"         User Data Steps: {', '.join(action.user_data_steps)}")
                        if action.affected_data_categories:
                            print(f"         Affected Data: {', '.join(action.affected_data_categories)}")
                        if action.user_role_context:
                            print(f"         User Role: {action.user_role_context}")
                        if action.timeline:
                            print(f"         Timeline: {action.timeline}")
                        print(f"         User Verification: {', '.join(action.user_verification_steps)}")
                        print(f"         Derived From: {action.derived_from_text[:100]}...")
                        print(f"         Confidence: {action.confidence_score}")
                        print()
                else:
                    print(f"   👤 USER ACTIONS - Individual: None inferred")

                # Show integrated alignment
                if i <= len(result.integrated_rules):
                    integrated_rule = result.integrated_rules[i-1]
                    print(f"   🔗 Integrated Standards:")
                    print(f"      DPV Processing: {[p.split('#')[-1] for p in integrated_rule.dpv_hasProcessing] if integrated_rule.dpv_hasProcessing else 'none'}")
                    print(f"      DPV Purposes: {[p.split('#')[-1] for p in integrated_rule.dpv_hasPurpose] if integrated_rule.dpv_hasPurpose else 'none'}")
                    print(f"      DPV Data Types: {[d.split('#')[-1] for d in integrated_rule.dpv_hasPersonalData] if integrated_rule.dpv_hasPersonalData else 'none'}")
                    print(f"      DPV Rule Actions: {[a.split('#')[-1] for a in integrated_rule.dpv_hasRuleAction] if integrated_rule.dpv_hasRuleAction else 'none'}")
                    print(f"      DPV User Actions: {[a.split('#')[-1] for a in integrated_rule.dpv_hasUserAction] if integrated_rule.dpv_hasUserAction else 'none'}")
                    print(f"      ODRE Dual Action Inference: Rule={integrated_rule.odre_action_inference}, User={integrated_rule.odre_user_action_inference}")
                    if integrated_rule.chunk_references:
                        print(f"      Chunk References: {integrated_rule.chunk_references}")

                print("-" * 80)

        # Save results in multiple formats
        if result.rules:
            print(f"\n=== SAVING RESULTS ===")

            # Ensure output directories exist
            os.makedirs(Config.RULES_OUTPUT_PATH, exist_ok=True)
            os.makedirs(Config.STANDARDS_OUTPUT_PATH, exist_ok=True)

            # Generate timestamp for unique filenames
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

            print("Enhanced formats with dual actions:")

            # Save JSON format with dual actions
            json_file = os.path.join(Config.RULES_OUTPUT_PATH, f"rules_with_dual_actions_{timestamp}.json")
            result.save_json(json_file)
            print(f"   JSON Rules with Dual Actions: {json_file}")

            # Save single comprehensive CSV format
            csv_file = os.path.join(Config.RULES_OUTPUT_PATH, f"rules_with_dual_actions_{timestamp}.csv")
            result.save_csv(csv_file)
            print(f"   CSV Rules with Dual Actions: {csv_file}")

            print("\nIntegrated Standards Formats:")

            # Save integrated formats
            if result.integrated_rules:
                integrated_ttl_file = os.path.join(Config.STANDARDS_OUTPUT_PATH, f"integrated_standards_{timestamp}.ttl")
                result.save_integrated_ttl(integrated_ttl_file)
                print(f"   Integrated TTL: {integrated_ttl_file}")

                integrated_jsonld_file = os.path.join(Config.STANDARDS_OUTPUT_PATH, f"integrated_standards_{timestamp}.jsonld")
                result.save_integrated_jsonld(integrated_jsonld_file)
                print(f"   Integrated JSON-LD: {integrated_jsonld_file}")

                integrated_json_file = os.path.join(Config.STANDARDS_OUTPUT_PATH, f"integrated_rules_{timestamp}.json")
                result.save_integrated_json(integrated_json_file)
                print(f"   Integrated JSON: {integrated_json_file}")

            print(f"\nStandards Integration Summary:")
            print(f"   DPV v2.1: Processing activities with dynamic action mappings")
            print(f"   ODRL: Policy expressions with data-specific constraints") 
            print(f"   ODRE: Enforcement framework with dual action inference capability")
            print(f"   Multi-Level Processing: Legislation + guidance docs integration")
            print(f"   Dynamic Chunking: Large document processing support")
            print(f"   Comprehensive Analysis: Whole document understanding")
            print(f"   Anti-Hallucination: Focused analysis with verification")

            # Show dual action statistics
            if result.total_actions > 0 or result.total_user_actions > 0:
                rule_action_types = {}
                user_action_types = {}
                priorities = {}

                for rule in result.rules:
                    # Rule action statistics
                    for action in rule.actions:
                        rule_action_types[action.action_type] = rule_action_types.get(action.action_type, 0) + 1
                        priorities[action.priority] = priorities.get(action.priority, 0) + 1

                    # User action statistics
                    for action in rule.user_actions:
                        user_action_types[action.action_type] = user_action_types.get(action.action_type, 0) + 1
                        priorities[action.priority] = priorities.get(action.priority, 0) + 1

                print(f"\n🎯 DUAL ACTION INFERENCE STATISTICS:")
                print(f"   Total Rule Actions (Organizational): {result.total_actions}")
                print(f"   Total User Actions (Individual): {result.total_user_actions}")
                print(f"   Unique Rule Action Types: {len(rule_action_types)}")
                print(f"   Unique User Action Types: {len(user_action_types)}")
                if rule_action_types:
                    print(f"   Most Common Rule Types: {dict(sorted(rule_action_types.items(), key=lambda x: x[1], reverse=True)[:3])}")
                if user_action_types:
                    print(f"   Most Common User Types: {dict(sorted(user_action_types.items(), key=lambda x: x[1], reverse=True)[:3])}")
                print(f"   Priority Distribution: {dict(priorities)}")

                # Calculate average confidence for both action types
                if result.total_actions > 0:
                    total_rule_confidence = sum(action.confidence_score for rule in result.rules for action in rule.actions)
                    avg_rule_confidence = total_rule_confidence / result.total_actions
                    print(f"   Average Rule Action Confidence: {avg_rule_confidence:.2f}")

                if result.total_user_actions > 0:
                    total_user_confidence = sum(action.confidence_score for rule in result.rules for action in rule.user_actions)
                    avg_user_confidence = total_user_confidence / result.total_user_actions
                    print(f"   Average User Action Confidence: {avg_user_confidence:.2f}")

            # Show database status
            total_existing = len(analyzer.rule_manager.existing_rules)
            existing_rule_actions = sum(len(rule.actions) for rule in analyzer.rule_manager.existing_rules)
            existing_user_actions = sum(len(rule.user_actions) for rule in analyzer.rule_manager.existing_rules)
            print(f"\n=== RULE DATABASE STATUS ===")
            print(f"Total rules in database: {total_existing}")
            print(f"Total rule actions in database: {existing_rule_actions}")
            print(f"Total user actions in database: {existing_user_actions}")
            print(f"New rules added: {len(result.rules)}")
            print(f"New rule actions added: {result.total_actions}")
            print(f"New user actions added: {result.total_user_actions}")
            print(f"Database file: {Config.EXISTING_RULES_FILE}")

        else:
            print("\nNo rules were extracted.")

        print(f"\nAdvanced processing with comprehensive document analysis and dual action inference complete!")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    # Run the enhanced main function
    asyncio.run(main())