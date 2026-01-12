# 🚀 Simple Guide - Address Extractor

## Step 1: Train (Optional - for +1% accuracy)

```bash
cd address-extractor-complete

# Install spaCy (one time only)
pip3 install spacy
python3 -m spacy download xx_ent_wiki_sm

# Generate training data (~2 min)
python3 prepare_spacy_training_data.py

# Train model (~30 min)
python3 train_spacy_model.py
```

**Skip this step if you want to test without training first!**

---

## Step 2: Test

```bash
python3 simple_test.py
```

That's it! ✅

---

## What You'll See

```
Testing Address:
1152/C "Greenhouse", House# 45, Road# 08...
================================================================================

✅ Confidence: 95.0%
⏱️  Time: 12.34ms

📦 Extracted Components:
  house_number    = 45
  road            = 08
  area            = Shapla Residential Area
  district        = Chittagong
  postal_code     = 4219
```

---

## Add Your Own Test Addresses

Edit `simple_test.py` and add addresses to this list:

```python
more_tests = [
    'Your address here',
    'Another address here',
]
```

---

## Use in Your Code

```python
from production_address_extractor import ProductionAddressExtractor

extractor = ProductionAddressExtractor(
    data_path="../main/Processed data/merged_addresses.json"
)

result = extractor.extract("Your address here")
print(result['components'])
```

Done! 🎉
