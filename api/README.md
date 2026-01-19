# API Directory

This directory contains API entry points for different platforms.

## Structure

```
api/
├── python/          # Python API entry points
│   ├── extract.py           # Node.js interface (python-shell)
│   └── fastapi_server.py    # FastAPI REST API server
└── node/            # Node.js/TypeScript library
    ├── index.ts     # Main library export
    └── test.ts      # Library tests
```

## Python API

### extract.py
Called by Node.js via `python-shell`:
```typescript
import { AddressExtractor } from 'ai-bangladesh-address-parser';
const extractor = new AddressExtractor();
```

### fastapi_server.py
Standalone FastAPI server:
```bash
python3 api/python/fastapi_server.py
# Server runs on http://localhost:8000
```

## Node.js API

The `node/` directory contains the TypeScript source for the npm package.

After building:
```typescript
import { AddressExtractor } from 'ai-bangladesh-address-parser';
const extractor = new AddressExtractor();
```
