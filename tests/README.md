# Tests

Simple test scripts for the Bangladesh Address Extractor.

## Quick Test

```bash
python3 tests/simple_test.py
```

## Using Newly Trained Model

**Important:** The test script uses the model from `models/production/address_ner_model`.

To use your newly trained model:

```bash
# Copy trained model to production location
cp -r models/training/outputs/trained_model models/production/address_ner_model

# Then run test
python3 tests/simple_test.py
```

Or specify model path in test script.

## What It Tests

- ✅ Address extraction from various formats
- ✅ Component extraction (house, road, area, district, postal code)
- ✅ Confidence scores
- ✅ Extraction time
- ✅ System initialization

## Test Addresses

The test includes:
- Simple addresses: `"House 12, Road 5, Mirpur 1, Dhaka"`
- Complex addresses: `"1152/C "Greenhouse", House# 45, Road# 08, Shapla Residential Area, Halishahar, Chittagong-4219"`
- Short addresses: `"Banani, Dhaka"`
- Special formats: `"h-107/2,r-7"`, `"h:107/2,R:7"`

## Output

Shows:
- Extracted components
- Confidence scores
- Extraction time
- System status

---

**File:** `tests/simple_test.py`
