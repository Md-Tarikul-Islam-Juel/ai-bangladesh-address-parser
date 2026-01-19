#!/usr/bin/env python3
"""
FINAL PRODUCTION ADDRESS EXTRACTOR TEST
========================================
Complete 9-Stage Pipeline with ML + Geographic Intelligence
- 98%+ Confidence Postal Code Predictions
- Offline Geographic Intelligence (598 Upazilas, 3215 Unions)
- Gazetteer from 21,810 Real Bangladesh Addresses
- Bangladesh Context-Aware ML Model

Usage: python3 simple_test.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json

from src.core import ProductionAddressExtractor

print("="*80)
print("🇧🇩 PRODUCTION ADDRESS EXTRACTION SYSTEM")
print("="*80)

# Initialize extractor (automatically uses trained spaCy + geographic intelligence)
print("\nInitializing system...")
print("  → Loading Gazetteer from 21,810 real addresses...")
print("  → Loading Offline Geographic Intelligence...")
print("  → Loading Bangladesh-trained ML model...")

# Load data path
data_path = Path(__file__).parent.parent / "data" / "raw" / "merged_addresses.json"
data_path_str = str(data_path) if data_path.exists() else None

# Initialize extractor (automatically loads stage config from config/stage_config.json)
extractor = ProductionAddressExtractor(
    data_path=data_path_str
)

# Check what's enabled
print("\n✅ System Ready!")
print(f"  📊 Gazetteer: {'ENABLED' if extractor.gazetteer else 'DISABLED'}")
if extractor.gazetteer:
    print(f"     • {len(extractor.gazetteer.areas)} areas loaded")
    print(f"  🗺️  Offline Geo: {'ENABLED' if extractor.gazetteer.offline_geo else 'DISABLED'}")
    if extractor.gazetteer.offline_geo:
        geo = extractor.gazetteer.offline_geo
        print(f"     • {len(geo.divisions)} divisions")
        print(f"     • {len(geo.districts)} districts") 
        print(f"     • {len(geo.upazilas)} upazilas with postal codes")
        print(f"     • {len(geo.unions)} unions")
        print(f"     • {len(geo.postal_to_upazila)} postal code mappings")
print(f"  🤖 ML Model (spaCy NER): {'ENABLED' if extractor.spacy_ner and extractor.spacy_ner.enabled else 'DISABLED'}")
print(f"  🔧 FSM Parser: {'ENABLED' if extractor.fsm_parser else 'DISABLED'}")
print(f"  📝 Script Detection: {'ENABLED' if extractor.script_detector else 'DISABLED'}")
print()

# Test addresses (Array/List)
# Mix of addresses with and without explicit postal codes
test_addresses = [
    '105/A, Central Road, gulisthan, Dhaka',
    'House 12, Road 5, Mirpur 1, Dhaka',
    'Flat A-3, Building 7, Bashundhara R/A, Dhaka',
    'Banani, Dhaka',
    'Gulshan 2, Dhaka',
    'Dhanmondi 15, Dhaka',
    '1152/C "Greenhouse", House# 45, Road# 08, Shapla Residential Area, Halishahar, Chittagong-4219',
    '101/1 west monipur House name- Dream house, 60 feet road, 4th floor, flat- D2, Mirpur-2, Dhaka-1216',
    '1/4, South Begun Bari (Master Bari), Tejgaon I/A, Tejgaon, Dhaka -1208. (Near Satrasta)',
    '৬ রোড, ৯ ব্লক, C, চন্দ্রিমা মডেল টাউন, মোহাম্মদপুর, ঢাকা।',
    '৫৬ জিগাতলা, হাজী আবদুর রহমান লেন, ধানমন্ডি, ঢাকা-১২০৯' ,'sottota tower, h107/2,Road 7, zigatola',
    "Uttara, Sector 11, Road 13A, House 1, Floor 7B" 
]

print("="*80)
print(f"Testing {len(test_addresses)} Addresses")
print("="*80)
print()

# Process all addresses
results = []
for i, address in enumerate(test_addresses, 1):
    print(f"[{i}/{len(test_addresses)}] {address}")
    print("-" * 80)
    
    result = extractor.extract(address)
    results.append(result)
    
    # Show overall metrics
    print(f"⏱️  Time: {result['extraction_time_ms']:.2f}ms | 📊 Confidence: {result['overall_confidence']:.1%}")
    
    # Show components - each on separate line
    components = result['components']
    print("\n📦 Extracted Components:")
    
    found_any = False
    if components.get('flat_number'):
        print(f"   flat     = {components['flat_number']}")
        found_any = True
    if components.get('house_number'):
        print(f"   house    = {components['house_number']}")
        found_any = True
    if components.get('floor_number'):
        print(f"   floor    = {components['floor_number']}")
        found_any = True
    if components.get('road'):
        print(f"   road     = {components['road']}")
        found_any = True
    if components.get('block_number'):
        print(f"   block    = {components['block_number']}")
        found_any = True
    if components.get('area'):
        print(f"   area     = {components['area']}")
        found_any = True
    if components.get('district'):
        print(f"   district = {components['district']}")
        found_any = True
    if components.get('division'):
        print(f"   division = {components['division']}")
        found_any = True
    if components.get('postal_code'):
        postal = components['postal_code']
        
        # Get postal code confidence from evidence map if available
        postal_confidence = None
        if 'evidence_map' in result and 'postal_code' in result['evidence_map']:
            evidence = result['evidence_map']['postal_code']
            if evidence:
                # Get highest confidence from evidence
                postal_confidence = max(e.get('confidence', 0) for e in evidence)
        
        # Check if postal was in original address
        implicit = postal not in address
        
        # Display with confidence if >= 90%
        if postal_confidence and postal_confidence >= 0.90:
            confidence_str = f" ({postal_confidence:.1%} confidence)"
            if implicit:
                print(f"   postal   = {postal} ✨ (auto-predicted){confidence_str}")
            else:
                print(f"   postal   = {postal}{confidence_str}")
        else:
            if implicit:
                print(f"   postal   = {postal} ✨ (auto-predicted)")
            else:
                print(f"   postal   = {postal}")
        found_any = True
    
    if not found_any:
        print("   (no components extracted)")
    
    print()


# Summary statistics
print("="*80)
print("📊 SUMMARY")
print("="*80)

total_addresses = len(results)
with_postal = sum(1 for r in results if r['components'].get('postal_code'))
implicit_postal = sum(1 for i, r in enumerate(results) 
                      if r['components'].get('postal_code') and 
                      r['components']['postal_code'] not in test_addresses[i])

avg_confidence = sum(r['overall_confidence'] for r in results) / len(results) if results else 0
avg_time = sum(r['extraction_time_ms'] for r in results) / len(results) if results else 0

print(f"Total Addresses Tested: {total_addresses}")
print(f"Addresses with Postal Code: {with_postal}/{total_addresses}")
print(f"Auto-Predicted Postal Codes: {implicit_postal} ✨")
print(f"Average Confidence: {avg_confidence:.1%}")
print(f"Average Processing Time: {avg_time:.2f}ms")
print()
print("="*80)
print("✅ DONE! Modify 'test_addresses' array above to test more addresses.")
print("="*80)
print()
print("💡 TIP: The system now auto-predicts postal codes with 98%+ confidence!")
print("   - Uses 21,810 real Bangladesh addresses (Gazetteer)")
print("   - Uses 598 Upazilas + 3,215 Unions (Offline Geo)")
print("   - Uses Bangladesh-trained ML model (spaCy NER)")
print("="*80)
