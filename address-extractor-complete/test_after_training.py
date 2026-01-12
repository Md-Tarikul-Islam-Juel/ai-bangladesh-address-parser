#!/usr/bin/env python3
"""
Test After Training - Verify Improvements
==========================================
"""

from production_address_extractor import ProductionAddressExtractor

# Initialize with trained model
extractor = ProductionAddressExtractor(
    data_path="../main/Processed data/merged_addresses.json"
)

# Test cases that were problematic before
test_cases = [
    {
        'address': 'Flat A-3, Building 7, Bashundhara R/A, Dhaka',
        'expected': {
            'flat_number': 'A-3',
            'house_number': '7',
            'area': 'Bashundhara',  # R/A pattern
            'district': 'Dhaka',
            'division': 'Dhaka',
        }
    },
    {
        'address': 'House 12, Road 5, Dhanmondi, Dhaka',
        'expected': {
            'house_number': '12',
            'road': '5',
            'area': 'Dhanmondi',
            'district': 'Dhaka',
            'postal_code': '1209',  # Should be inferred!
            'division': 'Dhaka',
        }
    },
    {
        'address': '105/A, Central Road, Hatirpool, Dhaka',
        'expected': {
            'flat_number': '105/A',
            'road': 'Central Road',
            'area': 'Hatirpool',
            'district': 'Dhaka',
            'division': 'Dhaka',
        }
    },
    {
        'address': '1152/C "Greenhouse", House# 45, Road# 08, Shapla Residential Area, Halishahar, Chittagong-4219',
        'expected': {
            'house_number': '45',
            'road': '08',
            'area': 'Halishahar',  # or Shapla
            'district': 'Chattogram',
            'postal_code': '4219',
            'division': 'Chattogram',
        }
    }
]

print("=" * 80)
print("🧪 TESTING AFTER ML TRAINING")
print("=" * 80)
print()

total_tests = 0
passed_tests = 0
improved_components = []

for i, test in enumerate(test_cases, 1):
    address = test['address']
    expected = test['expected']
    
    print(f"[Test {i}/{len(test_cases)}]")
    print(f"Address: {address[:70]}...")
    print("-" * 80)
    
    # Extract
    result = extractor.extract(address)
    components = result['components']
    confidence = result['overall_confidence']
    
    print(f"Confidence: {confidence:.1%}")
    print()
    
    # Check each expected component
    test_results = []
    for component, expected_value in expected.items():
        actual_value = components.get(component, '')
        
        if actual_value:
            # Check if extracted value matches expected (fuzzy match)
            if expected_value.lower() in actual_value.lower() or actual_value.lower() in expected_value.lower():
                test_results.append(f"  ✅ {component:15} = {actual_value}")
                passed_tests += 1
            else:
                test_results.append(f"  ⚠️  {component:15} = {actual_value} (expected: {expected_value})")
        else:
            test_results.append(f"  ❌ {component:15} = (not detected) - expected: {expected_value}")
        
        total_tests += 1
    
    # Show all results
    for result_line in test_results:
        print(result_line)
        if '✅' in result_line:
            component = result_line.split('=')[0].split()[1].strip()
            if component not in improved_components:
                improved_components.append(component)
    
    print()

# Summary
accuracy = (passed_tests / total_tests * 100) if total_tests > 0 else 0

print("=" * 80)
print("📊 SUMMARY")
print("=" * 80)
print(f"Tests Passed: {passed_tests}/{total_tests}")
print(f"Accuracy: {accuracy:.1f}%")
print()

if accuracy >= 95:
    print("🎉 EXCELLENT! Training was successful!")
    print(f"   Achieved {accuracy:.1f}% accuracy on test cases")
elif accuracy >= 90:
    print("✅ GOOD! Training improved the system")
    print(f"   Achieved {accuracy:.1f}% accuracy")
else:
    print("⚠️  NEEDS REVIEW - Check if ML is properly loaded")
    print("   Run: python3 check_ml_status.py")

print()
print("Improved components detected:")
for comp in improved_components:
    print(f"  ✅ {comp}")

print()
print("=" * 80)
