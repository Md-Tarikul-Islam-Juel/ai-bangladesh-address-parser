#!/usr/bin/env python3
"""Test Area Detection with ML"""

from production_address_extractor import ProductionAddressExtractor
import spacy
from pathlib import Path

print("=" * 80)
print("TESTING AREA DETECTION")
print("=" * 80)

# Test the raw ML model first
model_path = Path(__file__).parent / "models" / "address_ner_model"
nlp = spacy.load(str(model_path))

test_cases = [
    'Flat A-3, Building 7, Bashundhara R/A, Dhaka',
    'House 12, Dhanmondi, Dhaka',
    'Shapla Residential Area, Halishahar',
    'Bashundhara Residential Area',
]

print("\n1️⃣  RAW ML MODEL TEST:")
print("-" * 80)
for address in test_cases:
    doc = nlp(address)
    print(f"\nAddress: {address}")
    if doc.ents:
        for ent in doc.ents:
            print(f"  {ent.label_:10} = {ent.text}")
    else:
        print("  (no entities detected)")

print("\n\n2️⃣  PRODUCTION SYSTEM TEST:")
print("-" * 80)

extractor = ProductionAddressExtractor(
    data_path="../main/Processed data/merged_addresses.json"
)

for address in test_cases:
    print(f"\nAddress: {address}")
    result = extractor.extract(address)
    components = result['components']
    
    # Show what was detected
    found = []
    for key, value in components.items():
        if value:
            found.append(f"{key}={value}")
    
    if found:
        print(f"  Found: {', '.join(found)}")
    else:
        print("  (nothing detected)")
    
    # Check specifically for area
    if components.get('area'):
        print(f"  ✅ Area detected: {components['area']}")
    else:
        print(f"  ❌ Area NOT detected")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

# Check what entity labels the model was trained on
print("\nML Model Entity Labels:")
if hasattr(nlp, 'get_pipe'):
    ner = nlp.get_pipe('ner')
    print(f"  Labels: {ner.labels}")
else:
    print("  (could not retrieve labels)")

print("\n" + "=" * 80)
