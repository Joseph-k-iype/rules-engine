"""
RESTful API interface for the Legislation Rules Converter.
Provides HTTP endpoints for all major functionality.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from .main import LegislationRulesConverter, create_app
from .models import LegislationRule, ProcessingStatus
from .config import Config

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class ProcessTextRequest(BaseModel):
    text: str = Field(..., description="Legislation text to process")
    article_reference: Optional[str] = Field(None, description="Article reference")
    applicable_countries: Optional[List[str]] = Field(None, description="Applicable countries")
    adequacy_countries: Optional[List[str]] = Field(None, description="Adequacy countries")
    save_rules: bool = Field(True, description="Whether to save extracted rules")

class ProcessResponse(BaseModel):
    success: bool
    message: str
    extracted_rules: int
    new_rules_added: Optional[int] = None
    processing_time: float
    job_id: Optional[str] = None

class RuleSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query")
    source_file: Optional[str] = Field(None, description="Filter by source file")
    role: Optional[str] = Field(None, description="Filter by role")
    limit: Optional[int] = Field(None, description="Limit results")

class MetadataRequest(BaseModel):
    filename: str
    applicable_countries: List[str]
    adequacy_countries: Optional[List[str]] = None
    jurisdiction: Optional[str] = None
    regulation_type: Optional[str] = None

class ExportRequest(BaseModel):
    formats: List[str] = Field(["json", "csv", "ttl", "jsonld"], description="Export formats")

# Global app instance
app_instance: Optional[LegislationRulesConverter] = None

async def get_app_instance():
    """Dependency to get the application instance."""
    global app_instance
    if app_instance is None:
        app_instance = await create_app()
    return app_instance

# FastAPI app
app = FastAPI(
    title="Legislation Rules Converter API",
    description="RESTful API for converting legislation to machine-readable rules",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    global app_instance
    try:
        app_instance = await create_app()
        logger.info("API application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global app_instance
    if app_instance:
        await app_instance.shutdown()
        logger.info("API application shutdown complete")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Legislation Rules Converter API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "/status"
    }

@app.get("/status")
async def get_status(app_inst: LegislationRulesConverter = Depends(get_app_instance)):
    """Get application status and statistics."""
    try:
        status = app_inst.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/folder", response_model=ProcessResponse)
async def process_folder(
    background_tasks: BackgroundTasks,
    app_inst: LegislationRulesConverter = Depends(get_app_instance)
):
    """Process all PDF files in the legislation folder."""
    try:
        result = await app_inst.process_legislation_folder()
        return ProcessResponse(**result)
    except Exception as e:
        logger.error(f"Error processing folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/file", response_model=ProcessResponse)
async def process_file(
    file: UploadFile = File(...),
    applicable_countries: Optional[str] = None,
    adequacy_countries: Optional[str] = None,
    article_reference: Optional[str] = None,
    app_inst: LegislationRulesConverter = Depends(get_app_instance)
):
    """Process a single uploaded PDF file."""
    try:
        # Save uploaded file temporarily
        temp_file = Path(f"/tmp/{file.filename}")
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Parse country parameters
        kwargs = {}
        if applicable_countries:
            kwargs['applicable_countries'] = [c.strip() for c in applicable_countries.split(',')]
        if adequacy_countries:
            kwargs['adequacy_countries'] = [c.strip() for c in adequacy_countries.split(',')]
        if article_reference:
            kwargs['article_reference'] = article_reference
        
        # Process the file
        result = await app_inst.process_single_file(temp_file, **kwargs)
        
        # Clean up
        temp_file.unlink()
        
        return ProcessResponse(**result)
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/text", response_model=ProcessResponse)
async def process_text(
    request: ProcessTextRequest,
    app_inst: LegislationRulesConverter = Depends(get_app_instance)
):
    """Process raw legislation text."""
    try:
        kwargs = {
            'article_reference': request.article_reference,
            'save_rules': request.save_rules
        }
        if request.applicable_countries:
            kwargs['applicable_countries'] = request.applicable_countries
        if request.adequacy_countries:
            kwargs['adequacy_countries'] = request.adequacy_countries
        
        result = await app_inst.process_text(request.text, **kwargs)
        return ProcessResponse(**result)
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rules/search")
async def search_rules(
    request: RuleSearchRequest,
    app_inst: LegislationRulesConverter = Depends(get_app_instance)
):
    """Search existing rules."""
    try:
        if request.query:
            rules = await app_inst.rule_manager.search_rules(request.query)
        elif request.source_file:
            rules = await app_inst.rule_manager.get_rules_by_source(request.source_file)
        elif request.role:
            rules = await app_inst.rule_manager.get_rules_by_role(request.role)
        else:
            rules = await app_inst.rule_manager.get_all_rules()
        
        # Apply limit
        if request.limit:
            rules = rules[:request.limit]
        
        return {
            "total_results": len(rules),
            "rules": [rule.model_dump() for rule in rules]
        }
    except Exception as e:
        logger.error(f"Error searching rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rules/{rule_id}")
async def get_rule(
    rule_id: str,
    app_inst: LegislationRulesConverter = Depends(get_app_instance)
):
    """Get a specific rule by ID."""
    try:
        rule = await app_inst.rule_manager.get_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        return rule.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/metadata")
async def add_metadata(
    request: MetadataRequest,
    app_inst: LegislationRulesConverter = Depends(get_app_instance)
):
    """Add metadata for a legislation file."""
    try:
        kwargs = {}
        if request.jurisdiction:
            kwargs['jurisdiction'] = request.jurisdiction
        if request.regulation_type:
            kwargs['regulation_type'] = request.regulation_type
        
        await app_inst.metadata_manager.add_file_metadata(
            request.filename,
            request.applicable_countries,
            request.adequacy_countries or [],
            **kwargs
        )
        
        return {
            "success": True,
            "message": f"Metadata added for {request.filename}"
        }
    except Exception as e:
        logger.error(f"Error adding metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export")
async def export_data(
    request: ExportRequest,
    app_inst: LegislationRulesConverter = Depends(get_app_instance)
):
    """Export rules and ontologies."""
    try:
        output_dir = Path("/tmp/exports")
        result = await app_inst.export_data(output_dir, request.formats)
        return result
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export/{filename}")
async def download_export(filename: str):
    """Download an exported file."""
    try:
        file_path = Path(f"/tmp/exports/{filename}")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    app_inst: LegislationRulesConverter = Depends(get_app_instance)
):
    """Get the status of a processing job."""
    try:
        job = app_inst.extraction_engine.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cache")
async def clear_cache(app_inst: LegislationRulesConverter = Depends(get_app_instance)):
    """Clear all caches."""
    try:
        if app_inst.pdf_processor:
            app_inst.pdf_processor.clear_cache()
        if app_inst.standards_converter:
            app_inst.standards_converter.clear_cache()
        if app_inst.openai_service:
            app_inst.openai_service.reset_statistics()
        
        return {
            "success": True,
            "message": "All caches cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/validate")
async def validate_environment():
    """Validate environment and configuration."""
    try:
        from .utils import validate_environment
        errors, warnings = validate_environment()
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Error validating environment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def start_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the API server."""
    uvicorn.run(
        "legislation_rules_converter.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    start_api()