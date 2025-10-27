"""
Main Entry Point for ODRL to Rego Conversion System
Supports CLI and API modes with ReAct agents
Updated with latest LangChain/LangGraph patterns
"""
import argparse
import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import config - Updated to use proper exports
try:
    from src.config import OPENAI_MODEL, get_openai_client
    print(f"✓ Loaded configuration from src/config.py")
    print(f"  OpenAI Model: {OPENAI_MODEL}")
    CONFIG_LOADED = True
except ImportError as e:
    print(f"⚠ Could not load src/config.py: {e}")
    print(f"  Using environment variables instead")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "o3-mini-2025-01-31")
    CONFIG_LOADED = False

# Import conversion functions - Updated imports
from src.agents import convert_odrl_to_rego_react, convert_odrl_file_to_rego


def cli_convert(args):
    """Run conversion from CLI using ReAct agents"""
    print("\n" + "="*80)
    print("ODRL to Rego Conversion - ReAct Agent System")
    print("="*80)
    print(f"Model: {OPENAI_MODEL}")
    print(f"Input: {args.input}")
    print(f"Max Corrections: {args.max_corrections}")
    print(f"Verbose: {args.verbose}")
    print("="*80 + "\n")
    
    print("Loading ODRL policy...")
    
    try:
        # Use the dedicated file conversion function
        result = convert_odrl_file_to_rego(
            input_file=args.input,
            output_file=args.output,
            existing_rego_file=args.existing_rego,
            max_corrections=args.max_corrections
        )
        
        # Print messages
        if args.verbose:
            print("\nConversion Log:")
            print("-" * 80)
            for msg in result["messages"]:
                print(f"  {msg}")
            
            # Print reasoning chain if verbose
            if result.get("reasoning_chain"):
                print("\nReasoning Chain:")
                print("-" * 80)
                for idx, step in enumerate(result["reasoning_chain"], 1):
                    print(f"\n{idx}. Stage: {step.get('stage', 'unknown')}")
                    reasoning = step.get('reasoning', '')
                    # Truncate long reasoning for readability
                    if len(reasoning) > 500:
                        reasoning = reasoning[:500] + "..."
                    print(f"   {reasoning}")
        
        # Print results
        print("\n" + "="*80)
        if result["success"]:
            print("✓ CONVERSION SUCCESSFUL")
        else:
            print("✗ CONVERSION FAILED")
        print("="*80)
        print(f"Policy ID: {result['policy_id']}")
        print(f"Stage Reached: {result['stage_reached']}")
        print(f"Correction Attempts: {result['correction_attempts']}")
        
        if result.get("logical_issues"):
            print(f"\nLogical Issues ({len(result['logical_issues'])}):")
            for issue in result["logical_issues"]:
                print(f"  ⚠ {issue}")
        
        if result["success"]:
            if args.output:
                output_file = args.output
            else:
                # Generate output filename from input
                input_path = Path(args.input)
                output_file = input_path.stem + ".rego"
            
            print(f"\nGenerated Rego saved to: {output_file}")
            print(f"Lines of code: {len(result['generated_rego'].split(chr(10)))}")
            
            if args.verbose:
                print("\nGenerated Rego Code:")
                print("-" * 80)
                print(result["generated_rego"])
                print("-" * 80)
        else:
            print(f"\nError: {result.get('error_message', 'Unknown error')}")
            if not args.verbose:
                print("Run with -v flag for detailed error information")
        
        # Return exit code
        return 0 if result["success"] else 1
        
    except FileNotFoundError:
        print(f"\n✗ ERROR: Input file '{args.input}' not found")
        return 1
    except json.JSONDecodeError as e:
        print(f"\n✗ ERROR: Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: Conversion failed with exception: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cli_server(args):
    """Start FastAPI server"""
    import uvicorn
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║         ODRL to Rego Conversion API Server                           ║
    ║         Enterprise-Scale with ReAct Agents                           ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    Starting server on http://{host}:{port}
    
    API Documentation: http://{host}:{port}/docs
    
    Endpoints:
      POST   /convert              - Convert ODRL JSON to Rego
      POST   /convert/file         - Upload and convert ODRL file
      GET    /rego/{{policy_id}}     - Get Rego for policy
      GET    /rego/{{policy_id}}/download - Download Rego file
      GET    /rego/files/list      - List all Rego files
      DELETE /rego/{{policy_id}}     - Delete policy Rego
      GET    /system/info          - System configuration
      GET    /health               - Health check
    
    ReAct Agents:
      • ODRL Parser Agent       - Semantic understanding
      • Type Inference Agent    - Data type detection
      • Rego Generator Agent    - Enterprise-scale code generation
      • Reflection Agent        - Validation
      • Correction Agent        - Automatic fixes
    
    Enterprise Features:
      • Regex pattern matching for flexible rules
      • String built-ins for hierarchical structures
      • Case-insensitive operations
      • Set operations for efficient checks
      • Multi-tenant ready
    
    Press Ctrl+C to stop the server
    """.format(host=args.host, port=args.port))
    
    # Import here to avoid loading FastAPI unnecessarily
    from src.api.fastapi_server import app
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="ODRL to Rego Conversion System - LangGraph ReAct Multi-Agent Implementation (Latest Libraries)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert ODRL file to Rego using ReAct agents
  python main_odrl_rego.py convert -i policy.json -o policy.rego
  
  # Convert with verbose output (shows ReAct agent reasoning)
  python main_odrl_rego.py convert -i policy.json -o policy.rego -v
  
  # Convert with existing Rego (append mode)
  python main_odrl_rego.py convert -i new_policy.json -e existing.rego -o combined.rego
  
  # Start API server
  python main_odrl_rego.py server --port 8000
  
  # Start API server with auto-reload (development)
  python main_odrl_rego.py server --port 8000 --reload

ReAct Agents (Latest LangChain/LangGraph):
  The system uses multiple specialized ReAct agents that can use tools:
  - ODRL Parser: Extracts and understands ODRL components
  - Type Inference: Determines Rego data types from constraints
  - Rego Generator: Creates enterprise-scale OPA Rego v1 code
  - Reflection: Validates generated code
  - Correction: Fixes issues automatically

Enterprise-Scale Rego Features:
  - Regex pattern matching (regex.match) for flexible rules
  - String built-ins (startswith, contains, lower) for hierarchical orgs
  - Case-insensitive operations for user inputs
  - Set operations for efficient permission checks
  - Multi-tenant and multi-subsidiary support
  - Scales to thousands of users, departments, and resources

Libraries:
  - LangChain (latest): Modern tool decorators and patterns
  - LangGraph (latest): create_react_agent, MemorySaver
  - Pydantic V2: model_config with ConfigDict
  - OpenAI: Latest API patterns

Configuration:
  The system integrates with src/config.py for OpenAI settings.
  Set OPENAI_API_KEY in .env file or environment.
  
  Default model: {model}
  Config loaded: {config_loaded}
        """.format(model=OPENAI_MODEL, config_loaded=CONFIG_LOADED)
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Convert command
    convert_parser = subparsers.add_parser(
        'convert',
        help='Convert ODRL policy to Rego using ReAct agents'
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
        '-m', '--max-corrections',
        type=int,
        default=3,
        help='Maximum correction attempts (default: 3)'
    )
    convert_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output showing agent reasoning'
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
    elif args.command == 'server':
        cli_server(args)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())