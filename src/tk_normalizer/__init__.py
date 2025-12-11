"""
tk-normalizer: URL normalization library for consistent URL representation.

This library provides URL normalization functionality to create normalized
representations of URLs, handling variations in protocols, subdomains,
query parameters, and more.
"""

from .normalizer import InvalidUrlException, TkNormalizer

__version__ = "1.1.0"
__all__ = ["TkNormalizer", "InvalidUrlException"]
