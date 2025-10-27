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

from src.config import OPENAI_MODEL, get_openai_client
from src.agents.react_workflow import convert_odrl_file_to_rego, convert_odrl_to_rego_with_coverage

# Verify config loaded
try:
    client = get_openai_client()
    CONFIG_LOADED = True
except Exception as e:
    print(f"⚠ Warning: Config loading issue: {e}")
    CONFIG_LOADED = False


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
            print(f"✓ Success: {result['success']}")
            print(f"✓ Policy ID: {result['policy_id']}")
            print(f"✓ Stage Reached: {result['stage_reached']}")
            print(f"✓ Correction Attempts: {result['correction_attempts']}")
            
            if result.get("expert_analyses"):
                print(f"✓ Expert Consultations: {result['expert_analyses']['expert_count']}")
                print(f"✓ Expert Consensus: {result['expert_analyses']['consensus']['consensus_reached']}")
                print(f"✓ Confidence: {result['expert_analyses']['consensus']['confidence']:.2f}")
            
            print(f"✓ Reasoning Steps: {len(result['reasoning_chain'])}")
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


def cli_server(args):
    """
    Start FastAPI server for API access.
    """
    try:
        import uvicorn
        from src.api.fastapi_server import app
        
        print(f"\n{'='*80}")
        print(f"Starting ODRL to Rego Conversion Server")
        print(f"{'='*80}")
        print(f"Model: {OPENAI_MODEL}")
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"Reload: {args.reload}")
        print(f"{'='*80}\n")
        
        uvicorn.run(
            "src.api.fastapi_server:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    except ImportError:
        print("✗ Error: uvicorn and fastapi not installed")
        print("Install with: pip install uvicorn fastapi")
        return 1
    except Exception as e:
        print(f"✗ Error starting server: {e}")
        return 1


def cli_analyze(args):
    """
    Analyze ODRL policy structure without conversion.
    """
    input_file = args.input
    
    if not os.path.exists(input_file):
        print(f"✗ Error: Input file not found: {input_file}")
        return 1
    
    try:
        with open(input_file, 'r') as f:
            policy = json.load(f)
        
        print(f"\n{'='*80}")
        print(f"ODRL Policy Analysis")
        print(f"{'='*80}")
        
        # Basic structure
        print(f"\n[Structure]")
        print(f"Policy ID: {policy.get('@id', 'N/A')}")
        print(f"Policy Type: {policy.get('@type', 'N/A')}")
        print(f"Permissions: {len(policy.get('permission', []))}")
        print(f"Prohibitions: {len(policy.get('prohibition', []))}")
        print(f"Obligations: {len(policy.get('obligation', []))}")
        
        # Coverage analysis
        print(f"\n[Coverage/Jurisdiction Analysis]")
        jurisdictions = set()
        for perm in policy.get('permission', []):
            for constraint in perm.get('constraint', []):
                left_op = constraint.get('leftOperand', '').lower()
                if any(kw in left_op for kw in ['jurisdiction', 'coverage', 'spatial', 'region']):
                    right_op = constraint.get('rightOperand')
                    if isinstance(right_op, list):
                        jurisdictions.update(right_op)
                    elif right_op:
                        jurisdictions.add(right_op)
        
        for prohib in policy.get('prohibition', []):
            for constraint in prohib.get('constraint', []):
                left_op = constraint.get('leftOperand', '').lower()
                if any(kw in left_op for kw in ['jurisdiction', 'coverage', 'spatial', 'region']):
                    right_op = constraint.get('rightOperand')
                    if isinstance(right_op, list):
                        jurisdictions.update(right_op)
                    elif right_op:
                        jurisdictions.add(right_op)
        
        if jurisdictions:
            print(f"Jurisdictions Found: {', '.join(sorted(jurisdictions))}")
        else:
            print("Jurisdictions: GLOBAL (no specific jurisdiction constraints)")
        
        # Action analysis
        print(f"\n[Actions]")
        actions = set()
        for perm in policy.get('permission', []):
            action = perm.get('action')
            if action:
                actions.add(f"ALLOW: {action}")
        for prohib in policy.get('prohibition', []):
            action = prohib.get('action')
            if action:
                actions.add(f"DENY: {action}")
        
        for action in sorted(actions):
            print(f"  {action}")
        
        # Constraint type analysis
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
  
  # Convert with Mixture of Experts (default)
  python main_odrl_rego.py convert -i policy.json -o policy.rego --use-moe
  
  # Convert without Mixture of Experts (faster)
  python main_odrl_rego.py convert -i policy.json -o policy.rego --no-moe
  
  # Append to existing Rego file
  python main_odrl_rego.py convert -i new_policy.json -e existing.rego -o combined.rego
  
  # Analyze ODRL policy structure
  python main_odrl_rego.py analyze -i policy.json
  
  # Start API server
  python main_odrl_rego.py server --port 8000
  
  # Start API server with auto-reload (development)
  python main_odrl_rego.py server --port 8000 --reload

Key Features:
  - Coverage-Based Rules: Groups rules by jurisdiction + action
  - Regex Pattern Matching: Uses regex.match() and regex.find_all_string_submatch_n()
  - Hierarchical Jurisdictions: Supports parent-child relationships (US > US:CA)
  - AST Validation: Validates logic via Abstract Syntax Trees
  - Mixture of Experts: Consults specialized expert agents
  - Chain of Thought: Documents reasoning at each step
  - Self-Reflection: Validates and corrects its own output
  - OpenAI o3-mini: Uses reasoning model (no temperature/max_tokens needed)

Model: {model}
Config: {config_loaded}
        """.format(model=OPENAI_MODEL, config_loaded=CONFIG_LOADED)
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
        help='Input ODRL JSON file path'
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
        help='Input ODRL JSON file path'
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
    
    # Validate environment
    if not os.getenv("OPENAI_API_KEY"):
        print("\n✗ ERROR: OPENAI_API_KEY environment variable is not set")
        print("Please set it in your .env file or environment")
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