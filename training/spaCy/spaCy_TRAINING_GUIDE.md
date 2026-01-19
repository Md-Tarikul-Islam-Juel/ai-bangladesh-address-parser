# Complete Training Guide

**Single comprehensive guide for training the Bangladesh Address Extractor model.**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prepare Training Data](#prepare-training-data)
3. [Training Commands](#training-commands)
4. [Regex Patterns Integration](#regex-patterns-integration)
5. [Training Workflow](#training-workflow)
6. [Pattern Statistics](#pattern-statistics)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Recommended: One-Command Training
```bash
# Consolidate datasets and train in one command
python3 training/spaCy/scripts/train.py train --mode spacy --epochs 200 --consolidate
```

This single command will:
1. ✅ Consolidate all training datasets
2. ✅ Enhance entities using regex patterns
3. ✅ Remove duplicates
4. ✅ Train the model with best data

### Alternative: Step-by-Step
```bash
# Step 1: Consolidate datasets
python3 training/spaCy/scripts/train.py consolidate

# Step 2: Train model
python3 training/scripts/train.py train --mode spacy --epochs 200
```

---

## Prepare Training Data

### Quick Preparation

Convert `merged_addresses.json` to spaCy training format:

```bash
python3 training/spaCy/scripts/training_dataset_prepare.py
```

**What it does:**
- ✅ Loads addresses from `data/raw/merged_addresses.json`
- ✅ Extracts entities using regex processors and patterns
- ✅ Validates all entity spans
- ✅ Removes duplicates
- ✅ Saves to `data/training/spacy_training_data.json`

**Options:**
```bash
python3 training/spaCy/scripts/training_dataset_prepare.py \
  --input data/raw/merged_addresses.json \
  --output data/training/spacy_training_data.json \
  --min-entities 1
```

**See:** [DATA_PREPARATION_GUIDE.md](DATA_PREPARATION_GUIDE.md) for detailed guide

---

## Training Commands

### `train` - Train Model

**Basic Usage:**
```bash
python3 training/scripts/train.py train --mode spacy --epochs 200
```

**With Auto-Consolidation (Recommended):**
```bash
python3 training/spaCy/scripts/train.py train --mode spacy --epochs 200 --consolidate
```

**Options:**
- `--mode {m4,pytorch-cpu,spacy}` - Training mode (default: m4)
  - `spacy` - CPU-only spaCy training (8-12 hours, 98.5% accuracy)
  - `pytorch-cpu` - CPU-only PyTorch (6-8 hours, 99.5% accuracy)
  - `m4` - M4 Metal GPU (4-6 hours, 99.5% accuracy) - **Recommended if available**
- `--data PATH` - Path to training data (default: `data/raw/merged_addresses.json`)
- `--epochs N` - Number of epochs/iterations (default: 50, recommended: 200 for spaCy)
- `--output PATH` - Output directory (default: `models/training/outputs/trained_model`)
- `--test` - Test mode (1,000 addresses, 10 epochs)
- `--consolidate` - Auto-consolidate training datasets before training
- `--consolidate-input FILE [FILE ...]` - Input files for consolidation
- `--consolidate-output FILE` - Output file for consolidated data

**Features:**
- ✅ Uses regex patterns from `src/regex/patterns.py` for enhanced extraction
- ✅ Automatically finds accurate entity spans using patterns
- ✅ Geographic intelligence integration
- ✅ Regex processor fallback

**Examples:**
```bash
# Quick test (10 epochs, 1,000 addresses)
python3 training/scripts/train.py train --mode spacy --epochs 10 --test

# Full training with consolidation
python3 training/spaCy/scripts/train.py train --mode spacy --epochs 200 --consolidate

# GPU training (if available)
python3 training/scripts/train.py train --mode m4 --epochs 50 --consolidate
```

---

### `consolidate` - Consolidate Training Datasets

**Usage:**
```bash
python3 training/spaCy/scripts/train.py consolidate \
  --input data/training/spacy_training_data.json \
         data/training/spacy_training_data_enhanced.json \
  --output data/training/spacy_training_data.json
```

**What it does:**
- ✅ Merges multiple training datasets
- ✅ Removes duplicates
- ✅ Enhances entities using regex patterns
- ✅ Validates all entity spans
- ✅ Creates single best dataset

**Options:**
- `--input FILE [FILE ...]` - Input training data files
- `--output FILE` - Output consolidated data file

---

### `enhance` - Enhance Training Data

**Usage:**
```bash
python3 training/spaCy/scripts/train.py enhance \
  --input data/training/spacy_training_data.json \
  --output data/training/spacy_training_data_enhanced.json
```

**What it does:**
- Fixes house/road entity separation issues
- Validates entity spans
- Adds missing examples

**Options:**
- `--input PATH` - Input training data file
- `--output PATH` - Output enhanced data file

---

### `add-examples` - Add House/Road Pattern Examples

**Usage:**
```bash
python3 training/spaCy/scripts/train.py add-examples
```

**What it does:**
- Adds specific examples for `h-X, r-Y` patterns
- Ensures proper entity separation
- Improves model accuracy on complex patterns

**Options:**
- `--output PATH` - Training data file to update

---

## Regex Patterns Integration

### Overview

The training system uses **144 unified regex patterns** from `src/regex/patterns.py` to:
- Extract address components accurately
- Find exact entity spans in text
- Improve training data quality
- Ensure consistency between training and inference

### Pattern Components

| Component | Patterns | Confidence Range | Description |
|-----------|----------|------------------|-------------|
| **House** | 73 | 0.90 - 0.98 | House number patterns (explicit, slash, banglish) |
| **Road** | 46 | 0.85 - 1.00 | Road number patterns (explicit, slash, bangla) |
| **Postal** | 8 | 0.98 - 1.00 | Postal code patterns (explicit, city-dash) |
| **Flat** | 5 | 0.98 | Flat number patterns |
| **Floor** | 5 | 0.98 | Floor number patterns |
| **Block** | 6 | 0.98 | Block number patterns |
| **Area** | 1 | 0.85 | Area patterns |

**Total: 144 patterns**

### How Patterns Work

1. **Pattern Priority:** Higher confidence patterns are tried first
2. **Accurate Spans:** Patterns find exact positions in text
3. **Component Extraction:** Patterns extract values directly from text
4. **Fallback:** If patterns don't match, regex processors are used

### Example

**Before (simple string search):**
```python
text = "h-107/2, r-7, mirpur"
# Finds "107/2" at position 2-7 (may be inaccurate)
```

**After (pattern matching):**
```python
text = "h-107/2, r-7, mirpur"
# Pattern: r'\b[hH][\s-]+([\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)'
# Finds "107/2" at exact position (accurate)
# Pattern: r'\b[rR][\s-]+([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)'
# Finds "7" at exact position (accurate)
```

### Pattern File Location

**File:** `src/regex/patterns.py`

All patterns are in one file for easy maintenance:
- Update patterns once
- Used everywhere automatically
- Single source of truth

---

## Training Workflow

### Complete Workflow (Recommended)

```bash
# Option 1: One command (easiest)
python3 training/spaCy/scripts/train.py train --mode spacy --epochs 200 --consolidate

# Option 2: Step by step (more control)
python3 training/spaCy/scripts/train.py consolidate
python3 training/spaCy/scripts/train.py add-examples
python3 training/scripts/train.py train --mode spacy --epochs 200
```

### Step-by-Step Breakdown

#### Step 1: Consolidate Datasets (Optional but Recommended)
```bash
python3 training/spaCy/scripts/train.py consolidate \
  --input data/training/spacy_training_data.json \
         data/training/spacy_training_data_enhanced.json \
  --output data/training/spacy_training_data.json
```

**What happens:**
- Loads all input datasets
- Removes duplicate addresses
- Enhances entities using regex patterns
- Validates all entity spans
- Saves consolidated dataset

#### Step 2: Add Examples (Optional)
```bash
python3 training/spaCy/scripts/train.py add-examples
```

**What happens:**
- Adds 13+ examples for `h-X, r-Y` patterns
- Ensures proper house/road separation
- Improves model accuracy

#### Step 3: Train Model
```bash
# spaCy training (CPU)
python3 training/scripts/train.py train --mode spacy --epochs 200

# PyTorch training (CPU)
python3 training/scripts/train.py train --mode pytorch-cpu --epochs 50

# M4 Metal GPU training (if available)
python3 training/scripts/train.py train --mode m4 --epochs 50
```

**What happens during training:**
- Loads training data from `data/raw/merged_addresses.json`
- Extracts components using regex patterns
- Finds accurate entity spans using pattern matching
- Prepares data for spaCy/PyTorch
- Trains model with validation
- Saves model to `models/training/outputs/`

#### Step 4: Move to Production
```bash
# After training completes
mv models/training/outputs/trained_model models/production/address_ner_model
```

---

## Pattern Statistics

### Pattern Distribution

- **House Number:** 73 patterns
  - Explicit patterns: `h-107/2`, `h@45`, `House No 12`, etc.
  - Slash patterns: `107/2`, `12/6`, etc.
  - Banglish patterns: `Kha/50`, `JA-10/1/A`, etc.

- **Road Number:** 46 patterns
  - Explicit patterns: `r-7`, `R@7`, `Road No 5`, etc.
  - Named roads: `Gulshan Road`, `Mirpur Lane`, etc.
  - Bangla patterns: `রোড নং ১৪`, `লেন-৩`, etc.

- **Postal Code:** 8 patterns
  - Explicit: `Post: 1216`, `P.O: 4000`, etc.
  - City-dash: `Dhaka-1216`, `Chittagong-4000`, etc.

- **Other Components:** 22 patterns
  - Flat: 5 patterns
  - Floor: 5 patterns
  - Block: 6 patterns
  - Area: 1 pattern

### Pattern Confidence Levels

- **1.00 (100%):** Very specific patterns (e.g., `Line #16`, `রোড নং ১৪`)
- **0.98 (98%):** High confidence patterns (e.g., `h-107/2`, `Road No 5`)
- **0.90-0.97 (90-97%):** Medium confidence patterns
- **0.85-0.89 (85-89%):** Lower confidence patterns (used as fallback)

---

## Troubleshooting

### Patterns Not Loading?

```bash
# Check if patterns file exists
ls src/regex/patterns.py

# Test import
python3 -c "from src.regex.patterns import ALL_PATTERNS; print(f'Loaded {len(ALL_PATTERNS)} components')"
```

**Expected output:**
```
Loaded 7 components
```

### Training Data Issues?

```bash
# Validate and consolidate training data
python3 training/spaCy/scripts/train.py consolidate \
  --output data/training/validated.json

# Check the output
python3 -c "import json; data = json.load(open('data/training/validated.json')); print(f'Valid examples: {len(data)}')"
```

### Model Not Training?

1. **Check dependencies:**
   ```bash
   python3 training/scripts/train.py train --mode spacy --epochs 1 --test
   ```

2. **Check data path:**
   ```bash
   ls data/raw/merged_addresses.json
   ```

3. **Check output directory:**
   ```bash
   mkdir -p models/training/outputs
   ```

### Low Accuracy After Training?

1. **Increase epochs:**
   ```bash
   python3 training/scripts/train.py train --mode spacy --epochs 300
   ```

2. **Add more examples:**
   ```bash
   python3 training/spaCy/scripts/train.py add-examples
   python3 training/spaCy/scripts/train.py consolidate
   ```

3. **Enhance training data:**
   ```bash
   python3 training/spaCy/scripts/train.py enhance
   ```

---

## Best Practices

### 1. Always Consolidate First
```bash
# Consolidate before training for best results
python3 training/spaCy/scripts/train.py consolidate
```

### 2. Use Auto-Consolidate Flag
```bash
# Simplest way - consolidates and trains in one command
python3 training/spaCy/scripts/train.py train --mode spacy --epochs 200 --consolidate
```

### 3. Test Before Full Training
```bash
# Quick test to verify everything works
python3 training/scripts/train.py train --mode spacy --epochs 10 --test
```

### 4. Monitor Training Progress
- Training shows progress every 10 iterations
- Watch for F1 score improvements
- Best model is saved automatically

### 5. Validate After Training
```bash
# Test the trained model
python3 tests/simple_test.py
```

---

## File Structure

```
training/
├── scripts/
│   └── train.py          # Unified training script
├── TRAINING_GUIDE.md     # This file (complete guide)
└── outputs/              # Training outputs
    └── trained_model/    # Trained models
```

---

## Quick Reference

### Most Common Commands

```bash
# One-command training (RECOMMENDED)
python3 training/spaCy/scripts/train.py train --mode spacy --epochs 200 --consolidate

# Quick test
python3 training/scripts/train.py train --mode spacy --epochs 10 --test

# Consolidate only
python3 training/spaCy/scripts/train.py consolidate

# Add examples
python3 training/spaCy/scripts/train.py add-examples
```

### Training Modes Comparison

| Mode | Time | Accuracy | Hardware |
|------|------|----------|----------|
| `spacy` | 8-12 hours | 98.5% | CPU only |
| `pytorch-cpu` | 6-8 hours | 99.5% | CPU only |
| `m4` | 4-6 hours | 99.5% | M4 Metal GPU |

---

## Summary

**For best results, use:**
```bash
python3 training/spaCy/scripts/train.py train --mode spacy --epochs 200 --consolidate
```

This single command:
1. ✅ Consolidates all training datasets
2. ✅ Enhances with regex patterns
3. ✅ Trains the model
4. ✅ Saves to `models/training/outputs/`

**After training:**
```bash
mv models/training/outputs/trained_model models/production/address_ner_model
```

---

**That's it! One command, complete training workflow.**
