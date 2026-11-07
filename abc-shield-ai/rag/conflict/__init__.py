"""Conflict and overlap detection module for ABC Shield regulatory RAG."""

from rag.conflict.conflict_detector import (
    ConflictType,
    ConflictFinding,
    ConflictDetector,
    classify_relationship,
)

__all__ = [
    "ConflictType",
    "ConflictFinding",
    "ConflictDetector",
    "classify_relationship",
]
