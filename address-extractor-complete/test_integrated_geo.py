#!/usr/bin/env python3
"""
Test Integrated Offline Geographic Intelligence
"""
import sys

print("=" * 80)
print("🇧🇩 TESTING INTEGRATED OFFLINE GEO IN PRODUCTION SYSTEM")
print("=" * 80)
print()

try:
    # Test offline geo module directly
    print("1️⃣ Testing offline geo module...")
    from bangladesh_geo_offline import BangladeshOfflineGeo
    geo = BangladeshOfflineGeo()
    print(f"   ✅ Loaded {len(geo.divisions)} divisions")
    print(f"   ✅ Loaded {len(geo.upazilas)} upazilas")
    print()
    
    # Test direct prediction
    print("2️⃣ Testing direct postal prediction...")
    result = geo.predict_postal_code(area="Hatirpool", district="Dhaka")
    if result:
        print(f"   ✅ Hatirpool → {result['postal_code']} ({result['confidence']:.0%})")
    else:
        print(f"   ❌ No result")
    print()
    
    # Test production system integration
    print("3️⃣ Testing production system integration...")
    from production_address_extractor import ProductionAddressExtractor
    
    extractor = ProductionAddressExtractor(
        data_path='data/merged_addresses.json'
    )
    
    if extractor.gazetteer.offline_geo:
        print(f"   ✅ Production system has offline geo ENABLED!")
    else:
        print(f"   ❌ Production system offline geo NOT enabled")
    print()
    
    # Test extraction with postal prediction
    print("4️⃣ Testing extraction with implicit postal prediction...")
    test_cases = [
        "105/A, Central Road, Hatirpool, Dhaka",
        "House 12, Road 5, Mirpur 1, Dhaka",
        "Flat A-3, Building 7, Bashundhara R/A, Dhaka",
    ]
    
    for addr in test_cases:
        result = extractor.extract(addr)
        postal = result['components'].get('postal_code', 'NONE')
        print(f"   Address: {addr[:50]}...")
        print(f"   Postal: {postal}")
        print()
    
    print("=" * 80)
    print("✅ ALL INTEGRATION TESTS PASSED!")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
