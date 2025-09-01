"""
Main application orchestrator for the Legislation Rules Converter.
Initializes all components and provides the main application lifecycle.
"""

import asyncio
import logging
import sys
import signal
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Core modules
from .config import Config
from .utils import setup_logging, validate_environment, ProgressTracker
from .event_system import initialize_event_system, shutdown_event_system
from .file_watcher import initialize_file_watcher, shutdown_file_watcher
from .rule_manager import initialize_rule_manager, get_rule_manager
from .metadata_manager import initialize_metadata_manager, get_metadata_manager
from .openai_service import initialize_openai_service, get_openai_service
from .pdf_processor import initialize_pdf_processor, get_pdf_processor
from .standards_converter import StandardsConverter
from .ontology_manager import OntologyManager
from .extraction_engine import initialize_extraction_engine, get_extraction_engine
from .models import LegislationRule, ExtractionJob, ProcessingStatus

logger = logging.getLogger(__name__)

class LegislationRulesConverter:
    """Main application class that orchestrates all components."""
    
    def __init__(self):
        self.initialized = False
        self.running = False
        
        # Component instances
        self.event_system = None
        self.file_watcher = None
        self.rule_manager = None
        self.metadata_manager = None
        self.openai_service = None
        self.pdf_processor = None
        self.standards_converter = None
        self.ontology_manager = None
        self.extraction_engine = None
        
        # Application state
        self.startup_time = None
        self.shutdown_handlers = []
    
    async def initialize(self) -> bool:
        """Initialize all application components."""
        if self.initialized:
            logger.warning("Application already initialized")
            return True
        
        try:
            self.startup_time = datetime.utcnow()
            logger.info("Starting Legislation Rules Converter initialization...")
            
            # Validate configuration and environment
            Config.validate_config()
            errors, warnings = validate_environment()
            
            if errors:
                for error in errors:
                    logger.error(error)
                logger.error("Cannot start application due to configuration errors")
                return False
            
            for warning in warnings:
                logger.warning(warning)
            
            # Initialize core services
            progress = ProgressTracker(8)
            progress.start()
            
            logger.info("Initializing OpenAI service...")
            self.openai_service = await initialize_openai_service()
            progress.update()
            
            logger.info("Initializing PDF processor...")
            self.pdf_processor = await initialize_pdf_processor()
            progress.update()
            
            logger.info("Initializing rule manager...")
            self.rule_manager = await initialize_rule_manager()
            progress.update()
            
            logger.info("Initializing metadata manager...")
            self.metadata_manager = await initialize_metadata_manager()
            progress.update()
            
            logger.info("Initializing standards converter...")
            self.standards_converter = StandardsConverter()
            progress.update()
            
            logger.info("Initializing ontology manager...")
            self.ontology_manager = OntologyManager(self.standards_converter)
            progress.update()
            
            logger.info("Initializing extraction engine...")
            self.extraction_engine = await initialize_extraction_engine(
                self.openai_service, self.rule_manager, 
                self.standards_converter, self.ontology_manager
            )
            progress.update()
            
            logger.info("Initializing event system...")
            self.event_system = await initialize_event_system(
                self.ontology_manager, self.rule_manager, self.standards_converter
            )
            progress.update()
            
            # Initialize file watcher (optional - may not be available)
            logger.info("Initializing file watcher...")
            try:
                self.file_watcher = await initialize_file_watcher()
                if self.file_watcher:
                    logger.info("File watcher initialized successfully")
                else:
                    logger.warning("File watcher not available - manual updates only")
            except Exception as e:
                logger.warning(f"File watcher initialization failed: {e}")
                self.file_watcher = None
            
            # Register shutdown handlers
            self._register_shutdown_handlers()
            
            self.initialized = True
            self.running = True
            
            initialization_time = (datetime.utcnow() - self.startup_time).total_seconds()
            logger.info(f"Application initialized successfully in {initialization_time:.2f} seconds")
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            await self._cleanup()
            return False
    
    async def process_legislation_folder(self, folder_path: Path = None) -> Dict[str, Any]:
        """Process all PDF files in the legislation folder."""
        if not self.initialized:
            raise RuntimeError("Application not initialized")
        
        if folder_path is None:
            folder_path = Config.LEGISLATION_PDF_PATH
        
        logger.info(f"Processing legislation folder: {folder_path}")
        start_time = datetime.utcnow()
        
        try:
            # Get PDF files
            pdf_files = await self.pdf_processor.get_pdf_files(folder_path)
            
            if not pdf_files:
                logger.warning(f"No PDF files found in {folder_path}")
                return {
                    "success": True,
                    "message": "No PDF files to process",
                    "processed_files": 0,
                    "extracted_rules": 0,
                    "processing_time": 0.0
                }
            
            # Get already processed files
            processed_files = self.rule_manager.get_processed_files()
            new_files = [f for f in pdf_files if f.name not in processed_files]
            
            if not new_files:
                logger.info("All PDF files have already been processed")
                return {
                    "success": True,
                    "message": "All files already processed",
                    "processed_files": 0,
                    "extracted_rules": 0,
                    "processing_time": 0.0
                }
            
            logger.info(f"Processing {len(new_files)} new PDF files")
            all_extracted_rules = []
            
            # Process each file
            for pdf_file in new_files:
                try:
                    logger.info(f"Processing: {pdf_file.name}")
                    
                    # Extract text from PDF
                    text, metadata = await self.pdf_processor.extract_text_from_file(pdf_file)
                    
                    # Get metadata for this file
                    file_metadata = self.metadata_manager.get_file_metadata(pdf_file.name)
                    
                    # Extract rules
                    result = await self.extraction_engine.extract_from_text(
                        legislation_text=text,
                        article_reference=f"Document: {pdf_file.name}",
                        source_file=pdf_file.name,
                        applicable_countries=file_metadata['applicable_countries'],
                        adequacy_countries=file_metadata['adequacy_countries']
                    )
                    
                    all_extracted_rules.extend(result.rules)
                    
                except Exception as e:
                    logger.error(f"Error processing {pdf_file}: {e}")
                    continue
            
            # Save new rules
            if all_extracted_rules:
                added_count = await self.rule_manager.save_new_rules(all_extracted_rules)
                
                # Trigger ontology regeneration
                if added_count > 0:
                    await self.ontology_manager.regenerate_ontologies([
                        rule.model_dump() for rule in all_extracted_rules
                    ])
            else:
                added_count = 0
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                "success": True,
                "message": f"Processed {len(new_files)} files, extracted {len(all_extracted_rules)} rules",
                "processed_files": len(new_files),
                "extracted_rules": len(all_extracted_rules),
                "new_rules_added": added_count,
                "processing_time": processing_time
            }
            
            logger.info(f"Folder processing completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing legislation folder: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_files": 0,
                "extracted_rules": 0,
                "processing_time": (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def process_single_file(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """Process a single legislation file."""
        if not self.initialized:
            raise RuntimeError("Application not initialized")
        
        logger.info(f"Processing single file: {file_path}")
        start_time = datetime.utcnow()
        
        try:
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "extracted_rules": 0
                }
            
            # Extract text from PDF
            text, metadata = await self.pdf_processor.extract_text_from_file(file_path)
            
            # Get metadata
            file_metadata = self.metadata_manager.get_file_metadata(file_path.name)
            
            # Override with provided kwargs
            applicable_countries = kwargs.get('applicable_countries', file_metadata['applicable_countries'])
            adequacy_countries = kwargs.get('adequacy_countries', file_metadata['adequacy_countries'])
            
            # Extract rules
            result = await self.extraction_engine.extract_from_text(
                legislation_text=text,
                article_reference=kwargs.get('article_reference', f"Document: {file_path.name}"),
                source_file=file_path.name,
                applicable_countries=applicable_countries,
                adequacy_countries=adequacy_countries
            )
            
            # Save rules
            if result.rules:
                added_count = await self.rule_manager.save_new_rules(result.rules)
                
                # Trigger ontology update
                if added_count > 0:
                    await self.ontology_manager.regenerate_ontologies([
                        rule.model_dump() for rule in result.rules
                    ])
            else:
                added_count = 0
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            response = {
                "success": True,
                "message": f"Processed {file_path.name}, extracted {len(result.rules)} rules",
                "extracted_rules": len(result.rules),
                "new_rules_added": added_count,
                "processing_time": processing_time,
                "rules": [rule.model_dump() for rule in result.rules]
            }
            
            logger.info(f"Single file processing completed: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing single file: {e}")
            return {
                "success": False,
                "error": str(e),
                "extracted_rules": 0,
                "processing_time": (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def process_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process raw legislation text."""
        if not self.initialized:
            raise RuntimeError("Application not initialized")
        
        logger.info("Processing raw text input")
        start_time = datetime.utcnow()
        
        try:
            # Extract rules
            result = await self.extraction_engine.extract_from_text(
                legislation_text=text,
                article_reference=kwargs.get('article_reference', "Raw Text Input"),
                source_file=kwargs.get('source_file', "text_input.txt"),
                applicable_countries=kwargs.get('applicable_countries', []),
                adequacy_countries=kwargs.get('adequacy_countries', [])
            )
            
            # Save rules if requested
            added_count = 0
            if kwargs.get('save_rules', True) and result.rules:
                added_count = await self.rule_manager.save_new_rules(result.rules)
                
                # Trigger ontology update
                if added_count > 0:
                    await self.ontology_manager.regenerate_ontologies([
                        rule.model_dump() for rule in result.rules
                    ])
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "success": True,
                "message": f"Processed text input, extracted {len(result.rules)} rules",
                "extracted_rules": len(result.rules),
                "new_rules_added": added_count,
                "processing_time": processing_time,
                "rules": [rule.model_dump() for rule in result.rules]
            }
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return {
                "success": False,
                "error": str(e),
                "extracted_rules": 0,
                "processing_time": (datetime.utcnow() - start_time).total_seconds()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get application status and statistics."""
        if not self.initialized:
            return {
                "initialized": False,
                "running": False
            }
        
        status = {
            "initialized": self.initialized,
            "running": self.running,
            "startup_time": self.startup_time.isoformat() if self.startup_time else None,
            "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds() if self.startup_time else 0
        }
        
        # Add component status
        try:
            if self.rule_manager:
                status["rules"] = self.rule_manager.get_statistics()
            
            if self.openai_service:
                status["openai"] = self.openai_service.get_statistics()
            
            if self.pdf_processor:
                status["pdf_processor"] = self.pdf_processor.get_cache_stats()
            
            if self.ontology_manager:
                status["ontology"] = self.ontology_manager.get_ontology_status()
            
            if self.extraction_engine:
                active_jobs = self.extraction_engine.get_all_jobs()
                status["extraction"] = {
                    "active_jobs": len(active_jobs),
                    "jobs": {job_id: {
                        "status": job.status.value,
                        "progress": job.progress,
                        "source_file": job.source_file
                    } for job_id, job in active_jobs.items()}
                }
            
            if self.file_watcher:
                status["file_watcher"] = self.file_watcher.get_status()
            
        except Exception as e:
            status["status_error"] = str(e)
        
        return status
    
    async def export_data(self, output_dir: Path, formats: list = None) -> Dict[str, Any]:
        """Export all data in specified formats."""
        if not self.initialized:
            raise RuntimeError("Application not initialized")
        
        if formats is None:
            formats = ["json", "csv", "ttl", "jsonld"]
        
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        exported_files = []
        
        try:
            # Export rules
            if "json" in formats:
                json_file = output_dir / f"all_rules_{timestamp}.json"
                await self.rule_manager.export_rules(json_file, "json")
                exported_files.append(str(json_file))
            
            if "csv" in formats:
                csv_file = output_dir / f"all_rules_{timestamp}.csv"
                await self.rule_manager.export_rules(csv_file, "csv")
                exported_files.append(str(csv_file))
            
            # Export integrated standards
            if self.rule_manager.existing_rules:
                integrated_rules = self.standards_converter.batch_convert_rules(
                    self.rule_manager.existing_rules
                )
                
                if "ttl" in formats:
                    ttl_file = output_dir / f"integrated_ontology_{timestamp}.ttl"
                    await self.ontology_manager._generate_complete_ontologies(
                        integrated_rules, timestamp
                    )
                    exported_files.append(str(ttl_file))
                
                if "jsonld" in formats:
                    jsonld_file = output_dir / f"integrated_ontology_{timestamp}.jsonld"
                    # TTL generation also creates JSON-LD
                    exported_files.append(str(jsonld_file))
            
            return {
                "success": True,
                "exported_files": exported_files,
                "formats": formats,
                "output_directory": str(output_dir)
            }
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "exported_files": exported_files
            }
    
    def _register_shutdown_handlers(self):
        """Register signal handlers for graceful shutdown."""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def shutdown(self):
        """Gracefully shutdown the application."""
        if not self.running:
            return
        
        logger.info("Starting application shutdown...")
        self.running = False
        
        try:
            # Shutdown components in reverse order
            if self.file_watcher:
                await shutdown_file_watcher()
            
            if self.event_system:
                await shutdown_event_system()
            
            # Run custom shutdown handlers
            for handler in self.shutdown_handlers:
                try:
                    await handler()
                except Exception as e:
                    logger.error(f"Error in shutdown handler: {e}")
            
            await self._cleanup()
            
            if self.startup_time:
                uptime = (datetime.utcnow() - self.startup_time).total_seconds()
                logger.info(f"Application shutdown complete after {uptime:.1f} seconds uptime")
            else:
                logger.info("Application shutdown complete")
                
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def _cleanup(self):
        """Clean up resources."""
        try:
            # Clear caches
            if self.pdf_processor:
                self.pdf_processor.clear_cache()
            
            if self.standards_converter:
                self.standards_converter.clear_cache()
            
            # Reset statistics
            if self.openai_service:
                self.openai_service.reset_statistics()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def add_shutdown_handler(self, handler):
        """Add a custom shutdown handler."""
        self.shutdown_handlers.append(handler)

# Global application instance
app = None

async def create_app() -> LegislationRulesConverter:
    """Create and initialize the application."""
    global app
    
    # Setup logging first
    setup_logging()
    
    app = LegislationRulesConverter()
    
    success = await app.initialize()
    if not success:
        logger.error("Application initialization failed")
        sys.exit(1)
    
    logger.info("Application created and initialized successfully")
    return app

def get_app() -> Optional[LegislationRulesConverter]:
    """Get the global application instance."""
    return app

async def main():
    """Main entry point for running the application standalone."""
    try:
        # Create and initialize application
        application = await create_app()
        
        # Process legislation folder by default
        result = await application.process_legislation_folder()
        
        # Print results
        print(f"\n=== PROCESSING RESULTS ===")
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        print(f"Processed Files: {result['processed_files']}")
        print(f"Extracted Rules: {result['extracted_rules']}")
        print(f"Processing Time: {result['processing_time']:.2f} seconds")
        
        # Show status
        status = application.get_status()
        print(f"\n=== APPLICATION STATUS ===")
        print(f"Total Rules in Database: {status.get('rules', {}).get('total_rules', 0)}")
        print(f"OpenAI Requests: {status.get('openai', {}).get('request_count', 0)}")
        print(f"Uptime: {status.get('uptime_seconds', 0):.1f} seconds")
        
        # Keep running for file watching
        if application.file_watcher and application.file_watcher.is_watching:
            print(f"\n=== FILE WATCHING ACTIVE ===")
            print("Monitoring for file changes... Press Ctrl+C to exit.")
            
            try:
                while application.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass
        
        # Shutdown
        await application.shutdown()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())