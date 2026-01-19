#!/usr/bin/env python3
"""
FastAPI-based REST API for Address Extraction
Alternative to python-shell approach
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import ProductionAddressExtractor

app = FastAPI(
    title="Bangladesh Address Extractor API",
    description="Production-grade address extraction system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize extractor
data_path = Path(__file__).parent.parent / "data" / "merged_addresses.json"
if data_path.exists():
    extractor = ProductionAddressExtractor(data_path=str(data_path))
else:
    extractor = ProductionAddressExtractor()

class AddressRequest(BaseModel):
    address: str
    detailed: Optional[bool] = False

class AddressResponse(BaseModel):
    components: dict
    overall_confidence: float
    extraction_time_ms: float
    normalized_address: str
    original_address: str
    cached: Optional[bool] = None
    metadata: Optional[dict] = None

@app.get("/")
async def root():
    return {
        "service": "Bangladesh Address Extractor",
        "version": "1.0.0",
        "status": "ready"
    }

@app.post("/extract", response_model=AddressResponse)
async def extract_address(request: AddressRequest):
    """Extract components from a Bangladeshi address"""
    result = extractor.extract(request.address, detailed=request.detailed)
    
    return AddressResponse(
        components=result.get('components', {}),
        overall_confidence=result.get('overall_confidence', 0.0),
        extraction_time_ms=result.get('extraction_time_ms', 0),
        normalized_address=result.get('normalized_address', ''),
        original_address=result.get('original_address', request.address),
        cached=result.get('cached'),
        metadata=result.get('metadata') if request.detailed else None
    )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "extractor_ready": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
