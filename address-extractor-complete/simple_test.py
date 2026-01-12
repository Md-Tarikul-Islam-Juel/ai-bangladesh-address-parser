#!/usr/bin/env python3
"""
Simple Test Script for Address Extractor
=========================================
Usage: python3 simple_test.py
"""

from production_address_extractor import ProductionAddressExtractor
import json

# Initialize extractor (automatically uses trained spaCy if available)
print("Loading extractor...")
extractor = ProductionAddressExtractor(
    data_path="../main/Processed data/merged_addresses.json"
)
print("✓ Ready!\n")

# Test address
test_address = 'sottota tower, h:107/2,R:7, north bishil, mirpur 1, dhaka 1217'

print("="*80)
print("Testing Address:")
print(test_address)
print("="*80)

# Extract
result = extractor.extract(test_address)

# Show results
print(f"\n✅ Confidence: {result['overall_confidence']:.1%}")
print(f"⏱️  Time: {result['extraction_time_ms']:.2f}ms")

print("\n📦 Extracted Components:")
for component, value in result['components'].items():
    if value:
        print(f"  {component:15} = {value}")

print("\n" + "="*80)
print("WANT TO TEST MORE ADDRESSES? Edit this file and add to the list below:")
print("="*80)

# Add more test addresses here
more_tests = [
    'House 12, Road 5, Dhanmondi, Dhaka-1209',
    'Flat A-3, Building 7, Bashundhara R/A, Dhaka',
]

if more_tests:
    print("\nTesting additional addresses...\n")
    for i, addr in enumerate(more_tests, 1):
        print(f"{i}. {addr}")
        result = extractor.extract(addr)
        print(f"   ✅ {result['overall_confidence']:.0%} confidence")
        components = {k: v for k, v in result['components'].items() if v}
        print(f"   Found: {list(components.keys())}\n")

# Show statistics
print("="*80)
print("SYSTEM STATISTICS")
print("="*80)
stats = extractor.stats
print(f"Total Processed: {stats['total_processed']}")
print(f"Total Time: {stats['total_time_ms']:.2f}ms")
print(f"Errors: {stats['errors']}")
if stats['total_processed'] > 0:
    print(f"Avg Time/Address: {stats['total_time_ms'] / stats['total_processed']:.2f}ms")
