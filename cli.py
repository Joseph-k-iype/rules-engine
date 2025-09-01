"""
Command Line Interface for the Legislation Rules Converter.
Provides comprehensive CLI commands for all major functionality.
"""

import asyncio
import click
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from .main import create_app, get_app
from .config import Config
from .utils import format_file_size, truncate_text

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config-file', type=click.Path(exists=True), help='Custom configuration file')
@click.pass_context
def cli(ctx, verbose, config_file):
    """Legislation Rules Converter - Convert legislation to machine-readable rules."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config_file'] = config_file
    
    # Setup logging level
    if verbose:
        from .utils import setup_logging
        setup_logging("DEBUG")

@cli.command()
@click.option('--folder', '-f', type=click.Path(exists=True, path_type=Path), 
              help='Folder containing PDF files', default=None)
@click.option('--force', is_flag=True, help='Force reprocessing of already processed files')
@click.pass_context
def process(ctx, folder, force):
    """Process legislation PDFs and extract rules."""
    async def run_process():
        app = await create_app()
        
        try:
            if folder is None:
                folder_path = Config.LEGISLATION_PDF_PATH
            else:
                folder_path = folder
            
            click.echo(f"Processing legislation folder: {folder_path}")
            
            if force:
                # Clear existing rules to force reprocessing
                click.echo("Force mode enabled - clearing existing rules...")
                app.rule_manager.existing_rules.clear()
                app.rule_manager.rule_index.clear()
            
            # Process folder
            result = await app.process_legislation_folder(folder_path)
            
            if result['success']:
                click.echo(f"✅ Success: {result['message']}")
                click.echo(f"📁 Processed Files: {result['processed_files']}")
                click.echo(f"📋 Extracted Rules: {result['extracted_rules']}")
                if 'new_rules_added' in result:
                    click.echo(f"🆕 New Rules Added: {result['new_rules_added']}")
                click.echo(f"⏱️  Processing Time: {result['processing_time']:.2f} seconds")
            else:
                click.echo(f"❌ Error: {result.get('error', 'Unknown error')}", err=True)
                sys.exit(1)
            
        finally:
            await app.shutdown()
    
    asyncio.run(run_process())

@cli.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
@click.option('--countries', help='Applicable countries (comma-separated)')
@click.option('--adequacy', help='Adequacy countries (comma-separated)')
@click.option('--article', help='Article reference')
@click.pass_context
def process_file(ctx, file_path, countries, adequacy, article):
    """Process a single legislation file."""
    async def run_process_file():
        app = await create_app()
        
        try:
            kwargs = {}
            if countries:
                kwargs['applicable_countries'] = [c.strip() for c in countries.split(',')]
            if adequacy:
                kwargs['adequacy_countries'] = [c.strip() for c in adequacy.split(',')]
            if article:
                kwargs['article_reference'] = article
            
            click.echo(f"Processing file: {file_path}")
            
            result = await app.process_single_file(file_path, **kwargs)
            
            if result['success']:
                click.echo(f"✅ Success: {result['message']}")
                click.echo(f"📋 Extracted Rules: {result['extracted_rules']}")
                click.echo(f"🆕 New Rules Added: {result['new_rules_added']}")
                click.echo(f"⏱️  Processing Time: {result['processing_time']:.2f} seconds")
                
                # Show extracted rules summary
                if ctx.obj.get('verbose') and result.get('rules'):
                    click.echo("\n📄 Extracted Rules:")
                    for i, rule in enumerate(result['rules'], 1):
                        click.echo(f"  {i}. {rule['name']}")
                        click.echo(f"     {truncate_text(rule['description'], 80)}")
            else:
                click.echo(f"❌ Error: {result.get('error', 'Unknown error')}", err=True)
                sys.exit(1)
            
        finally:
            await app.shutdown()
    
    asyncio.run(run_process_file())

@cli.command()
@click.option('--text', help='Legislation text to process')
@click.option('--file', 'text_file', type=click.Path(exists=True), help='File containing legislation text')
@click.option('--article', help='Article reference')
@click.option('--countries', help='Applicable countries (comma-separated)')
@click.option('--save/--no-save', default=True, help='Save extracted rules')
@click.pass_context
def process_text(ctx, text, text_file, article, countries, save):
    """Process raw legislation text."""
    if not text and not text_file:
        click.echo("Error: Must provide either --text or --file", err=True)
        sys.exit(1)
    
    async def run_process_text():
        app = await create_app()
        
        try:
            # Get text content
            if text_file:
                with open(text_file, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                click.echo(f"Processing text from file: {text_file}")
            else:
                text_content = text
                click.echo("Processing provided text...")
            
            kwargs = {'save_rules': save}
            if article:
                kwargs['article_reference'] = article
            if countries:
                kwargs['applicable_countries'] = [c.strip() for c in countries.split(',')]
            
            result = await app.process_text(text_content, **kwargs)
            
            if result['success']:
                click.echo(f"✅ Success: {result['message']}")
                click.echo(f"📋 Extracted Rules: {result['extracted_rules']}")
                if save:
                    click.echo(f"🆕 New Rules Added: {result['new_rules_added']}")
                click.echo(f"⏱️  Processing Time: {result['processing_time']:.2f} seconds")
                
                # Show rules if not saving
                if not save and ctx.obj.get('verbose') and result.get('rules'):
                    click.echo("\n📄 Extracted Rules:")
                    for rule in result['rules']:
                        click.echo(f"  • {rule['name']}: {truncate_text(rule['description'], 60)}")
            else:
                click.echo(f"❌ Error: {result.get('error', 'Unknown error')}", err=True)
                sys.exit(1)
            
        finally:
            await app.shutdown()
    
    asyncio.run(run_process_text())

@cli.command()
@click.option('--format', 'output_format', 
              type=click.Choice(['json', 'csv', 'table']), 
              default='table', help='Output format')
@click.option('--search', help='Search rules by keyword')
@click.option('--source', help='Filter by source file')
@click.option('--role', help='Filter by impacted role')
@click.option('--limit', type=int, help='Limit number of results')
@click.pass_context
def list_rules(ctx, output_format, search, source, role, limit):
    """List and search existing rules."""
    async def run_list_rules():
        app = await create_app()
        
        try:
            rules = await app.rule_manager.get_all_rules()
            
            # Apply filters
            if search:
                rules = await app.rule_manager.search_rules(search)
            elif source:
                rules = await app.rule_manager.get_rules_by_source(source)
            elif role:
                rules = await app.rule_manager.get_rules_by_role(role)
            
            # Apply limit
            if limit:
                rules = rules[:limit]
            
            if not rules:
                click.echo("No rules found matching the criteria.")
                return
            
            if output_format == 'json':
                click.echo(json.dumps([rule.model_dump() for rule in rules], 
                                    indent=2, default=str, ensure_ascii=False))
            elif output_format == 'csv':
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['ID', 'Name', 'Description', 'Source', 'Role', 'Confidence'])
                
                for rule in rules:
                    writer.writerow([
                        rule.id,
                        rule.name,
                        truncate_text(rule.description, 100),
                        rule.source_file,
                        rule.primary_impacted_role.value if rule.primary_impacted_role else '',
                        f"{rule.confidence_score:.2f}"
                    ])
                
                click.echo(output.getvalue())
            else:  # table format
                click.echo(f"Found {len(rules)} rules:\n")
                for i, rule in enumerate(rules, 1):
                    click.echo(f"{i:3d}. {rule.name}")
                    click.echo(f"     ID: {rule.id}")
                    click.echo(f"     Description: {truncate_text(rule.description, 80)}")
                    click.echo(f"     Source: {rule.source_file}")
                    if rule.primary_impacted_role:
                        click.echo(f"     Role: {rule.primary_impacted_role.value}")
                    click.echo(f"     Confidence: {rule.confidence_score:.2f}")
                    click.echo()
            
        finally:
            await app.shutdown()
    
    asyncio.run(run_list_rules())

@cli.command()
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='Output directory', default=Path('./exports'))
@click.option('--format', 'formats', multiple=True, 
              type=click.Choice(['json', 'csv', 'ttl', 'jsonld']),
              default=['json', 'csv', 'ttl', 'jsonld'], help='Export formats')
@click.pass_context
def export(ctx, output, formats):
    """Export rules and ontologies in various formats."""
    async def run_export():
        app = await create_app()
        
        try:
            click.echo(f"Exporting data to: {output}")
            click.echo(f"Formats: {', '.join(formats)}")
            
            result = await app.export_data(output, list(formats))
            
            if result['success']:
                click.echo(f"✅ Export completed successfully")
                click.echo(f"📁 Output directory: {result['output_directory']}")
                click.echo(f"📄 Exported files:")
                for file_path in result['exported_files']:
                    file_size = format_file_size(Path(file_path).stat().st_size)
                    click.echo(f"  • {Path(file_path).name} ({file_size})")
            else:
                click.echo(f"❌ Export failed: {result.get('error', 'Unknown error')}", err=True)
                sys.exit(1)
            
        finally:
            await app.shutdown()
    
    asyncio.run(run_export())

@cli.command()
@click.pass_context
def status(ctx):
    """Show application status and statistics."""
    async def run_status():
        app = await create_app()
        
        try:
            status_info = app.get_status()
            
            click.echo("=== APPLICATION STATUS ===")
            click.echo(f"Initialized: {'✅' if status_info['initialized'] else '❌'}")
            click.echo(f"Running: {'✅' if status_info['running'] else '❌'}")
            
            if status_info.get('startup_time'):
                click.echo(f"Started: {status_info['startup_time']}")
                click.echo(f"Uptime: {status_info['uptime_seconds']:.1f} seconds")
            
            # Rules statistics
            if 'rules' in status_info:
                rules_info = status_info['rules']
                click.echo(f"\n=== RULES DATABASE ===")
                click.echo(f"Total Rules: {rules_info.get('total_rules', 0)}")
                click.echo(f"Sources: {rules_info.get('sources', 0)}")
                click.echo(f"Average Confidence: {rules_info.get('avg_confidence', 0):.2f}")
                
                if 'roles_distribution' in rules_info:
                    click.echo(f"Role Distribution:")
                    for role, count in rules_info['roles_distribution'].items():
                        click.echo(f"  • {role}: {count}")
            
            # OpenAI statistics
            if 'openai' in status_info:
                openai_info = status_info['openai']
                click.echo(f"\n=== OPENAI API ===")
                click.echo(f"Requests: {openai_info.get('request_count', 0)}")
                click.echo(f"Total Tokens: {openai_info.get('total_tokens', 0):,}")
                click.echo(f"Error Rate: {openai_info.get('error_rate', 0):.2%}")
            
            # PDF Processor
            if 'pdf_processor' in status_info:
                pdf_info = status_info['pdf_processor']
                click.echo(f"\n=== PDF PROCESSOR ===")
                click.echo(f"Cached Files: {pdf_info.get('cached_files', 0)}")
                click.echo(f"Processed Files: {pdf_info.get('processed_files', 0)}")
                click.echo(f"PyMuPDF: {'✅' if pdf_info.get('pymupdf_available') else '❌'}")
                click.echo(f"pdfplumber: {'✅' if pdf_info.get('pdfplumber_available') else '❌'}")
            
            # Ontology Manager
            if 'ontology' in status_info:
                ontology_info = status_info['ontology']
                click.echo(f"\n=== ONTOLOGY MANAGER ===")
                click.echo(f"Last Update: {ontology_info.get('last_update', 'Never')}")
                click.echo(f"RDF Available: {'✅' if ontology_info.get('rdf_available') else '❌'}")
                click.echo(f"Generated Files: {len(ontology_info.get('files', []))}")
            
            # Extraction Engine
            if 'extraction' in status_info:
                extraction_info = status_info['extraction']
                click.echo(f"\n=== EXTRACTION ENGINE ===")
                click.echo(f"Active Jobs: {extraction_info.get('active_jobs', 0)}")
                
                if extraction_info.get('jobs'):
                    click.echo("Current Jobs:")
                    for job_id, job_info in extraction_info['jobs'].items():
                        click.echo(f"  • {job_id[:8]}: {job_info['status']} ({job_info['progress']:.1f}%)")
            
            # File Watcher
            if 'file_watcher' in status_info:
                watcher_info = status_info['file_watcher']
                click.echo(f"\n=== FILE WATCHER ===")
                click.echo(f"Active: {'✅' if watcher_info.get('is_watching') else '❌'}")
                click.echo(f"Watched Directories: {watcher_info.get('active_watches', 0)}")
            
        finally:
            await app.shutdown()
    
    asyncio.run(run_status())

@cli.command()
@click.option('--filename', required=True, help='PDF filename')
@click.option('--countries', required=True, help='Applicable countries (comma-separated)')
@click.option('--adequacy', help='Adequacy countries (comma-separated)', default='')
@click.option('--jurisdiction', help='Jurisdiction name')
@click.option('--type', 'reg_type', help='Regulation type')
@click.pass_context
def add_metadata(ctx, filename, countries, adequacy, jurisdiction, reg_type):
    """Add metadata for a legislation file."""
    async def run_add_metadata():
        app = await create_app()
        
        try:
            applicable_countries = [c.strip() for c in countries.split(',')]
            adequacy_countries = [c.strip() for c in adequacy.split(',')] if adequacy else []
            
            kwargs = {}
            if jurisdiction:
                kwargs['jurisdiction'] = jurisdiction
            if reg_type:
                kwargs['regulation_type'] = reg_type
            
            await app.metadata_manager.add_file_metadata(
                filename, applicable_countries, adequacy_countries, **kwargs
            )
            
            click.echo(f"✅ Metadata added for {filename}")
            click.echo(f"📍 Countries: {', '.join(applicable_countries)}")
            if adequacy_countries:
                click.echo(f"🤝 Adequacy: {', '.join(adequacy_countries)}")
            
        finally:
            await app.shutdown()
    
    asyncio.run(run_add_metadata())

@cli.command()
@click.confirmation_option(prompt='Are you sure you want to clear all caches?')
@click.pass_context
def clear_cache(ctx):
    """Clear all caches and temporary data."""
    async def run_clear_cache():
        app = await create_app()
        
        try:
            # Clear various caches
            if app.pdf_processor:
                app.pdf_processor.clear_cache()
                click.echo("✅ PDF processor cache cleared")
            
            if app.standards_converter:
                app.standards_converter.clear_cache()
                click.echo("✅ Standards converter cache cleared")
            
            if app.openai_service:
                app.openai_service.reset_statistics()
                click.echo("✅ OpenAI statistics reset")
            
            click.echo("✅ All caches cleared successfully")
            
        finally:
            await app.shutdown()
    
    asyncio.run(run_clear_cache())

@cli.command()
@click.pass_context
def validate(ctx):
    """Validate environment and configuration."""
    from .utils import validate_environment
    
    click.echo("=== ENVIRONMENT VALIDATION ===")
    
    errors, warnings = validate_environment()
    
    if not errors and not warnings:
        click.echo("✅ All checks passed - environment is ready")
        return
    
    if warnings:
        click.echo("\n⚠️  WARNINGS:")
        for warning in warnings:
            click.echo(f"  • {warning}")
    
    if errors:
        click.echo("\n❌ ERRORS:")
        for error in errors:
            click.echo(f"  • {error}")
        click.echo("\nFix these errors before running the application.")
        sys.exit(1)
    else:
        click.echo("\n✅ No critical errors found")

@cli.command()
@click.pass_context
def watch(ctx):
    """Start file watching mode for automatic processing."""
    async def run_watch():
        app = await create_app()
        
        try:
            if not app.file_watcher:
                click.echo("❌ File watching not available. Install watchdog: pip install watchdog")
                sys.exit(1)
            
            click.echo("🔍 File watcher is active")
            click.echo("Monitoring directories for changes...")
            
            watcher_status = app.file_watcher.get_status()
            for directory in watcher_status['watch_directories']:
                click.echo(f"  📁 Watching: {directory}")
            
            click.echo("\nPress Ctrl+C to stop watching.")
            
            try:
                while app.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                click.echo("\n👋 Stopping file watcher...")
            
        finally:
            await app.shutdown()
    
    asyncio.run(run_watch())

if __name__ == '__main__':
    cli()