#!/usr/bin/env python3
"""Test imports to debug the issue"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing processor imports...\n")

# Test each import individually
processors = [
    ('house_number_processor', 'AdvancedHouseNumberExtractor'),
    ('road_processor', 'AdvancedRoadNumberExtractor'),
    ('area_processor', 'AdvancedAreaExtractor'),
    ('district_processor', 'AdvancedCityExtractor'),
    ('postal_code_processor', 'AdvancedPostalCodeExtractor'),
    ('flat_number_processor', 'AdvancedFlatNumberExtractor'),
    ('floor_number_processor', 'AdvancedFloorNumberExtractor'),
    ('block_processor', 'AdvancedBlockNumberExtractor'),
]

success_count = 0
failed = []

for module_name, class_name in processors:
    try:
        module = __import__(module_name)
        cls = getattr(module, class_name)
        print(f"✓ {module_name}.{class_name}")
        success_count += 1
    except Exception as e:
        print(f"✗ {module_name}.{class_name}")
        print(f"  Error: {type(e).__name__}: {e}")
        failed.append((module_name, str(e)))

print(f"\n{'='*60}")
print(f"Result: {success_count}/{len(processors)} processors loaded")

if failed:
    print(f"\n❌ Failed imports:")
    for module_name, error in failed:
        print(f"  - {module_name}: {error}")
else:
    print("\n✅ All processors loaded successfully!")
