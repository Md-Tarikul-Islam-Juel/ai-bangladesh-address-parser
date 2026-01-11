#!/usr/bin/env python3
"""
Test Production System
======================

Simple test to verify the complete 9-stage system works

Usage:
    python test_production_system.py
"""

import json
from pathlib import Path

# Import the production system
from production_address_extractor import ProductionAddressExtractor

def test_single_address():
    """Test on the complex address from user"""
    print("=" * 80)
    print("TEST 1: COMPLEX ADDRESS EXTRACTION")
    print("=" * 80)
    print()
    
    # Initialize system
    data_path = "../Processed data/merged_addresses.json"
    if Path(data_path).exists():
        print(f"✓ Found dataset: {data_path}")
        extractor = ProductionAddressExtractor(data_path=data_path)
    else:
        print(f"✗ Dataset not found: {data_path}")
        print("  Using default gazetteer...")
        extractor = ProductionAddressExtractor()
    
    print()
    
    # Test address from user
    test_address = '1152/C "Greenhouse", House# 45, Road# 08 (In front of Kamal Store), Shapla Residential Area, Halishahar, Chittagong-4219'
    
    print("INPUT:")
    print(f"  {test_address}")
    print()
    
    # Extract
    result = extractor.extract(test_address, detailed=True)
    
    print("NORMALIZED:")
    print(f"  {result['normalized_address']}")
    print()
    
    print("EXTRACTED COMPONENTS:")
    components = result['components']
    for component, value in components.items():
        if value:
            symbol = "✓"
        else:
            symbol = "✗"
        print(f"  {symbol} {component:15s} = {value if value else '(not found)'}")
    print()
    
    print(f"CONFIDENCE: {result['overall_confidence']:.1%}")
    print(f"TIME: {result['extraction_time_ms']:.2f}ms")
    print()
    
    # Expected vs Actual
    print("VALIDATION:")
    expected = {
        'house_number': '45',
        'road': '08',
        'area': 'Halishahar',
        'district': 'Chattogram',
        'postal_code': '4219'
    }
    
    all_correct = True
    for component, expected_value in expected.items():
        actual_value = components.get(component, '')
        match = actual_value.lower() == expected_value.lower()
        symbol = "✓" if match else "✗"
        print(f"  {symbol} {component:15s}: expected '{expected_value}', got '{actual_value}'")
        if not match:
            all_correct = False
    
    print()
    
    if all_correct:
        print("🎉 ALL TESTS PASSED! System working perfectly!")
    else:
        print("⚠ Some components don't match expected values")
    
    print()
    print("=" * 80)
    print()
    
    return all_correct


def test_batch():
    """Test batch processing"""
    print("=" * 80)
    print("TEST 2: BATCH PROCESSING (10 addresses)")
    print("=" * 80)
    print()
    
    data_path = "../Processed data/merged_addresses.json"
    
    if not Path(data_path).exists():
        print(f"✗ Dataset not found: {data_path}")
        print("  Skipping batch test")
        return
    
    # Load first 10 addresses
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    test_data = data[:10]
    addresses = [item['address'] for item in test_data]
    
    # Initialize extractor
    extractor = ProductionAddressExtractor(data_path=data_path)
    
    # Process batch
    print(f"Processing {len(addresses)} addresses...")
    print()
    
    results = extractor.batch_extract(addresses, show_progress=False)
    
    # Show results
    print("RESULTS:")
    for i, (item, result) in enumerate(zip(test_data, results), 1):
        print(f"\n{i}. {item['address'][:60]}...")
        print(f"   Extracted: house={result['components']['house_number']}, "
              f"road={result['components']['road']}, "
              f"area={result['components']['area']}")
        print(f"   Confidence: {result['overall_confidence']:.0%}, "
              f"Time: {result['extraction_time_ms']:.2f}ms")
    
    print()
    print("=" * 80)
    print("✓ Batch processing works!")
    print("=" * 80)
    print()


def main():
    """Run all tests"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "PRODUCTION SYSTEM VERIFICATION TESTS" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    # Test 1: Single complex address
    test1_passed = test_single_address()
    
    # Test 2: Batch processing
    test_batch()
    
    print()
    print("=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
    print()
    
    if test1_passed:
        print("✅ System is working correctly!")
        print()
        print("Next steps:")
        print("  1. Process your full dataset:")
        print("     python production_address_extractor.py --batch \\")
        print("         --input '../Processed data/merged_addresses.json' \\")
        print("         --output 'output/processed_full.json'")
        print()
        print("  2. Integrate into your application")
        print("  3. Deploy to production")
    else:
        print("⚠ Some tests failed - review output above")
    
    print()


if __name__ == "__main__":
    main()
