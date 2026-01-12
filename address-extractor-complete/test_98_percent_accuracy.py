#!/usr/bin/env python3
"""
Test 98%+ Confidence Postal Code Predictions
"""

from production_address_extractor import ProductionAddressExtractor

print("=" * 80)
print("🎯 TESTING 98%+ CONFIDENCE POSTAL CODE PREDICTIONS")
print("=" * 80)
print()

# Initialize system
print("Loading system...")
extractor = ProductionAddressExtractor(data_path='data/merged_addresses.json')
print(f"✅ Gazetteer: {len(extractor.gazetteer.areas)} areas loaded")
print(f"✅ Offline Geo: {'ENABLED' if extractor.gazetteer.offline_geo else 'DISABLED'}")
print()

# Test addresses with expected postal codes
test_cases = [
    {
        'address': '105/A, Central Road, Hatirpool, Dhaka',
        'expected_postal': '1205',  # Hatirpool
        'expected_area': 'Hatirpool'
    },
    {
        'address': 'House 12, Road 5, Mirpur 1, Dhaka',
        'expected_postal': '1216',  # Mirpur
        'expected_area': 'Mirpur'
    },
    {
        'address': 'Flat A-3, Building 7, Bashundhara R/A, Dhaka',
        'expected_postal': '1229',  # Bashundhara
        'expected_area': 'Bashundhara'
    },
    {
        'address': 'House 45, Road 08, Halishahar, Chittagong-4219',
        'expected_postal': '4219',  # Explicit in address
        'expected_area': 'Halishahar'
    },
    {
        'address': 'Banani, Dhaka',
        'expected_postal': None,  # Should have postal if in gazetteer
        'expected_area': 'Banani'
    },
    {
        'address': 'Gulshan, Dhaka',
        'expected_postal': None,  # Should have postal if in gazetteer
        'expected_area': 'Gulshan'
    },
    {
        'address': 'Dhanmondi, Dhaka',
        'expected_postal': None,  # Should have postal if in gazetteer
        'expected_area': 'Dhanmondi'
    }
]

print("=" * 80)
print("TESTING POSTAL CODE PREDICTIONS")
print("=" * 80)
print()

passed = 0
failed = 0
low_confidence = 0

for i, test in enumerate(test_cases, 1):
    print(f"[{i}/{len(test_cases)}] {test['address']}")
    print("-" * 80)
    
    result = extractor.extract(test['address'])
    
    # Extract results
    postal = result['components'].get('postal_code')
    area = result['components'].get('area')
    confidence = result.get('confidence', 0)
    
    # Check Gazetteer data
    if area and area in extractor.gazetteer.areas:
        gaz_data = extractor.gazetteer.areas[area]
        print(f"   Gazetteer data for '{area}':")
        print(f"      Postal codes: {gaz_data.get('postal_codes', [])}")
        if 'postal_code_counts' in gaz_data:
            print(f"      Frequencies: {gaz_data['postal_code_counts']}")
    
    # Results
    print(f"   Extracted:")
    print(f"      Area: {area}")
    print(f"      Postal: {postal}")
    print(f"      Confidence: {confidence:.1%}")
    
    # Validation
    if test['expected_postal']:
        if postal == test['expected_postal']:
            print(f"   ✅ CORRECT! Expected {test['expected_postal']}, got {postal}")
            passed += 1
        else:
            print(f"   ❌ WRONG! Expected {test['expected_postal']}, got {postal}")
            failed += 1
    else:
        if postal:
            print(f"   ✅ Postal predicted: {postal}")
            passed += 1
        else:
            print(f"   ⚠️  No postal predicted")
    
    # Confidence check
    if postal and confidence < 0.98:
        print(f"   ⚠️  LOW CONFIDENCE: {confidence:.1%} (target: 98%+)")
        low_confidence += 1
    
    print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total tests: {len(test_cases)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Low confidence: {low_confidence}")
print()

if failed == 0 and low_confidence == 0:
    print("✅ ALL TESTS PASSED WITH 98%+ CONFIDENCE!")
elif failed == 0:
    print("✅ All predictions correct, but some have <98% confidence")
else:
    print("❌ Some predictions need improvement")
