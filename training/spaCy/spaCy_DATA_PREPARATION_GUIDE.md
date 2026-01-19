# Training Data Preparation Guide

**Quick guide for preparing spaCy training data from `merged_addresses.json`**

---

## Quick Start

### One Command
```bash
python3 training/spaCy/scripts/training_dataset_prepare.py
```

This converts `data/raw/merged_addresses.json` → `data/training/spacy_training_data.json`

---

## What It Does

The script automatically:

1. **Loads** addresses from `merged_addresses.json`
2. **Extracts** entities using:
   - Regex processors (most accurate)
   - Pattern-based span finding
   - Exact string matching (fallback)
3. **Validates** all entities:
   - Checks bounds
   - Detects overlaps
   - Validates formats
4. **Removes** duplicates
5. **Saves** spaCy training format

---

## Usage

### Basic (Default Paths)
```bash
python3 training/spaCy/scripts/training_dataset_prepare.py
```

**Input:** `data/raw/merged_addresses.json`  
**Output:** `data/training/spacy_training_data.json`

### Custom Paths
```bash
python3 training/spaCy/scripts/training_dataset_prepare.py \
  --input data/raw/merged_addresses.json \
  --output data/training/spacy_training_data.json \
  --min-entities 1
```

### Options
- `--input PATH` - Input `merged_addresses.json` file (default: `../../../data/raw/merged_addresses.json`)
- `--output PATH` - Output training data file (default: `../../../data/training/spacy_training_data.json`)
- `--min-entities N` - Minimum entities per example (default: 1)

---

## Input Format

**`merged_addresses.json`** should contain:
```json
[
  {
    "id": 1,
    "address": "#6, House #33, Flat 5E, Sector #4, Uttara",
    "components": {
      "house_number": "33",
      "flat_number": "5E",
      "block_number": "4",
      "area": "Uttara",
      "district": "",
      "road": "",
      "postal_code": ""
    }
  }
]
```

---

## Output Format

**`spacy_training_data.json`** format:
```json
[
  {
    "text": "#6, House #33, Flat 5E, Sector #4, Uttara",
    "entities": [
      [11, 13, "HOUSE"],   // "33" at position 11-13
      [20, 22, "FLAT"],    // "5E" at position 20-22
      [32, 33, "BLOCK"],   // "4" at position 32-33
      [35, 41, "AREA"]     // "Uttara" at position 35-41
    ]
  }
]
```

**Entity Labels:**
- `HOUSE` - House number
- `ROAD` - Road number/name
- `POSTAL` - Postal code
- `FLAT` - Flat number
- `FLOOR` - Floor number
- `BLOCK` - Block/Sector number
- `AREA` - Area name
- `DISTRICT` - District name

---

## How It Works

### 1. Entity Extraction Strategies

**Priority Order:**
1. **Regex Processors** (most accurate)
   - Uses actual extractors from `src/regex/`
   - Finds exact spans using patterns

2. **Pattern Matching**
   - Uses all patterns from `src/regex/patterns.py`
   - Tries patterns by confidence score

3. **Exact Matching**
   - Word-boundary exact match
   - Fallback for edge cases

### 2. Validation

- ✅ **Bounds Check** - Entity spans within text
- ✅ **Overlap Detection** - No overlapping entities
- ✅ **Format Validation** - Postal codes, etc.
- ✅ **Label Validation** - Valid entity types

### 3. Quality Assurance

- Removes duplicates
- Filters empty addresses
- Validates all entities
- Reports statistics

---

## Example Output

```
================================================================================
PROFESSIONAL TRAINING DATA PREPARATION
================================================================================

📂 Loading: data/raw/merged_addresses.json
   ✅ Loaded 1363 addresses

🔧 Processing addresses...
   ✅ Processed 1288 examples

💾 Saving: data/training/spacy_training_data.json
   ✅ Saved 1288 examples (359.3 KB)

================================================================================
STATISTICS
================================================================================
Total addresses:        1363
Processed:              1288
Skipped:                 75
Validation errors:      0

Entities created:
  AREA            896
  BLOCK           190
  DISTRICT        841
  FLAT            161
  FLOOR            94
  HOUSE           786
  POSTAL          182
  ROAD            703
================================================================================
```

---

## Next Steps

After preparation, train the model:

```bash
# Train with prepared data
python3 training/spaCy/scripts/train.py train --mode spacy --epochs 200
```

---

## Tips

1. **Minimum Entities:** Use `--min-entities 2` to filter examples with at least 2 entities
2. **Quality Check:** Review statistics to ensure good entity distribution
3. **Validation Errors:** Check first 10 errors shown in output
4. **File Size:** Output is typically 300-400 KB for 1,000+ examples

---

## Troubleshooting

**Issue:** "Input file not found"  
**Solution:** Check path with `--input` flag

**Issue:** "Validation errors"  
**Solution:** Check component values in `merged_addresses.json` match address text

**Issue:** "No entities created"  
**Solution:** Verify components in input file are not empty

---

**Script:** `training/spaCy/scripts/training_dataset_prepare.py`  
**Author:** Expert Dataset Preparation  
**Date:** January 2026
