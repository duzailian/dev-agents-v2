"""
Code Modification Module
=======================

This module provides tools for modifying source code, including:
- Generating patches (unified diffs)
- Applying patches to the codebase
- Reverting patches
"""

from .modifier import CodeModifier
from .patch_generator import PatchGenerator

__all__ = [
    "CodeModifier",
    "PatchGenerator",
]
