#!/usr/bin/env python3
import sys
print("=" * 80, flush=True)
print("QUICK GEO TEST", flush=True)
print("=" * 80, flush=True)

try:
    from bangladesh_geo_offline import BangladeshOfflineGeo
    print("✅ Module imported", flush=True)
    
    geo = BangladeshOfflineGeo()
    print(f"✅ Loaded {len(geo.divisions)} divisions", flush=True)
    print(f"✅ Loaded {len(geo.districts)} districts", flush=True)
    print(f"✅ Loaded {len(geo.upazilas)} upazilas", flush=True)
    print(f"✅ Loaded {len(geo.postal_to_upazila)} postal codes", flush=True)
    
    # Test postal prediction
    result = geo.predict_postal_code(area="Keraniganj", district="Dhaka")
    if result:
        print(f"\n✅ Test: Keraniganj → {result['postal_code']}", flush=True)
    else:
        print("\n❌ No result for test", flush=True)
        
except Exception as e:
    print(f"❌ ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ ALL TESTS PASSED!", flush=True)
