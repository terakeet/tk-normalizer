# tk-normalizer

[![Python](https://img.shields.io/pypi/pyversions/tk-normalizer.svg)](https://pypi.org/project/tk-normalizer/)
[![PyPI](https://img.shields.io/pypi/v/tk-normalizer.svg)](https://pypi.org/project/tk-normalizer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

URL normalization library for creating consistent URL representations.

## Purpose

The URL normalization process creates a mechanism to provide equivalence between URLs with varying string, protocol, scheme, and query parameter ordering. This library helps create normalized representations of URLs for consistent storage, comparison, and analysis.

## Installation

```bash
pip install tk-normalizer
```

## Quick Start

```python
from tk_normalizer import TkNormalizer

# Simple usage - str() returns just the normalized URL
normalized = TkNormalizer("http://www.Example.com/path?b=2&a=1&utm_source=test")
print(str(normalized))  # Output: example.com/path?a=1&b=2

# Get full details with dict()
print(dict(normalized))  # Returns all fields including query_string, path, and hashes
```

## Features

### URL Normalization

The following URLs all normalize to the same normalized form:

```
https://example.com/
http://www.example.com/
http://www.example.com
http://www.example.com/#my_search_engine_is_great
https://www.example.com/?utm_campaign=SomeGoogleCampaign
https://www.example.com/?utm_source=because&utm_campaign=SomeGoogleCampaign
```

All normalize to: `example.com`

### Normalization Process

URLs are normalized through the following steps:

- ✅ Protocol and www subdomains removed
- ✅ Lowercased
- ✅ Trailing slashes removed
- ✅ Query parameters reordered alphabetically by key
- ✅ Duplicate query parameter key/value pairs removed
- ✅ Common tracking parameters removed (utm_*, gclid, fbclid, etc.)
- ✅ Non-HTTP(S) protocols rejected
- ✅ Localhost URLs rejected

### Tracking Parameters Removed

The following tracking parameters are automatically removed during normalization:

- `utm_*` (all utm parameters)
- `gclid`, `fbclid`, `dclid` (click identifiers)
- `_ga`, `_gid`, `_fbp`, `_hjid` (analytics cookies)
- `msclkid` (Microsoft Ads)
- `aff_id`, `affid` (affiliate tracking)
- `referrer`, `adgroupid`, `srsltid`

## Advanced Usage

### Getting Full Normalization Details

```python
from tk_normalizer import TkNormalizer

normalizer = TkNormalizer("http://blog.example.com/page?b=2&a=1")

# Use str() for just the normalized URL
print(str(normalizer))  # blog.example.com/page?a=1&b=2

# Use dict() for complete normalization data
result = dict(normalizer)
print(result)
# {
#   'normalized_url': 'blog.example.com/page?a=1&b=2',
#   'parent_normalized_url': 'blog.example.com',
#   'root_normalized_url': 'example.com',
#   'query_string': 'a=1&b=2',
#   'path': '/page',
#   'normalized_url_hash': '...',
#   'parent_normalized_url_hash': '...',
#   'root_normalized_url_hash': '...'
# }
```

### Error Handling

```python
from tk_normalizer import TkNormalizer, InvalidUrlException

try:
    normalizer = TkNormalizer("not a valid url")
except InvalidUrlException as e:
    print(f"Invalid URL: {e}")
```

### Accessing Individual Components

```python
from tk_normalizer import TkNormalizer

normalizer = TkNormalizer("https://blog.example.com/path?a=1")

# Dict-like access to individual fields
print(normalizer["normalized_url"])       # blog.example.com/path?a=1
print(normalizer["parent_normalized_url"]) # blog.example.com
print(normalizer["root_normalized_url"])   # example.com
print(normalizer["query_string"])          # a=1
print(normalizer["path"])                  # /path

# Iterate over available fields
for key in normalizer:
    print(f"{key}: {normalizer[key]}")

# Get all field names
print(normalizer.keys())
```

## Hashing

For efficient storage and comparison, SHA-256 hashes are computed for:
- The normalized URL
- The parent normal URL (domain without path)
- The root normal URL (root domain without subdomains)

This provides fixed-length representations suitable for database indexing.

## Important Caveats

While this normalization process works well for most use cases, there are some limitations:

1. **www subdomain removal**: Technically, `www.example.com` and `example.com` could serve different content, though this is rare in practice.

2. **Case sensitivity**: URLs are lowercased, but some servers are case-sensitive for paths.

3. **Tracking parameters**: New tracking parameters emerge over time and may not be in the removal list.

4. **Fragment removal**: URL fragments (#anchors) are removed, which may affect single-page applications.

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/terakeet/tk-normalizer.git
cd tk-normalizer

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=tk_normalizer

# Run linting
ruff check src tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_normalizer.py

# Run with coverage report
pytest --cov=tk_normalizer --cov-report=html
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions, please use the [GitHub issue tracker](https://github.com/terakeet/tk-normalizer/issues).

## Credits

Based on the URL normalization functionality from [tk-core](https://github.com/terakeet/tk-core), extracted and packaged for standalone use.
