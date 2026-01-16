#!/usr/bin/env python3
"""
Python API for Address Extraction
Called by Node.js via python-shell
"""

import sys
import json
import os
from pathlib import Path

# Suppress all stdout logging - only output JSON to stdout
# Redirect logging to stderr so it doesn't interfere with JSON output
import logging
import os

# Suppress print statements by redirecting stdout to stderr
# This ensures only JSON goes to stdout
class SuppressPrint:
    """Context manager to suppress print statements"""
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = sys.stderr
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Send logs to stderr, not stdout
)

# Add parent directory and src directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.core.production_address_extractor import ProductionAddressExtractor
except ImportError as e:
    error_output = json.dumps({
        "error": f"Import error: {str(e)}",
        "components": {},
        "overall_confidence": 0.0,
        "extraction_time_ms": 0,
        "normalized_address": "",
        "original_address": ""
    })
    print(error_output, file=sys.stdout)
    sys.exit(1)

# Initialize extractor (singleton pattern)
_extractor = None

def get_extractor():
    """Get or create the extractor instance"""
    global _extractor
    if _extractor is None:
        # Suppress ALL print statements during initialization
        # Redirect stdout to stderr before creating extractor
        import sys
        import io
        
        old_stdout = sys.stdout
        sys.stdout = sys.stderr  # All prints go to stderr
        
        try:
            # Try to find data file
            data_path = Path(__file__).parent.parent / "data" / "merged_addresses.json"
            if data_path.exists():
                _extractor = ProductionAddressExtractor(data_path=str(data_path))
            else:
                _extractor = ProductionAddressExtractor()
        finally:
            # Restore stdout
            sys.stdout = old_stdout
    
    return _extractor

def main():
    """Main entry point for Python script"""
    try:
        # Get address from command line args
        if len(sys.argv) < 2:
            error_output = json.dumps({
                "error": "No address provided",
                "components": {},
                "overall_confidence": 0.0,
                "extraction_time_ms": 0,
                "normalized_address": "",
                "original_address": ""
            })
            print(error_output, file=sys.stdout)
            sys.exit(1)
        
        address = sys.argv[1]
        detailed = '--detailed' in sys.argv
        
        # Suppress any print statements from the extractor
        # Redirect stdout to stderr during extraction
        old_stdout = sys.stdout
        sys.stdout = sys.stderr  # All prints go to stderr
        
        try:
            # Extract components (any print statements will go to stderr)
            extractor = get_extractor()
            result = extractor.extract(address, detailed=detailed)
        finally:
            # Restore stdout for JSON output
            sys.stdout = old_stdout
        
        # Convert to JSON-serializable format
        output = {
            "components": result.get('components', {}),
            "overall_confidence": result.get('overall_confidence', 0.0),
            "extraction_time_ms": result.get('extraction_time_ms', 0),
            "normalized_address": result.get('normalized_address', ''),
            "original_address": result.get('original_address', address),
        }
        
        if 'cached' in result:
            output['cached'] = result['cached']
        
        if detailed and 'metadata' in result:
            output['metadata'] = result['metadata']
        
        # Output JSON to stdout (only JSON, no other text)
        print(json.dumps(output, ensure_ascii=False), file=sys.stdout)
        sys.stdout.flush()  # Ensure output is sent
        
    except Exception as e:
        error_output = json.dumps({
            "error": str(e),
            "components": {},
            "overall_confidence": 0.0,
            "extraction_time_ms": 0,
            "normalized_address": "",
            "original_address": sys.argv[1] if len(sys.argv) > 1 else ""
        })
        print(error_output, file=sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()
