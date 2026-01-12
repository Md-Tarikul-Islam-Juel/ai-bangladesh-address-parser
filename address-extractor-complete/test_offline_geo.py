#!/usr/bin/env python3
"""
Test Offline Geographic Intelligence System
"""

from bangladesh_geo_offline import BangladeshOfflineGeo

print("=" * 80)
print("🇧🇩 TESTING OFFLINE GEOGRAPHIC INTELLIGENCE")
print("=" * 80)
print()

# Initialize
geo = BangladeshOfflineGeo()

# Test cases
test_cases = [
    ("Hatirpool", "Dhaka", "Dhaka"),
    ("Dhanmondi", "Dhaka", "Dhaka"),
    ("Mirpur 1", "Dhaka", "Dhaka"),
    ("Bashundhara", "Dhaka", "Dhaka"),
    ("Halishahar", "Chattogram", "Chattogram"),
    ("Keraniganj", "Dhaka", "Dhaka"),
]

print("Testing postal code prediction:")
print("-" * 80)
print()

for area, district, division in test_cases:
    print(f"📍 Testing: {area}, {district}")
    
    result = geo.predict_postal_code(area=area, district=district, division=division)
    
    if result:
        print(f"   ✅ Postal Code: {result['postal_code']}")
        print(f"   📊 Confidence: {result['confidence']:.1%}")
        print(f"   🎯 Source: {result['source']}")
        print(f"   📌 Location: {result['full_location']}")
    else:
        print(f"   ❌ No postal code found")
    
    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Divisions: {len(geo.divisions)}")
print(f"Districts: {len(geo.districts)}")
print(f"Upazilas: {len(geo.upazilas)}")
print(f"Unions: {len(geo.unions)}")
print(f"Villages: {len(geo.villages)}")
print(f"Postal Codes: {len(geo.postal_to_upazila)}")
print()
print("✅ Offline geographic intelligence system ready!")
