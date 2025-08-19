"""
tk-normalizer: URL normalization library for consistent URL representation.

This library provides URL normalization functionality to create normalized
representations of URLs, handling variations in protocols, subdomains,
query parameters, and more.
"""

from .normalizer import InvalidUrlException, TkNormalizer

__version__ = "0.1.0"
__all__ = ["TkNormalizer", "InvalidUrlException", "url_normalize"]


def url_normalize(url: str) -> str:
    """
    Normalize a URL to its normalized form.

    This is a convenience function that creates a TkNormalizer instance
    and returns the normalized URL string.

    Args:
        url: The URL string to normalize.

    Returns:
        The normalized URL string.

    Raises:
        InvalidUrlException: If the URL is invalid or cannot be normalized.

    Example:
        >>> from tk_normalizer import url_normalize
        >>> url_normalize("http://www.Example.com/path?b=2&a=1&utm_source=test")
        'example.com/path?a=1&b=2'
    """
    normalizer = TkNormalizer(url)
    return normalizer.normalized_url
