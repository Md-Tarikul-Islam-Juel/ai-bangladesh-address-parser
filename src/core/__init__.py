"""
Core Address Extraction Module

Modular architecture for Bangladesh address parsing.
"""

from .extractor import ProductionAddressExtractor

# Public API
__all__ = [
    'ProductionAddressExtractor',
]

__version__ = "1.0.0"
