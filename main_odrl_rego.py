"""
Main Entry Point for ODRL to Rego Conversion System
Supports CLI and API modes with ReAct agents
Integrates with existing project config.py
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

# Import config to ensure it's loaded
try:
    from src.config import OPENAI_MODEL, get_openai_client
    print(f"✓ Loaded configuration from src/config.py")
    print(f"  OpenAI Model: {OPENAI_MODEL}")
except ImportError as e:
    print(f"⚠ Could not load src/config.py: {e}")
    print(f"  Using environment variables instead")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

from src.agents import convert_odrl_to_rego_react, convert_odrl_file_to_rego


def cli_convert(args):
    """Run conversion from CLI using ReAct agents"""
    print("\n" + "="*80)
    print("ODRL to Rego Conversion - ReAct Agent System")
    print("="*80)
    print(f"Model: {OPENAI_MODEL}")
    print(f"Input: {args.input}")
    print(f"Max Corrections: {args.max_corrections}")
    print("="*80 + "\n")
    
    print("Loading ODRL policy...")
    
    # Use the dedicated file conversion function
    result = convert_odrl_file_to_rego(
        input_file=args.input,
        output_file=args.output,
        existing_rego_file=args.existing_rego,
        max_corrections=args.max_corrections
    )
    
    # Print messages
    print("\nConversion Log:")
    print("-" * 80)
    for msg in result["messages"]:
        print(f"  {msg}")
    
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
    
    if result["logical_issues"]:
        print(f"\nLogical Issues ({len(result['logical_issues'])}):")
        for issue in result["logical_issues"]:
            print(f"  ⚠ {issue}")
    
    if result["success"]:
        if args.output:
            output_file = args.output
        else:
            output_file = result.get("output_file")
            
        if output_file:
            print(f"\n✓ Rego code saved to: {output_file}")
            print(f"  Size: {len(result['generated_rego'])} characters")
        
        if args.verbose:
            print("\n" + "="*80)
            print("Generated Rego Code:")
            print("="*80)
            print(result["generated_rego"])
            print("="*80)
    else:
        print(f"\n✗ Error: {result.get('error_message', 'Unknown error')}")
        return 1
    
    # Show reasoning chain if verbose
    if args.verbose and result["reasoning_chain"]:
        print("\n" + "="*80)
        print("ReAct Agent Reasoning Chain:")
        print("="*80)
        for step in result["reasoning_chain"]:
            print(f"\n[{step['stage'].upper()}]")
            print("-" * 80)
            # Truncate long reasoning for readability
            reasoning = step["reasoning"]
            if len(reasoning) > 1000:
                reasoning = reasoning[:1000] + "\n... (truncated)"
            print(reasoning)
    
    print("\n" + "="*80)
    print("Conversion complete!")
    print("="*80 + "\n")
    
    return 0 if result["success"] else 1


def start_server(args):
    """Start FastAPI server"""
    import uvicorn
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║  ODRL to Rego Conversion API Server                              ║
    ║  LangGraph ReAct Multi-Agent System                              ║
    ╚═══════════════════════════════════════════════════════════════════╝
    
    Configuration:
      Host: {args.host}
      Port: {args.port}
      Model: {OPENAI_MODEL}
      Reload: {args.reload}
    
    API Documentation: http://{args.host}:{args.port}/docs
    ReDoc: http://{args.host}:{args.port}/redoc
    
    Available Endpoints:
      POST   /convert              - Convert ODRL to Rego (ReAct agents)
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
      • Rego Generator Agent    - Code generation
      • Reflection Agent        - Validation
      • Correction Agent        - Automatic fixes
    
    Press Ctrl+C to stop the server
    """)
    
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
        description="ODRL to Rego Conversion System - LangGraph ReAct Multi-Agent Implementation",
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

ReAct Agents:
  The system uses multiple specialized ReAct agents that can use tools:
  - ODRL Parser: Extracts and understands ODRL components
  - Type Inference: Determines Rego data types from constraints
  - Rego Generator: Creates OPA Rego v1 compliant code
  - Reflection: Validates generated code
  - Correction: Fixes issues automatically

Configuration:
  The system integrates with src/config.py for OpenAI settings.
  Set OPENAI_API_KEY in .env file or environment.
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert ODRL to Rego (CLI mode)')
    convert_parser.add_argument('-i', '--input', required=True, 
                               help='Input ODRL JSON file')
    convert_parser.add_argument('-o', '--output', 
                               help='Output Rego file (default: auto-generated)')
    convert_parser.add_argument('-e', '--existing-rego', 
                               help='Existing Rego file to append to')
    convert_parser.add_argument('-m', '--max-corrections', type=int, default=3, 
                               help='Maximum correction attempts (default: 3)')
    convert_parser.add_argument('-v', '--verbose', action='store_true', 
                               help='Show detailed ReAct agent reasoning')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Start FastAPI server')
    server_parser.add_argument('--host', default='0.0.0.0', 
                              help='Server host (default: 0.0.0.0)')
    server_parser.add_argument('--port', type=int, 
                              default=int(os.getenv("SERVER_PORT", "8000")),
                              help='Server port (default: from env or 8000)')
    server_parser.add_argument('--reload', action='store_true', 
                              help='Enable auto-reload (development mode)')
    
    args = parser.parse_args()
    
    if args.command == 'convert':
        return cli_convert(args)
    elif args.command == 'server':
        start_server(args)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())