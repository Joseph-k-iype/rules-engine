"""
Main execution script for the legislation rules converter with decision-making capabilities.
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
    """Main execution function with enhanced processing and decision-making display."""

    analyzer = LegislationAnalyzer()

    try:
        print("\n=== ADVANCED LEGISLATION RULES CONVERTER WITH DECISION-MAKING CAPABILITIES ===")
        print("Processing legislation with dynamic chunking, triple action inference (rule + user + decision-enabling), comprehensive document analysis, decision inference, and anti-hallucination measures...\n")

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

        print(f"📄 Config file: {Config.METADATA_CONFIG_FILE}")
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
        print("📊 Processing configured legislation entries...")
        print("ℹ️ Note: Processing will run regardless of existing rules (no skipping)")
        os.makedirs(Config.LEGISLATION_PDF_PATH, exist_ok=True)

        result = await analyzer.process_legislation_folder()

        # Print results
        print(f"\n=== PROCESSING RESULTS ===")
        print(f"📊 Summary: {result.summary}")
        print(f"📈 Total Rules: {result.total_rules}")
        print(f"🎯 Total Rule Actions: {result.total_actions}")
        print(f"👤 Total User Actions: {result.total_user_actions}")
        print(f"🎲 Total Decision Rules: {result.total_decision_rules}")
        print(f"⚖️ Total Decision-Enabled Rules: {result.total_decisions}")
        print(f"🔍 Decision Contexts Found: {', '.join(result.decision_contexts) if result.decision_contexts else 'None'}")
        print(f"⏱️ Processing Time: {result.processing_time:.2f} seconds")
        print(f"🔗 Integrated Rules: {len(result.integrated_rules)}")
        print(f"📚 Documents Processed: {result.documents_processed}")

        if result.chunking_metadata:
            print(f"🧩 Chunking Applied:")
            for doc_id, chunk_info in result.chunking_metadata.items():
                print(f"   {doc_id}: {chunk_info['chunks']} chunks")

        # Display decision-making statistics
        if result.total_decisions > 0:
            print(f"\n=== DECISION-MAKING STATISTICS ===")
            decision_stats = result.get_decision_statistics()
            print(f"🎯 Rules with Decision Capabilities: {decision_stats['total_decision_enabled_rules']}")
            
            if decision_stats["decision_type_breakdown"]:
                print(f"📊 Decision Type Breakdown:")
                for decision_type, count in decision_stats["decision_type_breakdown"].items():
                    if count > 0:
                        emoji = "✅" if decision_type == "yes" else "❌" if decision_type == "no" else "❓" if decision_type == "maybe" else "❔"
                        print(f"   {emoji} {decision_type.upper()}: {count} rules")
            
            if decision_stats["decision_context_breakdown"]:
                print(f"🎪 Decision Context Breakdown:")
                for context, count in decision_stats["decision_context_breakdown"].items():
                    context_emoji = {
                        "data_transfer": "📤", "data_processing": "⚙️", "data_storage": "💾",
                        "data_collection": "📥", "data_sharing": "🤝", "data_deletion": "🗑️",
                        "consent_management": "✋", "rights_exercise": "👥", "compliance_verification": "✔️"
                    }.get(context, "📋")
                    print(f"   {context_emoji} {context.replace('_', ' ').title()}: {count} rules")
            
            if decision_stats["conditional_actions_required"]:
                print(f"🔧 Most Required Actions for Conditional Decisions:")
                sorted_actions = sorted(decision_stats["conditional_actions_required"].items(), key=lambda x: x[1], reverse=True)
                for action, count in sorted_actions[:5]:  # Top 5
                    action_emoji = {
                        "data_masking": "🎭", "data_encryption": "🔐", "consent_obtainment": "✋",
                        "safeguards_implementation": "🛡️", "documentation_completion": "📝",
                        "adequacy_verification": "✅", "impact_assessment": "📋"
                    }.get(action, "⚙️")
                    print(f"   {action_emoji} {action.replace('_', ' ').title()}: {count} times")

        if result.rules:
            print(f"\n=== EXTRACTED RULES WITH DECISION-MAKING CAPABILITIES ===")
            for i, rule in enumerate(result.rules, 1):
                print(f"\n🔸 Rule {i}: {rule.name}")
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

                # Display decision capabilities
                decision_summary = rule.get_decision_summary()
                if decision_summary["has_decision_capability"]:
                    print(f"   🎲 Decision Capability: YES")
                    
                    if decision_summary["primary_decision"]:
                        pd = decision_summary["primary_decision"]
                        decision_emoji = "✅" if pd["decision"] == "yes" else "❌" if pd["decision"] == "no" else "❓" if pd["decision"] == "maybe" else "❔"
                        print(f"   {decision_emoji} Primary Decision: {pd['decision'].upper()} for {pd['context'].replace('_', ' ')}")
                        print(f"      📊 Confidence: {pd['confidence']:.2f}")
                        if pd["required_actions"]:
                            print(f"      🔧 Required Actions: {', '.join(pd['required_actions'])}")
                    
                    if decision_summary["decision_contexts"]:
                        contexts = ', '.join(decision_summary["decision_contexts"])
                        print(f"   🎪 Decision Contexts: {contexts.replace('_', ' ')}")
                    
                    if decision_summary["enabling_actions"]:
                        print(f"   ⚙️ Actions that Enable Decisions:")
                        for action in decision_summary["enabling_actions"]:
                            action_emoji = "✅" if action["enables"] == "yes" else "❌" if action["enables"] == "no" else "❓"
                            print(f"      {action_emoji} {action['action_type']} → {action['enables']} for {action['context'].replace('_', ' ')}")
                else:
                    print(f"   🎲 Decision Capability: NO")

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
                        
                        # Show decision impact of condition
                        if hasattr(condition, 'decision_impact') and condition.decision_impact:
                            decision_impact = condition.decision_impact.value if hasattr(condition.decision_impact, 'value') else str(condition.decision_impact)
                            print(f"          Decision Impact: {decision_impact}")
                        
                        if hasattr(condition, 'conditional_requirement') and condition.conditional_requirement:
                            req = condition.conditional_requirement.value if hasattr(condition.conditional_requirement, 'value') else str(condition.conditional_requirement)
                            print(f"          Conditional Requirement: {req.replace('_', ' ')}")

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
                        
                        # Show decision capabilities of action
                        if hasattr(action, 'enables_decision') and action.enables_decision:
                            decision_emoji = "✅" if action.enables_decision.decision.value == "yes" else "❓"
                            print(f"         🎯 Enables Decision: {decision_emoji} {action.enables_decision.decision.value} for {action.enables_decision.context.value.replace('_', ' ')}")
                        
                        if hasattr(action, 'required_for_decision') and action.required_for_decision:
                            print(f"         🔧 Required For: {action.required_for_decision.value} decisions")
                        
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
                        
                        # Show decision capabilities of user action
                        if hasattr(action, 'enables_decision') and action.enables_decision:
                            decision_emoji = "✅" if action.enables_decision.decision.value == "yes" else "❓"
                            print(f"         🎯 Enables Decision: {decision_emoji} {action.enables_decision.decision.value} for {action.enables_decision.context.value.replace('_', ' ')}")
                        
                        if hasattr(action, 'decision_impact') and action.decision_impact:
                            print(f"         📊 Decision Impact: {action.decision_impact}")
                        
                        print()
                else:
                    print(f"   👤 USER ACTIONS - Individual: None inferred")

                # Show DECISION RULES (Decision Framework)
                if rule.decision_rules:
                    print(f"   🎲 DECISION RULES - Decision Framework ({len(rule.decision_rules)}):")
                    for decision_rule in rule.decision_rules:
                        context_emoji = {
                            "data_transfer": "📤", "data_processing": "⚙️", "data_storage": "💾",
                            "data_collection": "📥", "data_sharing": "🤝", "data_deletion": "🗑️",
                            "consent_management": "✋", "rights_exercise": "👥", "compliance_verification": "✔️"
                        }.get(decision_rule.context.value, "📋")
                        
                        print(f"      {context_emoji} Question: {decision_rule.question}")
                        print(f"         Context: {decision_rule.context.value.replace('_', ' ').title()}")
                        
                        default_emoji = "✅" if decision_rule.default_decision.value == "yes" else "❌" if decision_rule.default_decision.value == "no" else "❓"
                        print(f"         {default_emoji} Default Decision: {decision_rule.default_decision.value.upper()}")
                        
                        if decision_rule.requirements_for_yes:
                            print(f"         ✅ Requirements for YES: {', '.join(decision_rule.requirements_for_yes)}")
                        
                        if decision_rule.requirements_for_maybe:
                            maybe_reqs = [req.value.replace('_', ' ') for req in decision_rule.requirements_for_maybe]
                            print(f"         ❓ Requirements for MAYBE: {', '.join(maybe_reqs)}")
                        
                        if decision_rule.reasons_for_no:
                            print(f"         ❌ Reasons for NO: {', '.join(decision_rule.reasons_for_no)}")
                        
                        if decision_rule.applicable_scenarios:
                            print(f"         🎪 Scenarios: {', '.join(decision_rule.applicable_scenarios)}")
                        
                        print(f"         📊 Confidence: {decision_rule.confidence_score:.2f}")
                        print()
                else:
                    print(f"   🎲 DECISION RULES - Decision Framework: None inferred")

                # Show integrated alignment
                if i <= len(result.integrated_rules):
                    integrated_rule = result.integrated_rules[i-1]
                    print(f"   🔗 Integrated Standards:")
                    print(f"      DPV Processing: {[p.split('#')[-1] for p in integrated_rule.dpv_hasProcessing] if integrated_rule.dpv_hasProcessing else 'none'}")
                    print(f"      DPV Purposes: {[p.split('#')[-1] for p in integrated_rule.dpv_hasPurpose] if integrated_rule.dpv_hasPurpose else 'none'}")
                    print(f"      DPV Data Types: {[d.split('#')[-1] for d in integrated_rule.dpv_hasPersonalData] if integrated_rule.dpv_hasPersonalData else 'none'}")
                    print(f"      DPV Rule Actions: {[a.split('#')[-1] for a in integrated_rule.dpv_hasRuleAction] if integrated_rule.dpv_hasRuleAction else 'none'}")
                    print(f"      DPV User Actions: {[a.split('#')[-1] for a in integrated_rule.dpv_hasUserAction] if integrated_rule.dpv_hasUserAction else 'none'}")
                    print(f"      DPV Decision Actions: {[a.split('#')[-1] for a in integrated_rule.dpv_hasDecisionAction] if integrated_rule.dpv_hasDecisionAction else 'none'}")
                    print(f"      ODRE Triple Action Inference: Rule={integrated_rule.odre_action_inference}, User={integrated_rule.odre_user_action_inference}, Decision={integrated_rule.odre_decision_inference}")
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

            print("Enhanced formats with decision-making capabilities:")

            # Save JSON format with decision capabilities
            json_file = os.path.join(Config.RULES_OUTPUT_PATH, f"rules_with_decisions_{timestamp}.json")
            result.save_json(json_file)
            print(f"   JSON Rules with Decision Capabilities: {json_file}")

            # Save decision summary
            decision_summary_file = os.path.join(Config.RULES_OUTPUT_PATH, f"decision_summary_{timestamp}.json")
            result.save_decision_summary(decision_summary_file)
            print(f"   Decision Summary: {decision_summary_file}")

            # Save comprehensive CSV format
            csv_file = os.path.join(Config.RULES_OUTPUT_PATH, f"rules_with_decisions_{timestamp}.csv")
            result.save_csv(csv_file)
            print(f"   CSV Rules with Decision Capabilities: {csv_file}")

            print("\nIntegrated Standards Formats:")

            # Save integrated formats
            if result.integrated_rules:
                integrated_ttl_file = os.path.join(Config.STANDARDS_OUTPUT_PATH, f"integrated_standards_with_decisions_{timestamp}.ttl")
                result.save_integrated_ttl(integrated_ttl_file)
                print(f"   Integrated TTL with Decision Framework: {integrated_ttl_file}")

                integrated_jsonld_file = os.path.join(Config.STANDARDS_OUTPUT_PATH, f"integrated_standards_with_decisions_{timestamp}.jsonld")
                result.save_integrated_jsonld(integrated_jsonld_file)
                print(f"   Integrated JSON-LD with Decision Framework: {integrated_jsonld_file}")

                integrated_json_file = os.path.join(Config.STANDARDS_OUTPUT_PATH, f"integrated_rules_with_decisions_{timestamp}.json")
                result.save_integrated_json(integrated_json_file)
                print(f"   Integrated JSON with Decision Framework: {integrated_json_file}")

            print(f"\nStandards Integration Summary with Decision-Making:")
            print(f"   DPV v2.1: Processing activities with dynamic action mappings and decision contexts")
            print(f"   ODRL: Policy expressions with data-specific constraints and decision conditions") 
            print(f"   ODRE: Enforcement framework with triple action inference and decision-based enforcement")
            print(f"   Decision Framework: YES/NO/MAYBE decision inference with conditional requirements")
            print(f"   Multi-Level Processing: Legislation + guidance docs integration")
            print(f"   Dynamic Chunking: Large document processing support")
            print(f"   Comprehensive Analysis: Whole document understanding")
            print(f"   Anti-Hallucination: Focused analysis with verification")

            # Show triple action statistics with decision information
            if result.total_actions > 0 or result.total_user_actions > 0 or result.total_decision_rules > 0:
                rule_action_types = {}
                user_action_types = {}
                decision_contexts = {}
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
                    
                    # Decision context statistics
                    if rule.decision_outcome:
                        context = rule.decision_outcome.context.value
                        decision_contexts[context] = decision_contexts.get(context, 0) + 1
                    
                    for decision_rule in rule.decision_rules:
                        context = decision_rule.context.value
                        decision_contexts[context] = decision_contexts.get(context, 0) + 1

                print(f"\n🎯 TRIPLE ACTION INFERENCE WITH DECISION-MAKING STATISTICS:")
                print(f"   Total Rule Actions (Organizational): {result.total_actions}")
                print(f"   Total User Actions (Individual): {result.total_user_actions}")
                print(f"   Total Decision Rules (Decision Framework): {result.total_decision_rules}")
                print(f"   Unique Rule Action Types: {len(rule_action_types)}")
                print(f"   Unique User Action Types: {len(user_action_types)}")
                print(f"   Unique Decision Contexts: {len(decision_contexts)}")
                
                if rule_action_types:
                    print(f"   Most Common Rule Types: {dict(sorted(rule_action_types.items(), key=lambda x: x[1], reverse=True)[:3])}")
                if user_action_types:
                    print(f"   Most Common User Types: {dict(sorted(user_action_types.items(), key=lambda x: x[1], reverse=True)[:3])}")
                if decision_contexts:
                    print(f"   Most Common Decision Contexts: {dict(sorted(decision_contexts.items(), key=lambda x: x[1], reverse=True)[:3])}")
                print(f"   Priority Distribution: {dict(priorities)}")

                # Calculate average confidence for all action types
                if result.total_actions > 0:
                    total_rule_confidence = sum(action.confidence_score for rule in result.rules for action in rule.actions)
                    avg_rule_confidence = total_rule_confidence / result.total_actions
                    print(f"   Average Rule Action Confidence: {avg_rule_confidence:.2f}")

                if result.total_user_actions > 0:
                    total_user_confidence = sum(action.confidence_score for rule in result.rules for action in rule.user_actions)
                    avg_user_confidence = total_user_confidence / result.total_user_actions
                    print(f"   Average User Action Confidence: {avg_user_confidence:.2f}")
                
                if result.total_decision_rules > 0:
                    total_decision_confidence = sum(dr.confidence_score for rule in result.rules for dr in rule.decision_rules)
                    avg_decision_confidence = total_decision_confidence / result.total_decision_rules
                    print(f"   Average Decision Rule Confidence: {avg_decision_confidence:.2f}")

            # Show database status
            total_existing = len(analyzer.rule_manager.existing_rules)
            existing_rule_actions = sum(len(rule.actions) for rule in analyzer.rule_manager.existing_rules)
            existing_user_actions = sum(len(rule.user_actions) for rule in analyzer.rule_manager.existing_rules)
            existing_decision_rules = sum(len(getattr(rule, 'decision_rules', [])) for rule in analyzer.rule_manager.existing_rules)
            
            print(f"\n=== RULE DATABASE STATUS ===")
            print(f"Total rules in database: {total_existing}")
            print(f"Total rule actions in database: {existing_rule_actions}")
            print(f"Total user actions in database: {existing_user_actions}")
            print(f"Total decision rules in database: {existing_decision_rules}")
            print(f"New rules added: {len(result.rules)}")
            print(f"New rule actions added: {result.total_actions}")
            print(f"New user actions added: {result.total_user_actions}")
            print(f"New decision rules added: {result.total_decision_rules}")
            print(f"Database file: {Config.EXISTING_RULES_FILE}")

        else:
            print("\nNo rules were extracted.")

        print(f"\nAdvanced processing with comprehensive document analysis, triple action inference, and decision-making capabilities complete!")
        
        # Show practical usage example
        if result.total_decisions > 0:
            print(f"\n=== PRACTICAL DECISION-MAKING USAGE ===")
            print("📋 Example Questions Your Rules Can Now Answer:")
            
            # Find a few example rules with decision capabilities
            decision_rules = [rule for rule in result.rules if rule.decision_outcome or rule.decision_rules]
            
            for i, rule in enumerate(decision_rules[:3], 1):  # Show first 3 examples
                print(f"\n{i}. Based on {rule.source_article}:")
                
                if rule.decision_rules:
                    for decision_rule in rule.decision_rules[:1]:  # Show first decision rule
                        print(f"   ❓ Question: \"{decision_rule.question}\"")
                        
                        default_answer = decision_rule.default_decision.value.upper()
                        default_emoji = "✅" if default_answer == "YES" else "❌" if default_answer == "NO" else "❓"
                        print(f"   {default_emoji} Default Answer: {default_answer}")
                        
                        if decision_rule.requirements_for_maybe:
                            requirements = [req.value.replace('_', ' ') for req in decision_rule.requirements_for_maybe]
                            print(f"   🔧 Becomes YES if: {', '.join(requirements)} are completed")
                        
                        example_scenario = f"transferring {', '.join([cat.value.replace('_', ' ') for cat in rule.data_category])} from {rule.applicable_countries[0] if rule.applicable_countries else 'Country A'}"
                        print(f"   💡 Example: {example_scenario}")
                        break
            
            print(f"\n🎯 Your extracted rules can now provide YES/NO/MAYBE answers with specific action requirements!")
            print(f"🔍 Use the decision summary JSON file to query specific scenarios programmatically.")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    # Run the enhanced main function
    asyncio.run(main())