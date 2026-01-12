#!/usr/bin/env python3
"""
Debug Mirpur Postal Code Issue
"""

print("=" * 80)
print("🔍 DEBUGGING MIRPUR POSTAL CODE")
print("=" * 80)
print()

# Check Gazetteer
print("1️⃣ Checking Gazetteer (from merged_addresses.json)...")
from production_address_extractor import ProductionAddressExtractor

extractor = ProductionAddressExtractor(data_path='data/merged_addresses.json')
gaz = extractor.gazetteer

if 'Mirpur' in gaz.areas:
    print(f"   ✅ Mirpur in Gazetteer: {gaz.areas['Mirpur']}")
else:
    print(f"   ❌ Mirpur NOT in Gazetteer")

# Check offline geo
print()
print("2️⃣ Checking Offline Geo System...")
geo = extractor.gazetteer.offline_geo

if 'mirpur' in geo.upazilas:
    print(f"   Found as Upazila: {geo.upazilas['mirpur']}")
    
result = geo.predict_postal_code(area='Mirpur', district='Dhaka')
print(f"   Direct prediction: {result}")

# Check full extraction
print()
print("3️⃣ Full Address Extraction...")
test_addr = "House 12, Road 5, Mirpur 1, Dhaka"
result = extractor.extract(test_addr)

print(f"   Address: {test_addr}")
print(f"   Parsed area: {result['components'].get('area', 'NONE')}")
print(f"   Postal code: {result['components'].get('postal_code', 'NONE')}")
print()

# Check Gazetteer validation directly
print("4️⃣ Direct Gazetteer Validation...")
components = {'area': 'Mirpur', 'district': 'Dhaka'}
validated = gaz.validate(components)
print(f"   Input: {components}")
print(f"   Validated: {validated}")
