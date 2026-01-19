# Python API Directory

This directory contains Python entry points for the address extractor.

## Structure

```
python/
├── api/              # API entry points
│   ├── __init__.py
│   ├── extract.py           # Node.js interface (python-shell)
│   └── fastapi_server.py    # FastAPI REST API server
└── __init__.py
```

## Entry Points

### 1. extract.py (Node.js Interface)
Called by Node.js via `python-shell`:
```typescript
import { AddressExtractor } from 'ai-bangladesh-address-parser';
const extractor = new AddressExtractor();
```

### 2. fastapi_server.py (REST API)
Standalone FastAPI server:
```bash
python3 python/api/fastapi_server.py
# Server runs on http://localhost:8000
```

## Usage

The Node.js library automatically uses `python/api/extract.py`.

For FastAPI server:
```bash
cd python/api
python3 fastapi_server.py
```
