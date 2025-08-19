# URL Normalization Architecture

## Purpose

The URL normalization process creates a mechanism to provide equivalence between URLs with varying string, protocol, scheme, and query parameter ordering. This document describes the technical architecture and implementation details of the tk-normalizer library.

## Overview

The normalizer transforms URLs into a normalized form that allows for consistent comparison and storage. This is critical for:
- Deduplication of URLs in data processing pipelines
- Consistent URL matching across systems
- Efficient storage and indexing of web addresses
- Analytics and reporting on web traffic

## Normalization Process

### Input Processing

URLs undergo the following transformations in order:

1. **Lowercasing**: All URLs are converted to lowercase for consistency
2. **Protocol Removal**: HTTP/HTTPS protocols are stripped
3. **WWW Subdomain Removal**: The `www.` prefix is removed if present
4. **Path Normalization**: Trailing slashes are removed from paths
5. **Query Parameter Processing**:
   - Parameters are parsed and decoded
   - Tracking parameters are removed
   - Remaining parameters are alphabetically sorted by key
   - Duplicate key/value pairs are removed
6. **Fragment Removal**: URL fragments (#anchors) are discarded

### URL Validation

The normalizer performs strict validation to ensure URL quality:

- **Protocol Check**: Only HTTP(S) URLs are accepted
- **Domain Validation**: URLs must contain a valid TLD (no localhost)
- **Regex Validation**: Complex regex patterns validate URL structure
- **IP Address Handling**: Private IP ranges are rejected

### Regular Expression Details

The normalizer uses a comprehensive regex pattern that handles:
- International domain names (IDN)
- IP addresses (excluding private ranges)
- Subdomains with hyphens and underscores
- Port numbers
- Complex query strings
- Unicode characters in domains

## Hashing Strategy

### SHA-256 Hash Generation

For efficient storage and comparison, three hashes are computed:

1. **Normalized URL Hash**: Hash of the fully normalized URL
2. **Parent Normal URL Hash**: Hash of the domain without path
3. **Root Normal URL Hash**: Hash of the root domain

Example:
```
URL: http://blog.example.com/page?a=1
Normalized: blog.example.com/page?a=1
Parent: blog.example.com
Root: example.com
```

## Tracking Parameter Removal

### Currently Removed Parameters

The following tracking parameters are automatically removed:

```python
query_params_to_remove = [
    "utm_*",      # Google/Urchin tracking
    "gclid",      # Google Click ID
    "fbclid",     # Facebook Click ID
    "dclid",      # DoubleClick Click ID
    "_ga",        # Google Analytics
    "_gid",       # Google Analytics
    "_fbp",       # Facebook Pixel
    "_hjid",      # Hotjar
    "msclkid",    # Microsoft Ads
    "aff_id",     # Affiliate ID
    "affid",      # Affiliate ID
    "referrer",   # Referrer info
    "adgroupid",  # Ad group ID
    "srsltid",    # Google SERP tracking
]
```

### Wildcard Matching

The `utm_*` pattern uses fnmatch to remove all UTM parameters:
- utm_source
- utm_medium
- utm_campaign
- utm_term
- utm_content
- Any other utm_ prefixed parameter

## Edge Cases and Handling

### Catastrophic Backtracking Prevention

The regex patterns have been optimized to prevent catastrophic backtracking:
- Authentication patterns use non-greedy matching
- Lookahead assertions are minimized
- Character classes are used efficiently

### International Domains

The normalizer fully supports:
- Unicode domain names (IDN)
- Punycode encoded domains
- Non-Latin TLDs (.бел, .рф, etc.)
- Emoji domains (where valid)

### Query Parameter Edge Cases

Special handling for:
- Empty parameter values (`?param=`)
- Parameters without values (`?param`)
- URL-encoded values
- Duplicate parameters with different values

## Error Handling

### InvalidUrlException

Custom exception class that:
- Wraps the original exception for debugging
- Provides clear error messages
- Maintains exception chain
- Supports optional logging

### Logging Configuration

The normalizer uses Python's standard logging:
```python
logger = logging.getLogger(__name__)
```

Logging can be disabled per instance:
```python
normalizer = TkNormalizer(url, log_errors=False)
```

## Performance Considerations

### Optimization Strategies

1. **Compiled Regex**: Patterns are pre-compiled at module level
2. **Early Validation**: Quick checks before expensive operations
3. **Efficient String Operations**: Using built-in methods where possible
4. **Minimal Object Creation**: Reusing data structures

### Multiprocessing Safety

The normalizer is designed to be multiprocessing-safe:
- No shared state between instances
- Thread-safe operations
- Pickleable for process pools

## Output Format

### Standard Output

```python
{
    'normalized_url': 'example.com/path?a=1',
    'parent_normal_url': 'example.com',
    'root_normal_url': 'example.com',
    'normalized_url_hash': '...',
    'parent_normal_url_hash': '...',
    'root_normal_url_hash': '...'
}
```

### Component Access

Individual components are accessible as instance attributes:
- `normalized_url`: The normalized URL string
- `parent_normal_url`: Domain without path
- `root_normal_url`: Root domain without subdomains
- `original_url`: Original input URL
- `url_hashes`: Dictionary of computed hashes

## Known Limitations

### Technical Caveats

1. **WWW Subdomain Removal**: Technically, `www.example.com` and `example.com` could serve different content
2. **Case Sensitivity**: Some servers are case-sensitive for paths
3. **Fragment Handling**: Fragments are removed, which may affect SPAs
4. **Tracking Parameters**: New parameters emerge over time
5. **Content Parameters**: Some parameters that appear to be tracking may affect content

### Imperfect Equivalence

The normalization process is lossy by design. The original reference should be stored alongside the normalized URL when the original form is important.

## Testing Strategy

### Test Coverage

The test suite includes:
- Happy path tests for common URLs
- Edge case handling (international domains, special characters)
- Invalid URL rejection
- Catastrophic backtracking prevention
- Performance regression tests

### Fixture Categories

1. **Happy Normals**: URLs that should normalize successfully
2. **Happy Edges**: Edge cases that should work
3. **Sad Normals**: URLs that should be rejected

## Future Considerations

### Potential Enhancements

1. **Configurable Parameter Removal**: Allow custom tracking parameter lists
2. **Canonical Link Detection**: Parse HTML for canonical tags
3. **Redirect Resolution**: Follow redirect chains via HTTP unwinding

## References

- URL specification: [RFC 3986](https://tools.ietf.org/html/rfc3986)
- Internationalized Domain Names: [RFC 5890](https://tools.ietf.org/html/rfc5890)
- Original regex base: [GitHub Gist](https://gist.github.com/Integralist/edcfb88c925658a13fc3e51f581fe4bc)
