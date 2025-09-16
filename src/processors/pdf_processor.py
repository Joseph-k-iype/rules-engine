"""
PDF processing functionality with dynamic chunking for large files.
CORRECTED VERSION with proper PDF availability export.
"""
import os
import math
import logging
from typing import List, Dict, Union

from ..models.base_models import DocumentChunk, CountryMetadata
from ..config import Config

logger = logging.getLogger(__name__)

# PDF processing imports - CORRECTED to match original pattern
try:
    import pymupdf  # Modern PyMuPDF
    PDF_AVAILABLE = True
    print("PyMuPDF available for PDF processing")
except ImportError:
    try:
        import pdfplumber
        PDF_AVAILABLE = True
        print("pdfplumber available for PDF processing")
    except ImportError:
        PDF_AVAILABLE = False
        print("Warning: No PDF library found. Install PyMuPDF or pdfplumber: pip install PyMuPDF pdfplumber")


class PDFProcessor:
    """Enhanced PDF processor with dynamic chunking for large files."""

    @staticmethod
    def get_file_size(filepath: str) -> int:
        """Get file size in bytes."""
        return os.path.getsize(filepath)

    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """Extract text from PDF file."""
        if not PDF_AVAILABLE:
            raise ImportError("No PDF library available. Install PyMuPDF or pdfplumber")

        try:
            # Check which library is available and use it
            try:
                import pymupdf
                return PDFProcessor._extract_with_pymupdf(pdf_path)
            except ImportError:
                try:
                    import pdfplumber
                    return PDFProcessor._extract_with_pdfplumber(pdf_path)
                except ImportError:
                    raise ImportError("No PDF library available")
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            raise

    @staticmethod
    def _extract_with_pymupdf(pdf_path: str) -> str:
        """Extract text using modern PyMuPDF."""
        import pymupdf
        text = ""
        try:
            with pymupdf.open(pdf_path) as doc:
                for page in doc:
                    page_text = page.get_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            raise
        return text

    @staticmethod
    def _extract_with_pdfplumber(pdf_path: str) -> str:
        """Extract text using pdfplumber."""
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    @staticmethod
    def chunk_text(text: str, chunk_size: int = Config.CHUNK_SIZE, overlap_size: int = Config.OVERLAP_SIZE) -> List[DocumentChunk]:
        """Dynamically chunk text based on size with overlaps."""
        if len(text) <= chunk_size:
            return [DocumentChunk(text, 0, 1, 0, len(text))]

        chunks = []
        start = 0
        chunk_index = 0

        # Calculate total chunks
        total_chunks = math.ceil(len(text) / (chunk_size - overlap_size))

        while start < len(text):
            # Calculate end position
            end = min(start + chunk_size, len(text))

            # Try to break at sentence boundaries if possible
            if end < len(text):
                # Look for sentence endings within the last 200 characters
                search_start = max(end - 200, start)
                sentence_endings = ['.', '!', '?', '\n\n']

                best_break = -1
                for ending in sentence_endings:
                    pos = text.rfind(ending, search_start, end)
                    if pos > best_break:
                        best_break = pos + 1

                if best_break > start:
                    end = best_break

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunk = DocumentChunk(chunk_content, chunk_index, total_chunks, start, end)
                chunks.append(chunk)
                chunk_index += 1

            # Move start position with overlap
            if end >= len(text):
                break
            start = max(end - overlap_size, start + 1)

        return chunks

    @staticmethod
    def should_chunk_file(filepath: str) -> bool:
        """Determine if file should be chunked based on size."""
        file_size = PDFProcessor.get_file_size(filepath)
        return file_size > Config.MAX_FILE_SIZE


class MultiLevelPDFProcessor:
    """Process PDFs from multiple document levels with chunking support."""

    def __init__(self):
        self.pdf_processor = PDFProcessor()

    def process_country_documents(self, entry_id: str, metadata: CountryMetadata, base_path: str) -> Dict[str, Union[str, List[DocumentChunk]]]:
        """Process all documents for a country entry with dynamic chunking."""
        documents = {}

        # Process all available levels
        level_files = {
            "level_1": metadata.file_level_1,
            "level_2": metadata.file_level_2,
            "level_3": metadata.file_level_3
        }

        for level, filename in level_files.items():
            if filename:
                file_path = os.path.join(base_path, filename)
                if os.path.exists(file_path):
                    try:
                        text = self.pdf_processor.extract_text_from_pdf(file_path)

                        # Check if chunking is needed
                        if self.pdf_processor.should_chunk_file(file_path):
                            logger.info(f"Chunking {level} document: {filename}")
                            chunks = self.pdf_processor.chunk_text(text)
                            documents[level] = chunks
                        else:
                            documents[level] = text

                        logger.info(f"Processed {level} document: {filename}")
                    except Exception as e:
                        logger.error(f"Error processing {level} document {filename}: {e}")
                else:
                    logger.warning(f"{level} document not found: {file_path}")

        return documents


# Export PDF_AVAILABLE for use in other modules
__all__ = ['PDFProcessor', 'MultiLevelPDFProcessor', 'PDF_AVAILABLE']
