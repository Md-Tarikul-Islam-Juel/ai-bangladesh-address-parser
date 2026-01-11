#!/usr/bin/env python3
"""
Batch Processing Script
=======================

Process your entire dataset using the production pipeline

Usage:
    python batch_process.py \
        --input "../Processed data/merged_addresses.json" \
        --output "output/processed_addresses.json" \
        --detailed

Author: Senior ML Scientist
"""

import argparse
import json
from pathlib import Path
import time
import sys

sys.path.insert(0, str(Path(__file__).parent))
from complete_production_system import ProductionAddressExtractor


def main():
    parser = argparse.ArgumentParser(description='Batch process addresses')
    parser.add_argument('--input', required=True,
                       help='Input JSON file (merged_addresses.json)')
    parser.add_argument('--output', required=True,
                       help='Output JSON file')
    parser.add_argument('--detailed', action='store_true',
                       help='Include detailed metadata')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of addresses to process')
    
    args = parser.parse_args()
    
    # Load input data
    print(f"Loading data from {args.input}...")
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if args.limit:
        data = data[:args.limit]
    
    print(f"✓ Loaded {len(data)} addresses")
    print()
    
    # Initialize extractor
    print("Initializing production system...")
    extractor = ProductionAddressExtractor(data_path=args.input)
    print()
    
    # Process all addresses
    print("=" * 80)
    print("BATCH PROCESSING")
    print("=" * 80)
    print()
    
    results = []
    start_time = time.time()
    
    for i, record in enumerate(data, 1):
        if i % 100 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed
            remaining = (len(data) - i) / rate if rate > 0 else 0
            print(f"  Processed {i}/{len(data)} ({i/len(data)*100:.1f}%) - "
                  f"Rate: {rate:.1f} addr/s - "
                  f"ETA: {remaining:.0f}s")
        
        address = record.get('address', '')
        extracted = extractor.extract(address, detailed=args.detailed)
        
        # Keep original ID
        result = {
            'id': record.get('id', i),
            'address': address,
            'extracted': extracted['components'],
            'confidence': extracted['overall_confidence'],
            'extraction_time_ms': extracted['extraction_time_ms']
        }
        
        if args.detailed and 'metadata' in extracted:
            result['metadata'] = extracted['metadata']
        
        results.append(result)
    
    total_time = time.time() - start_time
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 80)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 80)
    print(f"Total processed: {len(results)}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time: {total_time/len(results)*1000:.2f}ms per address")
    print(f"Throughput: {len(results)/total_time:.1f} addresses/second")
    print(f"Output saved to: {output_path}")
    print()
    
    # Statistics
    stats = extractor.get_statistics()
    print("System Statistics:")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
