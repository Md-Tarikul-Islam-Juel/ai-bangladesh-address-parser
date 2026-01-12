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

# Test addresses (Array/List)
test_addresses = [
    '105/A, Central Road, Hatirpool, Dhaka',
    'House 12, Road 5, Dhanmondi, Dhaka-1209',
    'Flat A-3, Building 7, Bashundhara R/A, Dhaka',
    '1152/C "Greenhouse", House# 45, Road# 08, Shapla Residential Area, Halishahar, Chittagong-4219'
]

print("="*80)
print(f"Testing {len(test_addresses)} Addresses")
print("="*80)
print()

# Process all addresses
results = []
for i, address in enumerate(test_addresses, 1):
    print(f"[{i}/{len(test_addresses)}] Address: {address}")
    print("-" * 80)
    
    result = extractor.extract(address)
    results.append(result)
    
    # Show confidence and time
    print(f"Confidence: {result['overall_confidence']:.1%} | Time: {result['extraction_time_ms']:.2f}ms")
    
    # Show components - each on separate line
    components = result['components']
    print("Result:")
    
    found_any = False
    if components.get('flat_number'):
        print(f"  flat = {components['flat_number']}")
        found_any = True
    if components.get('house_number'):
        print(f"  house = {components['house_number']}")
        found_any = True
    if components.get('floor_number'):
        print(f"  floor = {components['floor_number']}")
        found_any = True
    if components.get('road'):
        print(f"  road = {components['road']}")
        found_any = True
    if components.get('block_number'):
        print(f"  block = {components['block_number']}")
        found_any = True
    if components.get('area'):
        print(f"  area = {components['area']}")
        found_any = True
    if components.get('district'):
        print(f"  district = {components['district']}")
        found_any = True
    if components.get('division'):
        print(f"  division = {components['division']}")
        found_any = True
    if components.get('postal_code'):
        print(f"  postal = {components['postal_code']}")
        found_any = True
    
    if not found_any:
        print("  (no components extracted)")
    
    print()

# Optional: Add more test addresses here if needed
# Uncomment the code below to test multiple addresses at once
#
# more_tests = [
#     'House 12, Road 5, Dhanmondi, Dhaka-1209',
#     'Flat A-3, Building 7, Bashundhara R/A, Dhaka',
# ]
#
# if more_tests:
#     print("\n" + "="*80)
#     print("TESTING ADDITIONAL ADDRESSES")
#     print("="*80)
#     print("\nTesting additional addresses...\n")
#     for i, addr in enumerate(more_tests, 1):
#         print(f"{i}. {addr}")
#         print("-" * 80)
#         result = extractor.extract(addr)
#         print(f"   ✅ Confidence: {result['overall_confidence']:.1%}")
#         print(f"   ⏱️  Time: {result['extraction_time_ms']:.2f}ms")
#         print(f"\n   📦 Extracted Components:")
#         
#         components = {k: v for k, v in result['components'].items() if v}
#         if components:
#             for component, value in components.items():
#                 print(f"      {component:15} = {value}")
#         else:
#             print("      (none)")
#         print()

print("\n" + "="*80)
print("✅ Done! Modify 'test_addresses' array above to test different addresses.")
print("="*80)

# Optional: Show system statistics
# Uncomment below to see processing stats
#
# print("\n" + "="*80)
# print("SYSTEM STATISTICS")
# print("="*80)
# stats = extractor.stats
# print(f"Total Processed: {stats['total_processed']}")
# print(f"Total Time: {stats['total_time_ms']:.2f}ms")
# print(f"Errors: {stats['errors']}")
# if stats['total_processed'] > 0:
#     print(f"Avg Time/Address: {stats['total_time_ms'] / stats['total_processed']:.2f}ms")
