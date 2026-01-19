# Models Directory

This directory contains trained ML models for address extraction.

## Structure

```
models/
├── production/          # ✅ ACTIVE - Model used by the system
│   └── address_ner_model/  # Currently running model
│
├── training/           # 🔬 EXPERIMENTAL - Newly trained models
│   └── outputs/        # Training outputs (test before production)
│       └── trained_model/  # Latest trained model
│
└── archived/          # 📦 BACKUP - Old models (for rollback)
    └── trained_model/  # Previous model versions
```

## Purpose of Each Folder

### 1. `production/` - Active Model
- **Used by:** The system automatically loads from here
- **Purpose:** The model that's currently running in production
- **Path:** `models/production/address_ner_model/`
- **When to update:** After testing a new model and confirming it's better

### 2. `training/` - Experimental Models
- **Used by:** Training script saves here
- **Purpose:** Store newly trained models for testing
- **Path:** `models/training/outputs/trained_model/`
- **When to use:** Test new models here before promoting to production

### 3. `archived/` - Backup Models
- **Used by:** Manual backup/rollback
- **Purpose:** Keep old model versions for safety
- **Path:** `models/archived/trained_model/`
- **When to use:** If new model has issues, rollback to archived version

## Workflow

### Training a New Model
```bash
# 1. Train model (saves to training/outputs/)
python3 training/spaCy/scripts/train.py train --mode spacy --epochs 200

# 2. Test the new model
# (Copy to production temporarily or specify path)

# 3. If good, promote to production
cp -r models/training/outputs/trained_model models/production/address_ner_model

# 4. Archive old production model (optional)
mv models/production/address_ner_model models/archived/trained_model_$(date +%Y%m%d)
```

## Why Three Folders?

**Best Practice:** Separates concerns
- ✅ **Production** = What's running (stable, tested)
- ✅ **Training** = What's being developed (experimental)
- ✅ **Archived** = What was running (backup/rollback)

This prevents accidentally breaking production with untested models.

## Simplification (Optional)

If you want to simplify, you can:
- Keep only `production/` and `training/`
- Remove `archived/` if you don't need rollback capability
- Or merge `training/outputs/` directly to `production/` after training

---

**Current Active Model:** `models/production/address_ner_model/`
