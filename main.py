"""
Main execution script for PDF to ODRL conversion.
Aligned with CSV to ODRL output format - NO TRUNCATION.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from src.analyzer import LegislationAnalyzer
from src.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main execution function for PDF to ODRL conversion."""

    analyzer = LegislationAnalyzer()

    try:
        print("\n" + "="*80)
        print("PDF TO ODRL CONVERTER")
        print("Aligned with CSV to ODRL output format - NO TRUNCATION")
        print("="*80 + "\n")

        # Show metadata configuration
        print("📋 METADATA CONFIGURATION:")
        processing_entries = analyzer.metadata_manager.get_all_processing_entries()
        if processing_entries:
            print(f"✅ Configured entries: {len(processing_entries)}")
            for entry_id, metadata in processing_entries:
                print(f"   📂 {entry_id}:")
                print(f"      🌍 Countries: {', '.join(metadata.country)}")
                if metadata.adequacy_country:
                    print(f"      🤝 Adequacy: {', '.join(metadata.adequacy_country)}")
                if metadata.file_level_1:
                    print(f"      📄 Level 1: {metadata.file_level_1}")
                if metadata.file_level_2:
                    print(f"      📖 Level 2: {metadata.file_level_2}")
                if metadata.file_level_3:
                    print(f"      📘 Level 3: {metadata.file_level_3}")
                print()
        else:
            print("⚠️ No configured entries found in legislation_metadata.json")
            print("Please create config/legislation_metadata.json with your configuration")
            return

        print(f"🔧 Config file: {Config.METADATA_CONFIG_FILE}")
        print(f"📏 Chunk size: {Config.CHUNK_SIZE} chars, Overlap: {Config.OVERLAP_SIZE} chars")
        print(f"📦 Chunking threshold: {Config.MAX_FILE_SIZE / (1024*1024):.1f} MB")
        print()

        # Check PDF processing availability
        try:
            from src.processors.pdf_processor import PDF_AVAILABLE
            if not PDF_AVAILABLE:
                print("⚠️ Warning: PDF processing libraries not available.")
                print("Install with: pip install PyMuPDF pdfplumber")
                return
        except ImportError:
            print("⚠️ Warning: PDF processor not available.")
            return

        # Process all PDFs and convert to ODRL format
        print("🚀 Starting PDF to ODRL conversion...")
        print("-"*80 + "\n")
        
        result = await analyzer.process_legislation_folder_to_odrl()

        # Save ODRL policies to output file
        if result.get('policies'):
            output_dir = Path("./odrl_output")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"pdf_odrl_policies_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result['policies'], f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ ODRL policies saved to: {output_file}")
            print(f"   Total policies: {len(result['policies'])}")
            print(f"   Processing time: {result['processing_time']:.2f}s")
            
            # Print summary
            print("\n" + "="*80)
            print("CONVERSION SUMMARY")
            print("="*80)
            print(f"Total Entries:      {len(result['documents_processed'])}")
            print(f"Successful:         {result['successful']}")
            print(f"Failed:             {result['failed']}")
            print(f"Total Policies:     {len(result['policies'])}")
            print(f"Processing Time:    {result['processing_time']:.2f}s")
            print()
            
            # Analyze policies
            total_permissions = sum(len(p.get('permission', [])) for p in result['policies'])
            total_prohibitions = sum(len(p.get('prohibition', [])) for p in result['policies'])
            
            print(f"Total Permissions:  {total_permissions}")
            print(f"Total Prohibitions: {total_prohibitions}")
            print()
            
            # Framework breakdown
            frameworks = {}
            for policy in result['policies']:
                fw = policy.get('custom:framework', 'Unknown')
                frameworks[fw] = frameworks.get(fw, 0) + 1
            
            print("By Framework:")
            for fw, count in frameworks.items():
                print(f"  {fw}: {count}")
            print()
            
            # Type breakdown
            types = {}
            for policy in result['policies']:
                t = policy.get('custom:type', 'Unknown')
                types[t] = types.get(t, 0) + 1
            
            print("By Type:")
            for t, count in types.items():
                print(f"  {t}: {count}")
            
            print("="*80)
            
        else:
            print("\n⚠️ No policies generated")

    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code if exit_code else 0)