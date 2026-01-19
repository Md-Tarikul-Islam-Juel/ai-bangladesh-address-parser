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
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.core import ProductionAddressExtractor
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
_current_thresholds = None

def get_extractor(component_thresholds=None):
    """Get or create the extractor instance"""
    global _extractor, _current_thresholds
    
    # Recreate extractor if thresholds changed or extractor doesn't exist
    thresholds_changed = (
        component_thresholds is not None and 
        component_thresholds != _current_thresholds
    )
    
    if _extractor is None or thresholds_changed:
        # Suppress ALL print statements during initialization
        # Redirect stdout to stderr before creating extractor
        import sys
        import io
        
        old_stdout = sys.stdout
        sys.stdout = sys.stderr  # All prints go to stderr
        
        try:
            # Try to find data file
            data_path = Path(__file__).parent.parent.parent / "data" / "raw" / "merged_addresses.json"
            if data_path.exists():
                _extractor = ProductionAddressExtractor(
                    data_path=str(data_path),
                    component_thresholds=component_thresholds
                )
            else:
                _extractor = ProductionAddressExtractor(
                    component_thresholds=component_thresholds
                )
            _current_thresholds = component_thresholds
        finally:
            # Restore stdout
            sys.stdout = old_stdout
    
    return _extractor

def main():
    """Main entry point for Python script"""
    try:
        # Parse command and arguments
        if len(sys.argv) < 2:
            error_output = json.dumps({
                "error": "No command provided",
                "components": {},
                "overall_confidence": 0.0,
                "extraction_time_ms": 0,
                "normalized_address": "",
                "original_address": ""
            })
            print(error_output, file=sys.stdout)
            sys.exit(1)
        
        command = sys.argv[1]
        
        # Parse component thresholds if provided
        component_thresholds = None
        if '--thresholds' in sys.argv:
            try:
                thresholds_idx = sys.argv.index('--thresholds')
                if thresholds_idx + 1 < len(sys.argv):
                    thresholds_json = sys.argv[thresholds_idx + 1]
                    component_thresholds = json.loads(thresholds_json)
            except (ValueError, json.JSONDecodeError) as e:
                pass
        
        # Suppress any print statements from the extractor
        old_stdout = sys.stdout
        sys.stdout = sys.stderr
        
        try:
            extractor = get_extractor(component_thresholds=component_thresholds)
            
            # Route to appropriate method based on command
            if command == 'extract':
                address = sys.argv[2] if len(sys.argv) > 2 else ""
                detailed = '--detailed' in sys.argv
                result = extractor.extract(address, detailed=detailed)
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
            
            elif command == 'validate':
                address = sys.argv[2] if len(sys.argv) > 2 else ""
                required = None
                if '--required' in sys.argv:
                    req_idx = sys.argv.index('--required')
                    if req_idx + 1 < len(sys.argv):
                        required = sys.argv[req_idx + 1].split(',')
                output = extractor.validate(address, required)
            
            elif command == 'format':
                address = sys.argv[2] if len(sys.argv) > 2 else ""
                style = 'full'
                separator = ', '
                include_postal = True
                if '--style' in sys.argv:
                    style_idx = sys.argv.index('--style')
                    if style_idx + 1 < len(sys.argv):
                        style = sys.argv[style_idx + 1]
                if '--separator' in sys.argv:
                    sep_idx = sys.argv.index('--separator')
                    if sep_idx + 1 < len(sys.argv):
                        separator = sys.argv[sep_idx + 1]
                if '--no-postal' in sys.argv:
                    include_postal = False
                formatted = extractor.format(address, style, separator, include_postal)
                output = {"formatted": formatted}
            
            elif command == 'compare':
                address1 = sys.argv[2] if len(sys.argv) > 2 else ""
                address2 = sys.argv[3] if len(sys.argv) > 3 else ""
                output = extractor.compare(address1, address2)
            
            elif command == 'suggest':
                query = sys.argv[2] if len(sys.argv) > 2 else ""
                limit = 5
                if '--limit' in sys.argv:
                    limit_idx = sys.argv.index('--limit')
                    if limit_idx + 1 < len(sys.argv):
                        limit = int(sys.argv[limit_idx + 1])
                suggestions = extractor.suggest(query, limit)
                output = {"suggestions": suggestions}
            
            elif command == 'enrich':
                address = sys.argv[2] if len(sys.argv) > 2 else ""
                output = extractor.enrich(address)
            
            elif command == 'statistics':
                # Read addresses from stdin or args
                addresses = []
                if len(sys.argv) > 2:
                    # Addresses as JSON array in args
                    addresses_json = sys.argv[2]
                    addresses = json.loads(addresses_json)
                else:
                    # Read from stdin
                    stdin_data = sys.stdin.read()
                    if stdin_data:
                        addresses = json.loads(stdin_data)
                stats = extractor.get_statistics(addresses)
                output = {"statistics": stats}
            
            else:
                # Default: treat as extract command for backward compatibility
                address = command
                detailed = '--detailed' in sys.argv
                result = extractor.extract(address, detailed=detailed)
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
        
        finally:
            sys.stdout = old_stdout
        
        # Output JSON to stdout
        print(json.dumps(output, ensure_ascii=False), file=sys.stdout)
        sys.stdout.flush()
        
    except Exception as e:
        error_output = json.dumps({
            "error": str(e),
            "components": {},
            "overall_confidence": 0.0,
            "extraction_time_ms": 0,
            "normalized_address": "",
            "original_address": sys.argv[2] if len(sys.argv) > 2 else ""
        })
        print(error_output, file=sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()
