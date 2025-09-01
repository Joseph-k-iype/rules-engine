"""
PDF processing module for extracting text from legislation documents.
Supports multiple PDF libraries and provides robust text extraction with error handling.
"""

import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import hashlib
from datetime import datetime

from .config import Config
from .models import ProcessingStatus
from .event_system import Event, event_bus

# PDF processing libraries
try:
    import pymupdf  # Modern PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# Check if any PDF library is available
PDF_AVAILABLE = PYMUPDF_AVAILABLE or PDFPLUMBER_AVAILABLE

logger = logging.getLogger(__name__)

class PDFMetadata:
    """Metadata extracted from PDF documents."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_size = 0
        self.page_count = 0
        self.title = ""
        self.author = ""
        self.subject = ""
        self.creator = ""
        self.producer = ""
        self.creation_date = None
        self.modification_date = None
        self.encrypted = False
        self.text_extractable = True
        self.extraction_method = ""
        self.checksum = ""
        
        # Calculate basic file metadata
        if file_path.exists():
            self.file_size = file_path.stat().st_size
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate MD5 checksum of the file."""
        try:
            with open(self.file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

class PDFProcessor:
    """PDF processor for extracting text from legislation documents."""
    
    def __init__(self):
        self.processed_files: Dict[str, PDFMetadata] = {}
        self.extraction_cache: Dict[str, str] = {}  # checksum -> extracted text
        
        if not PDF_AVAILABLE:
            logger.warning("No PDF processing libraries available. Install PyMuPDF or pdfplumber.")
    
    async def extract_text_from_file(self, pdf_path: Path, use_cache: bool = True) -> Tuple[str, PDFMetadata]:
        """Extract text from a single PDF file with metadata."""
        if not PDF_AVAILABLE:
            raise ImportError("No PDF library available. Install PyMuPDF or pdfplumber")
        
        # Create metadata object
        metadata = PDFMetadata(pdf_path)
        
        try:
            # Check cache if enabled
            if use_cache and metadata.checksum in self.extraction_cache:
                logger.debug(f"Using cached extraction for {pdf_path.name}")
                return self.extraction_cache[metadata.checksum], metadata
            
            logger.info(f"Extracting text from: {pdf_path}")
            
            # Publish extraction start event
            await event_bus.publish_event(Event(
                event_type="pdf_extraction_started",
                data={
                    "file_path": str(pdf_path),
                    "file_size": metadata.file_size,
                    "checksum": metadata.checksum
                },
                source="pdf_processor"
            ))
            
            # Try extraction with preferred method first
            text = ""
            if PYMUPDF_AVAILABLE:
                text, metadata = await self._extract_with_pymupdf(pdf_path, metadata)
            elif PDFPLUMBER_AVAILABLE:
                text, metadata = await self._extract_with_pdfplumber(pdf_path, metadata)
            else:
                raise ImportError("No PDF processing library available")
            
            # Cache the result
            if use_cache and text:
                self.extraction_cache[metadata.checksum] = text
            
            # Store metadata
            self.processed_files[str(pdf_path)] = metadata
            
            # Publish extraction complete event
            await event_bus.publish_event(Event(
                event_type="pdf_extraction_completed",
                data={
                    "file_path": str(pdf_path),
                    "text_length": len(text),
                    "page_count": metadata.page_count,
                    "extraction_method": metadata.extraction_method
                },
                source="pdf_processor"
            ))
            
            logger.info(f"Extracted {len(text)} characters from {metadata.page_count} pages")
            return text, metadata
            
        except Exception as e:
            metadata.text_extractable = False
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            
            # Publish extraction error event
            await event_bus.publish_event(Event(
                event_type="pdf_extraction_failed",
                data={
                    "file_path": str(pdf_path),
                    "error": str(e)
                },
                source="pdf_processor"
            ))
            
            raise
    
    async def _extract_with_pymupdf(self, pdf_path: Path, metadata: PDFMetadata) -> Tuple[str, PDFMetadata]:
        """Extract text using modern PyMuPDF with context manager."""
        text = ""
        
        try:
            # Use modern PyMuPDF API with context manager
            with pymupdf.open(pdf_path) as doc:
                metadata.page_count = len(doc)
                metadata.encrypted = doc.needs_pass
                metadata.extraction_method = "pymupdf"
                
                # Extract document metadata
                doc_metadata = doc.metadata
                if doc_metadata:
                    metadata.title = doc_metadata.get("title", "")
                    metadata.author = doc_metadata.get("author", "")
                    metadata.subject = doc_metadata.get("subject", "")
                    metadata.creator = doc_metadata.get("creator", "")
                    metadata.producer = doc_metadata.get("producer", "")
                    
                    # Handle dates
                    if "creationDate" in doc_metadata:
                        try:
                            metadata.creation_date = doc_metadata["creationDate"]
                        except:
                            pass
                    
                    if "modDate" in doc_metadata:
                        try:
                            metadata.modification_date = doc_metadata["modDate"]
                        except:
                            pass
                
                # Extract text from all pages
                for page_num, page in enumerate(doc):
                    try:
                        page_text = page.get_text()
                        if page_text:
                            text += f"\n--- Page {page_num + 1} ---\n"
                            text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            raise
        
        return text.strip(), metadata
    
    async def _extract_with_pdfplumber(self, pdf_path: Path, metadata: PDFMetadata) -> Tuple[str, PDFMetadata]:
        """Extract text using pdfplumber."""
        text = ""
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata.page_count = len(pdf.pages)
                metadata.extraction_method = "pdfplumber"
                
                # Extract document metadata
                if hasattr(pdf, 'metadata') and pdf.metadata:
                    doc_metadata = pdf.metadata
                    metadata.title = doc_metadata.get("/Title", "")
                    metadata.author = doc_metadata.get("/Author", "")
                    metadata.subject = doc_metadata.get("/Subject", "")
                    metadata.creator = doc_metadata.get("/Creator", "")
                    metadata.producer = doc_metadata.get("/Producer", "")
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num + 1} ---\n"
                            text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"PDFPlumber extraction failed: {e}")
            raise
        
        return text.strip(), metadata
    
    async def process_directory(self, directory_path: Path, pattern: str = "*.pdf") -> Dict[str, Tuple[str, PDFMetadata]]:
        """Process all PDF files in a directory."""
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        pdf_files = list(directory_path.glob(pattern))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory_path} with pattern {pattern}")
            return {}
        
        logger.info(f"Processing {len(pdf_files)} PDF files from {directory_path}")
        
        results = {}
        
        # Process files with controlled concurrency
        semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_PROCESSES)
        
        async def process_single_file(file_path):
            async with semaphore:
                try:
                    text, metadata = await self.extract_text_from_file(file_path)
                    return file_path.name, (text, metadata)
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    return file_path.name, (None, None)
        
        # Process all files concurrently
        tasks = [process_single_file(pdf_file) for pdf_file in pdf_files]
        processed_results = await asyncio.gather(*tasks)
        
        # Collect successful results
        for filename, (text, metadata) in processed_results:
            if text is not None and metadata is not None:
                results[filename] = (text, metadata)
        
        logger.info(f"Successfully processed {len(results)}/{len(pdf_files)} PDF files")
        return results
    
    async def get_pdf_files(self, directory_path: Path) -> List[Path]:
        """Get all PDF files from directory."""
        if not directory_path.exists():
            return []
        
        return list(directory_path.glob("*.pdf"))
    
    def get_processed_files(self) -> Dict[str, PDFMetadata]:
        """Get metadata for all processed files."""
        return self.processed_files.copy()
    
    def get_file_metadata(self, file_path: Path) -> Optional[PDFMetadata]:
        """Get metadata for a specific file."""
        return self.processed_files.get(str(file_path))
    
    def clear_cache(self):
        """Clear the extraction cache."""
        self.extraction_cache.clear()
        logger.info("PDF extraction cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_files": len(self.extraction_cache),
            "total_cached_characters": sum(len(text) for text in self.extraction_cache.values()),
            "processed_files": len(self.processed_files),
            "pymupdf_available": PYMUPDF_AVAILABLE,
            "pdfplumber_available": PDFPLUMBER_AVAILABLE
        }
    
    async def validate_pdf_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a PDF file and check if it's processable."""
        validation_result = {
            "valid": False,
            "readable": False,
            "encrypted": False,
            "page_count": 0,
            "file_size": 0,
            "errors": []
        }
        
        if not file_path.exists():
            validation_result["errors"].append("File does not exist")
            return validation_result
        
        validation_result["file_size"] = file_path.stat().st_size
        
        if validation_result["file_size"] == 0:
            validation_result["errors"].append("File is empty")
            return validation_result
        
        # Try to open and validate the PDF
        try:
            if PYMUPDF_AVAILABLE:
                with pymupdf.open(file_path) as doc:
                    validation_result["valid"] = True
                    validation_result["page_count"] = len(doc)
                    validation_result["encrypted"] = doc.needs_pass
                    
                    if not validation_result["encrypted"]:
                        # Try to extract text from first page
                        if len(doc) > 0:
                            try:
                                first_page_text = doc[0].get_text()
                                validation_result["readable"] = len(first_page_text.strip()) > 0
                            except:
                                validation_result["readable"] = False
            
            elif PDFPLUMBER_AVAILABLE:
                with pdfplumber.open(file_path) as pdf:
                    validation_result["valid"] = True
                    validation_result["page_count"] = len(pdf.pages)
                    
                    # Try to extract text from first page
                    if len(pdf.pages) > 0:
                        try:
                            first_page_text = pdf.pages[0].extract_text()
                            validation_result["readable"] = first_page_text is not None and len(first_page_text.strip()) > 0
                        except:
                            validation_result["readable"] = False
            
            else:
                validation_result["errors"].append("No PDF processing library available")
        
        except Exception as e:
            validation_result["errors"].append(f"PDF validation error: {str(e)}")
        
        return validation_result
    
    async def extract_document_structure(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract document structure information (headings, sections, etc.)."""
        structure = {
            "headings": [],
            "sections": [],
            "page_breaks": [],
            "font_sizes": {},
            "text_blocks": []
        }
        
        if not PYMUPDF_AVAILABLE:
            logger.warning("Document structure extraction requires PyMuPDF")
            return structure
        
        try:
            with pymupdf.open(pdf_path) as doc:
                for page_num, page in enumerate(doc):
                    # Get text with font information
                    blocks = page.get_text("dict")
                    
                    for block in blocks.get("blocks", []):
                        if block.get("type") == 0:  # Text block
                            for line in block.get("lines", []):
                                for span in line.get("spans", []):
                                    font_size = span.get("size", 0)
                                    text = span.get("text", "").strip()
                                    
                                    if text:
                                        # Track font sizes
                                        font_size = round(font_size, 1)
                                        structure["font_sizes"][font_size] = structure["font_sizes"].get(font_size, 0) + 1
                                        
                                        # Identify potential headings (larger font sizes, short text)
                                        if font_size > 12 and len(text) < 100 and not text.endswith('.'):
                                            structure["headings"].append({
                                                "text": text,
                                                "page": page_num + 1,
                                                "font_size": font_size
                                            })
                                        
                                        # Identify sections (numbered or lettered items)
                                        if any(text.startswith(prefix) for prefix in ["Article ", "Section ", "Chapter ", "Part "]):
                                            structure["sections"].append({
                                                "text": text,
                                                "page": page_num + 1,
                                                "font_size": font_size
                                            })
                    
                    # Track page breaks
                    structure["page_breaks"].append(page_num + 1)
        
        except Exception as e:
            logger.error(f"Error extracting document structure: {e}")
        
        return structure
    
    def is_pdf_processing_available(self) -> bool:
        """Check if PDF processing is available."""
        return PDF_AVAILABLE
    
    def get_available_libraries(self) -> List[str]:
        """Get list of available PDF processing libraries."""
        libraries = []
        if PYMUPDF_AVAILABLE:
            libraries.append("PyMuPDF")
        if PDFPLUMBER_AVAILABLE:
            libraries.append("pdfplumber")
        return libraries

# Global PDF processor instance
pdf_processor = None

async def initialize_pdf_processor() -> PDFProcessor:
    """Initialize the global PDF processor."""
    global pdf_processor
    pdf_processor = PDFProcessor()
    logger.info(f"PDF processor initialized with libraries: {pdf_processor.get_available_libraries()}")
    return pdf_processor

def get_pdf_processor() -> PDFProcessor:
    """Get the global PDF processor instance."""
    return pdf_processor

def is_pdf_processing_available() -> bool:
    """Check if PDF processing is available globally."""
    return PDF_AVAILABLE