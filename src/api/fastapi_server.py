"""
FastAPI Server for ODRL to Rego Conversion Service
Uses ReAct agents and integrates with existing project config
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Body, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import existing config
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.config import OPENAI_MODEL, get_openai_client
    CONFIG_LOADED = True
except ImportError:
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    CONFIG_LOADED = False

from ..agents.react_workflow import convert_odrl_to_rego_react


# ============================================================================
# Pydantic Models
# ============================================================================

class ODRLPolicy(BaseModel):
    """Input model for ODRL policy"""
    policy: Dict[str, Any] = Field(..., description="ODRL policy in JSON-LD format")
    append_to_existing: bool = Field(False, description="Whether to append to existing Rego")
    max_corrections: int = Field(3, description="Maximum correction attempts", ge=1, le=10)


class ConversionResponse(BaseModel):
    """Response model for conversion"""
    success: bool
    policy_id: str
    generated_rego: str
    messages: List[str]
    reasoning_chain: List[Dict[str, str]]
    logical_issues: List[str]
    correction_attempts: int
    error_message: Optional[str] = None
    stage_reached: str
    timestamp: str
    model_used: str


class RegoFile(BaseModel):
    """Model for Rego file metadata"""
    filename: str
    policy_ids: List[str]
    created_at: str
    updated_at: str
    size_bytes: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    model: str
    config_loaded: bool
    timestamp: str


class SystemInfo(BaseModel):
    """System information response"""
    openai_model: str
    config_source: str
    react_agents_enabled: bool
    max_corrections_default: int
    storage_directory: str


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="ODRL to Rego Conversion API",
    description="Convert ODRL policies to OPA Rego v1 using LangGraph ReAct agents",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage directory
REGO_STORAGE_DIR = Path("./rego_policies")
REGO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
METADATA_FILE = REGO_STORAGE_DIR / "metadata.json"


# ============================================================================
# Helper Functions
# ============================================================================

def load_metadata() -> Dict[str, Any]:
    """Load metadata about stored Rego files"""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {"files": {}}


def save_metadata(metadata: Dict[str, Any]):
    """Save metadata about stored Rego files"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)


def get_existing_rego(policy_id: str) -> Optional[str]:
    """Get existing Rego code for a policy ID"""
    metadata = load_metadata()
    
    for filename, file_meta in metadata.get("files", {}).items():
        if policy_id in file_meta.get("policy_ids", []):
            rego_path = REGO_STORAGE_DIR / filename
            if rego_path.exists():
                return rego_path.read_text()
    
    return None


def save_rego_file(policy_id: str, rego_code: str, append: bool = False) -> str:
    """Save Rego code to file"""
    metadata = load_metadata()
    
    # Sanitize policy ID for filename
    safe_id = policy_id.replace('/', '_').replace(':', '_').replace('http', '').replace('https', '').strip('_')
    filename = f"{safe_id}.rego"
    
    rego_path = REGO_STORAGE_DIR / filename
    
    # Write file
    if append and rego_path.exists():
        with open(rego_path, 'a') as f:
            f.write("\n\n# " + "="*60 + "\n")
            f.write(f"# Policy: {policy_id}\n")
            f.write(f"# Added: {datetime.utcnow().isoformat()}\n")
            f.write("# " + "="*60 + "\n\n")
            f.write(rego_code)
    else:
        with open(rego_path, 'w') as f:
            f.write(rego_code)
    
    # Update metadata
    if "files" not in metadata:
        metadata["files"] = {}
    
    if filename not in metadata["files"]:
        metadata["files"][filename] = {
            "policy_ids": [],
            "created_at": datetime.utcnow().isoformat()
        }
    
    if policy_id not in metadata["files"][filename]["policy_ids"]:
        metadata["files"][filename]["policy_ids"].append(policy_id)
    
    metadata["files"][filename]["updated_at"] = datetime.utcnow().isoformat()
    metadata["files"][filename]["size_bytes"] = rego_path.stat().st_size
    
    save_metadata(metadata)
    
    return filename


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "ODRL to Rego Conversion API",
        "version": "2.0.0",
        "description": "Convert ODRL policies to OPA Rego v1 using LangGraph ReAct agents",
        "docs": "/docs",
        "health": "/health",
        "system_info": "/system/info"
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "model": OPENAI_MODEL,
        "config_loaded": CONFIG_LOADED,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/system/info", response_model=SystemInfo, tags=["System"])
async def system_info():
    """Get system configuration information"""
    return {
        "openai_model": OPENAI_MODEL,
        "config_source": "src/config.py" if CONFIG_LOADED else "environment",
        "react_agents_enabled": True,
        "max_corrections_default": 3,
        "storage_directory": str(REGO_STORAGE_DIR.absolute())
    }


@app.post("/convert", response_model=ConversionResponse, tags=["Conversion"])
async def convert_odrl(request: ODRLPolicy):
    """
    Convert an ODRL policy to Rego using ReAct agents.
    
    This endpoint uses a multi-agent system with:
    - ODRL Parser Agent: Deep semantic understanding
    - Type Inference Agent: Data type detection  
    - Rego Generator Agent: Code generation
    - Reflection Agent: Validation
    - Correction Agent: Automatic fixes
    
    Example ODRL policy structure:
    ```json
    {
      "@context": "http://www.w3.org/ns/odrl.jsonld",
      "@type": "Set",
      "uid": "http://example.com/policy:1",
      "permission": [{
        "target": "http://example.com/data:dataset1",
        "action": "use",
        "constraint": [{
          "leftOperand": "purpose",
          "operator": "eq",
          "rightOperand": "http://example.com/purpose:research"
        }]
      }]
    }
    ```
    """
    try:
        # Get existing Rego if appending
        existing_rego = None
        if request.append_to_existing:
            policy_id = (request.policy.get("uid") or 
                        request.policy.get("@id") or 
                        request.policy.get("policyid"))
            if policy_id:
                existing_rego = get_existing_rego(policy_id)
        
        # Run ReAct agent conversion
        result = convert_odrl_to_rego_react(
            odrl_json=request.policy,
            existing_rego=existing_rego,
            max_corrections=request.max_corrections
        )
        
        # Save Rego file if successful
        if result["success"]:
            filename = save_rego_file(
                result["policy_id"],
                result["generated_rego"],
                append=request.append_to_existing
            )
            result["messages"].append(f"✓ Saved Rego to: {filename}")
        
        # Return response
        return ConversionResponse(
            success=result["success"],
            policy_id=result["policy_id"],
            generated_rego=result["generated_rego"],
            messages=result["messages"],
            reasoning_chain=result["reasoning_chain"],
            logical_issues=result["logical_issues"],
            correction_attempts=result["correction_attempts"],
            error_message=result.get("error_message"),
            stage_reached=result["stage_reached"],
            timestamp=datetime.utcnow().isoformat(),
            model_used=OPENAI_MODEL
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@app.post("/convert/file", tags=["Conversion"])
async def convert_odrl_file(
    file: UploadFile = File(...),
    append_to_existing: bool = Query(False),
    max_corrections: int = Query(3, ge=1, le=10)
):
    """Convert an ODRL policy from uploaded JSON file"""
    try:
        content = await file.read()
        odrl_policy = json.loads(content.decode('utf-8'))
        
        request = ODRLPolicy(
            policy=odrl_policy,
            append_to_existing=append_to_existing,
            max_corrections=max_corrections
        )
        
        return await convert_odrl(request)
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File conversion failed: {str(e)}")


@app.get("/rego/{policy_id}", tags=["Rego Management"])
async def get_rego(policy_id: str):
    """Retrieve generated Rego code for a specific policy ID"""
    rego_code = get_existing_rego(policy_id)
    
    if rego_code is None:
        raise HTTPException(status_code=404, detail=f"No Rego found for policy: {policy_id}")
    
    return {
        "policy_id": policy_id,
        "rego_code": rego_code,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/rego/{policy_id}/download", tags=["Rego Management"])
async def download_rego(policy_id: str):
    """Download Rego file for a specific policy ID"""
    metadata = load_metadata()
    
    filename = None
    for fname, file_meta in metadata.get("files", {}).items():
        if policy_id in file_meta.get("policy_ids", []):
            filename = fname
            break
    
    if filename is None:
        raise HTTPException(status_code=404, detail=f"No Rego file found for policy: {policy_id}")
    
    rego_path = REGO_STORAGE_DIR / filename
    if not rego_path.exists():
        raise HTTPException(status_code=404, detail=f"Rego file not found: {filename}")
    
    return FileResponse(
        path=str(rego_path),
        media_type="text/plain",
        filename=filename
    )


@app.get("/rego/files/list", response_model=List[RegoFile], tags=["Rego Management"])
async def list_rego_files():
    """List all stored Rego files with metadata"""
    metadata = load_metadata()
    
    files = []
    for filename, file_meta in metadata.get("files", {}).items():
        files.append(RegoFile(
            filename=filename,
            policy_ids=file_meta.get("policy_ids", []),
            created_at=file_meta.get("created_at", ""),
            updated_at=file_meta.get("updated_at", ""),
            size_bytes=file_meta.get("size_bytes", 0)
        ))
    
    return files


@app.delete("/rego/{policy_id}", tags=["Rego Management"])
async def delete_rego(policy_id: str):
    """Delete Rego rules for a specific policy ID"""
    metadata = load_metadata()
    
    filename = None
    for fname, file_meta in metadata.get("files", {}).items():
        if policy_id in file_meta.get("policy_ids", []):
            filename = fname
            break
    
    if filename is None:
        raise HTTPException(status_code=404, detail=f"No Rego found for policy: {policy_id}")
    
    file_meta = metadata["files"][filename]
    policy_ids = file_meta.get("policy_ids", [])
    
    if len(policy_ids) == 1:
        # Delete entire file
        rego_path = REGO_STORAGE_DIR / filename
        if rego_path.exists():
            rego_path.unlink()
        del metadata["files"][filename]
        save_metadata(metadata)
        
        return {
            "message": f"Deleted Rego file: {filename}",
            "policy_id": policy_id
        }
    else:
        # Remove policy from metadata
        policy_ids.remove(policy_id)
        file_meta["policy_ids"] = policy_ids
        file_meta["updated_at"] = datetime.utcnow().isoformat()
        save_metadata(metadata)
        
        return {
            "message": f"Removed policy {policy_id} from file {filename}",
            "policy_id": policy_id,
            "remaining_policies": policy_ids
        }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("SERVER_PORT", "8000"))
    uvicorn.run(
        "src.api.fastapi_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )