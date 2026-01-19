"""Shared types and enums"""

from enum import Enum


class ScriptType(Enum):
    """Script type enumeration"""
    BANGLA = "bn"
    ENGLISH = "en"
    MIXED = "mixed"
    NEUTRAL = "neutral"
