"""
Enhanced ODRL to Rego Conversion CLI with Coverage-Based Rules
Uses OpenAI o3-mini reasoning model with advanced agent patterns
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import Config, OPENAI_MODEL
from src.agents.react_workflow import convert_odrl_file_to_rego, convert_odrl_to_rego_with_coverage


def cli_convert(args):
    """
    Handle conversion command with coverage-based approach.
    """
    input_file = args.input
    output_file = args.output
    existing_rego_file = args.existing_rego
    use_moe = args.use_mixture_of_experts
    verbose = args.verbose
    
    # Validate input file
    if not os.path.exists(input_file):
        print(f"✗ Error: Input file not found: {input_file}")
        return 1
    
    # Validate existing rego file if provided
    if existing_rego_file and not os.path.exists(existing_rego_file):
        print(f"✗ Error: Existing Rego file not found: {existing_rego_file}")
        return 1
    
    print(f"\n{'='*80}")
    print(f"ODRL to Rego Conversion (Coverage-Based)")
    print(f"{'='*80}")
    print(f"Model: {OPENAI_MODEL}")
    print(f"Input: {input_file}")
    print(f"Output: {output_file or input_file.replace('.json', '.rego')}")
    print(f"Mixture of Experts: {use_moe}")
    print(f"Verbose: {verbose}")
    if existing_rego_file:
        print(f"Appending to: {existing_rego_file}")
    print(f"{'='*80}\n")
    
    try:
        result = convert_odrl_file_to_rego(
            input_file=input_file,
            output_file=output_file,
            existing_rego_file=existing_rego_file,
            use_mixture_of_experts=use_moe,
            verbose=verbose
        )
        
        if result["success"]:
            print("\n" + "="*80)
            print("CONVERSION SUMMARY")
            print("="*80)
            
            # Check if multiple policies were processed
            if "individual_results" in result:
                num_policies = len(result["individual_results"])
                successful = sum(1 for r in result["individual_results"] if r["success"])
                print(f"✓ Total Policies: {num_policies}")
                print(f"✓ Successful: {successful}")
                print(f"✗ Failed: {num_policies - successful}")
                print(f"✓ Total Correction Attempts: {result['correction_attempts']}")
                
                # Show individual policy summaries
                print(f"\n{'='*80}")
                print("INDIVIDUAL POLICY RESULTS")
                print(f"{'='*80}")
                for idx, individual_result in enumerate(result["individual_results"], 1):
                    status = "✓ SUCCESS" if individual_result["success"] else "✗ FAILED"
                    print(f"\nPolicy {idx}: {individual_result['policy_id']}")
                    print(f"  Status: {status}")
                    print(f"  Stage Reached: {individual_result['stage_reached']}")
                    
                    # Safely access expert_analyses
                    expert_analyses = individual_result.get("expert_analyses")
                    if expert_analyses and isinstance(expert_analyses, dict):
                        expert_count = expert_analyses.get("expert_count")
                        if expert_count is not None:
                            print(f"  Expert Consultations: {expert_count}")
                        
                        consensus = expert_analyses.get("consensus")
                        if consensus and isinstance(consensus, dict):
                            consensus_reached = consensus.get("consensus_reached")
                            if consensus_reached is not None:
                                print(f"  Expert Consensus: {consensus_reached}")
                    
                    if not individual_result["success"]:
                        print(f"  Error: {individual_result.get('error_message', 'Unknown error')}")
            else:
                # Single policy
                print(f"✓ Success: {result['success']}")
                print(f"✓ Policy ID: {result['policy_id']}")
                print(f"✓ Stage Reached: {result['stage_reached']}")
                print(f"✓ Correction Attempts: {result['correction_attempts']}")
                
                # Safely access expert_analyses for single policy
                expert_analyses = result.get("expert_analyses")
                if expert_analyses and isinstance(expert_analyses, dict):
                    expert_count = expert_analyses.get("expert_count")
                    if expert_count is not None:
                        print(f"✓ Expert Consultations: {expert_count}")
                    
                    consensus = expert_analyses.get("consensus")
                    if consensus and isinstance(consensus, dict):
                        consensus_reached = consensus.get("consensus_reached")
                        confidence = consensus.get("confidence")
                        if consensus_reached is not None:
                            print(f"✓ Expert Consensus: {consensus_reached}")
                        if confidence is not None:
                            print(f"✓ Confidence: {confidence:.2f}")
            
            print("="*80)
            
            return 0
        else:
            print("\n" + "="*80)
            print("CONVERSION FAILED")
            print("="*80)
            print(f"✗ Error: {result.get('error_message', 'Unknown error')}")
            print(f"✗ Stage: {result['stage_reached']}")
            print("="*80)
            return 1
    
    except Exception as e:
        print(f"\n✗ Fatal Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def cli_analyze(args):
    """
    Handle analyze command - show ODRL policy structure.
    """
    input_file = args.input
    
    if not os.path.exists(input_file):
        print(f"✗ Error: Input file not found: {input_file}")
        return 1
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both single policy and array of policies
        policies = data if isinstance(data, list) else [data]
        
        print(f"\n{'='*80}")
        print(f"ODRL POLICY ANALYSIS")
        print(f"{'='*80}")
        print(f"File: {input_file}")
        print(f"Number of policies: {len(policies)}\n")
        
        for idx, policy in enumerate(policies, 1):
            if len(policies) > 1:
                print(f"\n{'='*80}")
                print(f"POLICY {idx}/{len(policies)}")
                print(f"{'='*80}")
            
            # Basic info
            print(f"[Policy Info]")
            print(f"  ID: {policy.get('@id', 'N/A')}")
            print(f"  Type: {policy.get('@type', 'N/A')}")
            print(f"  Profile: {policy.get('profile', 'N/A')}")
            
            # Permissions
            print(f"\n[Permissions]")
            permissions = policy.get('permission', [])
            print(f"  Count: {len(permissions)}")
            for i, perm in enumerate(permissions, 1):
                action = perm.get('action', 'unknown')
                target = perm.get('target', 'unknown')
                print(f"  {i}. Action: {action}, Target: {target}")
                constraints = perm.get('constraint', [])
                if constraints:
                    print(f"     Constraints: {len(constraints)}")
            
            # Prohibitions
            print(f"\n[Prohibitions]")
            prohibitions = policy.get('prohibition', [])
            print(f"  Count: {len(prohibitions)}")
            for i, prohib in enumerate(prohibitions, 1):
                action = prohib.get('action', 'unknown')
                target = prohib.get('target', 'unknown')
                print(f"  {i}. Action: {action}, Target: {target}")
                constraints = prohib.get('constraint', [])
                if constraints:
                    print(f"     Constraints: {len(constraints)}")
            
            # Obligations
            print(f"\n[Obligations]")
            obligations = policy.get('obligation', [])
            print(f"  Count: {len(obligations)}")
            
            # Constraint analysis
            print(f"\n[Constraint Types]")
            constraint_types = {}
            
            for perm in policy.get('permission', []):
                for constraint in perm.get('constraint', []):
                    left_op = constraint.get('leftOperand', 'unknown')
                    constraint_types[left_op] = constraint_types.get(left_op, 0) + 1
            
            for prohib in policy.get('prohibition', []):
                for constraint in prohib.get('constraint', []):
                    left_op = constraint.get('leftOperand', 'unknown')
                    constraint_types[left_op] = constraint_types.get(left_op, 0) + 1
            
            for ctype, count in sorted(constraint_types.items()):
                print(f"  {ctype}: {count}")
            
            # Custom properties
            print(f"\n[Custom Properties]")
            has_original_data = False
            original_data_count = 0
            
            def check_original_data(obj):
                nonlocal has_original_data, original_data_count
                if isinstance(obj, dict):
                    if 'custom:originalData' in obj:
                        has_original_data = True
                        original_data_count += 1
                    for value in obj.values():
                        check_original_data(value)
                elif isinstance(obj, list):
                    for item in obj:
                        check_original_data(item)
            
            check_original_data(policy)
            
            if has_original_data:
                print(f"  custom:originalData: {original_data_count} rules tracked")
            else:
                print(f"  No custom:originalData found")
        
        print(f"\n{'='*80}\n")
        return 0
    
    except Exception as e:
        print(f"✗ Error analyzing policy: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cli_server(args):
    """
    Start FastAPI server for API access.
    """
    try:
        import uvicorn
        from src.api.fastapi_server import app
        
        print(f"\n{'='*80}")
        print(f"STARTING ODRL TO REGO API SERVER")
        print(f"{'='*80}")
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"Reload: {args.reload}")
        print(f"Model: {OPENAI_MODEL}")
        print(f"{'='*80}\n")
        
        uvicorn.run(
            "src.api.fastapi_server:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
        
        return 0
        
    except ImportError as e:
        print(f"✗ Error: FastAPI or uvicorn not installed")
        print(f"Install with: pip install fastapi uvicorn")
        return 1
    except Exception as e:
        print(f"✗ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """
    Main CLI entry point.
    """
    parser = argparse.ArgumentParser(
        description="Enhanced ODRL to Rego Converter with Coverage-Based Rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert ODRL to Rego with coverage-based rules
  python main_odrl_rego.py convert -i policy.json -o policy.rego
  
  # Convert with verbose output (shows reasoning chains)
  python main_odrl_rego.py convert -i policy.json -o policy.rego -v
  
  # Convert file with multiple policies (all will be processed)
  python main_odrl_rego.py convert -i policies_array.json -o all_policies.rego
  
  # Convert with Mixture of Experts (default)
  python main_odrl_rego.py convert -i policy.json -o policy.rego --use-moe
  
  # Convert without Mixture of Experts (faster)
  python main_odrl_rego.py convert -i policy.json -o policy.rego --no-moe
  
  # Append to existing Rego file
  python main_odrl_rego.py convert -i new_policy.json -e existing.rego -o combined.rego
  
  # Analyze ODRL policy structure (handles arrays too)
  python main_odrl_rego.py analyze -i policy.json
  
  # Start API server
  python main_odrl_rego.py server --port 8000
  
  # Start API server with auto-reload (development)
  python main_odrl_rego.py server --port 8000 --reload

Key Features:
  - Coverage-Based Rules: Groups rules by jurisdiction + action
  - Multiple Policy Support: Processes arrays of policies automatically
  - Regex Pattern Matching: Uses regex.match() and regex.find_all_string_submatch_n()
  - Hierarchical Jurisdictions: Supports parent-child relationships (US > US:CA)
  - AST Validation: Validates logic via Abstract Syntax Trees
  - Mixture of Experts: Consults specialized expert agents
  - Chain of Thought: Documents reasoning at each step
  - Self-Reflection: Validates and corrects its own output
  - OpenAI o3-mini: Uses reasoning model (no temperature/max_tokens needed)

Model: {model}
        """.format(model=OPENAI_MODEL)
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Convert command
    convert_parser = subparsers.add_parser(
        'convert',
        help='Convert ODRL policy to Rego using coverage-based approach'
    )
    convert_parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input ODRL JSON file path (single policy or array of policies)'
    )
    convert_parser.add_argument(
        '-o', '--output',
        help='Output Rego file path (default: <input>.rego)'
    )
    convert_parser.add_argument(
        '-e', '--existing-rego',
        help='Existing Rego file to append to'
    )
    convert_parser.add_argument(
        '--use-moe',
        dest='use_mixture_of_experts',
        action='store_true',
        default=True,
        help='Use Mixture of Experts pattern (default)'
    )
    convert_parser.add_argument(
        '--no-moe',
        dest='use_mixture_of_experts',
        action='store_false',
        help='Skip Mixture of Experts (faster but less thorough)'
    )
    convert_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output showing agent reasoning chains'
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze ODRL policy structure without conversion'
    )
    analyze_parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input ODRL JSON file path (single policy or array of policies)'
    )
    
    # Server command
    server_parser = subparsers.add_parser(
        'server',
        help='Start FastAPI server for API access'
    )
    server_parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Server host (default: 0.0.0.0)'
    )
    server_parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Server port (default: 8000)'
    )
    server_parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload (development only)'
    )
    
    args = parser.parse_args()
    
    # Validate API key before running any command
    if not Config.API_KEY:
        print("\n✗ ERROR: OPENAI_API_KEY is not configured")
        print("Please set it in your environment:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print("\nOr create a .env file with:")
        print("  OPENAI_API_KEY=your-api-key-here")
        return 1
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate handler
    if args.command == 'convert':
        return cli_convert(args)
    elif args.command == 'analyze':
        return cli_analyze(args)
    elif args.command == 'server':
        return cli_server(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())