# Tools Directory

This directory contains utility scripts and tools.

## Structure

```
tools/
├── control_stages.py    # Control which processing stages are enabled
└── postinstall.js       # npm postinstall script (Python dependency setup)
```

## Usage

### Control Stages
```bash
# Enable/disable specific stages
python3 tools/control_stages.py --disable fsm spacy --enable gazetteer

# Use a performance profile
python3 tools/control_stages.py --profile fast

# Show current configuration
python3 tools/control_stages.py --show
```

### Postinstall Script
Automatically runs after `npm install` to:
- Detect Python 3.9+
- Install Python dependencies from `requirements.txt`
- Download spaCy models if needed
