#!/usr/bin/env python3
"""
Test Postal Code Confidence Display
Shows detailed confidence and source information
"""

from production_address_extractor import ProductionAddressExtractor

print("="*80)
print("🎯 POSTAL CODE CONFIDENCE TEST")
print("="*80)
print()

# Initialize
extractor = ProductionAddressExtractor(data_path="data/merged_addresses.json")

# Test addresses
test_cases = [
    '105/A, Central Road, puran dhaka, Dhaka',
    'House 12, Road 5, Mirpur 1, Dhaka',
    'Flat A-3, Building 7, Bashundhara R/A, Dhaka',
]

for i, address in enumerate(test_cases, 1):
    print(f"[{i}] {address}")
    print("-" * 80)
    
    result = extractor.extract(address)
    
    # Show postal code with confidence
    postal = result['components'].get('postal_code')
    area = result['components'].get('area')
    district = result['components'].get('district')
    
    print(f"   Area: {area}")
    print(f"   District: {district}")
    print(f"   Postal: {postal}")
    
    # Check Gazetteer for confidence
    if area and area in extractor.gazetteer.areas:
        gaz_data = extractor.gazetteer.areas[area]
        print(f"\n   Gazetteer Data:")
        print(f"      Postal codes: {gaz_data.get('postal_codes', [])}")
        if 'postal_code_counts' in gaz_data:
            counts = gaz_data['postal_code_counts']
            total = sum(counts.values())
            print(f"      Frequencies: {counts}")
            if postal and postal in counts:
                confidence = counts[postal] / total
                print(f"      → {postal}: {counts[postal]}/{total} samples = {confidence:.1%} confidence")
    
    # Try offline geo
    if extractor.gazetteer.offline_geo:
        geo_result = extractor.gazetteer.offline_geo.predict_postal_code(
            area=area,
            district=district
        )
        if geo_result:
            print(f"\n   Offline Geo Prediction:")
            print(f"      Postal: {geo_result['postal_code']}")
            print(f"      Confidence: {geo_result['confidence']:.1%}")
            print(f"      Source: {geo_result['source']}")
    
    print()
