import fnmatch
import hashlib
import logging
import re
from collections.abc import Iterator, KeysView
from urllib.parse import ParseResult, parse_qsl, unquote, urlencode, urlparse

# Uses https://gist.github.com/Integralist/edcfb88c925658a13fc3e51f581fe4bc as a starting point
# Modified for more current rules regarding host/domain/tld naming.

ip_middle_octet = r"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5]))"
ip_last_octet = r"(?:\.(?:[0-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"

regex = re.compile(
    r"^"
    # protocol identifier
    r"(?:(?:https?|ftp)://)"
    # user:pass authentication (updated to avoid catastrophic backtracking)
    r"(?:[a-zA-Z0-9._%+-]+(?::[^\s@]*)?@)?"
    r"(?:"
    r"(?P<private_ip>"
    # IP address exclusion
    # private & local networks
    r"(?:(?:10|127)" + ip_middle_octet + "{2}" + ip_last_octet + ")|"
    r"(?:(?:169\.254|192\.168)" + ip_middle_octet + ip_last_octet + ")|"
    r"(?:172\.(?:1[6-9]|2\d|3[0-1])" + ip_middle_octet + ip_last_octet + "))"
    r"|"
    # IP address dotted notation octets
    # excludes loopback network 0.0.0.0
    # excludes reserved space >= 224.0.0.0
    # excludes network & broadcast addresses
    # (first & last IP address of each class)
    r"(?P<public_ip>"
    r"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
    r"" + ip_middle_octet + "{2}"
    r"" + ip_last_octet + ")"
    r"|"
    # host name (modified: handles multiple hyphens, underscores in hostnames, and trailing hyphens)
    r"(?:(?:[a-z\-_\u00a1-\uffff0-9]-?)*[a-z_\u00a1-\uffff0-9\-]+)"
    # domain name (modified: handles multiple hyphens, and also underscores in domain names, and trailing hyphens)
    r"(?:\.(?:[a-z\-_\u00a1-\uffff0-9]-?)*[a-z_\u00a1-\uffff0-9\-]+)*"
    # TLD identifier (modified: handles oddities like site.xn--p1ai/)
    r"(?:\.(?:[a-z0-9\-\u00a1-\uffff]{2,}))"
    r")"
    # port number
    r"(?::\d{2,5})?"
    # resource path
    r"(?:/\S*)?"
    # query string
    r"(?:\?\S*)?"
    r"$",
    re.UNICODE | re.IGNORECASE,
)

pattern = re.compile(regex)


class InvalidUrlException(Exception):
    def __init__(self, message: str, original_exception: Exception) -> None:
        super().__init__(message)
        self.original_exception = original_exception


class TkNormalizer:
    # Define the list of query parameters to remove
    query_params_to_remove: list[str] = [
        "utm_*",
        "gclid",
        "fbclid",
        "dclid",
        "_ga",
        "_gid",
        "_fbp",
        "_hjid",
        "msclkid",
        "aff_id",
        "affid",
        "referrer",
        "adgroupid",
        "srsltid",
    ]

    def __init__(self, url: str, log_errors: bool = True) -> None:
        try:
            url = url.strip()
            self.log_errors: bool = log_errors
            self.logger = logging.getLogger(__name__)
            self.original_url: str = url
            self.normalized_url: str
            self.parent_normalized_url: str
            self.root_normalized_url: str
            self.query_string: str
            self.path: str
            self.normalized_url, self.parent_normalized_url, self.root_normalized_url = self.process_url(url)
            self.url_hashes: dict[str, str] = self.compute_hashes()
        except InvalidUrlException as e:
            if self.log_errors:
                self.logger.warning(f"{e}")
            raise e
        except Exception as e:
            m = f"Invalid URL (exception): {url}"
            if self.log_errors:
                self.logger.error(m)
            raise InvalidUrlException(m, e) from e

    def process_url(self, url: str) -> tuple[str, str, str]:
        url = self.lowercase_url(url)
        parsed_url = self.parse_url(url)
        netloc, path, query = self.validate_url(parsed_url)
        path = unquote(path)
        netloc = self.remove_www_subdomain(netloc)

        path = self.remove_trailing_slash(path)
        query_params = self.parse_query_params(query)
        query_params = self.remove_unwanted_params(query_params)
        query_params = self.sort_query_params(query_params)
        unique_params = self.remove_duplicate_params(query_params)
        self.query_string = urlencode(unique_params)
        self.path = path
        normalized_url = self.rebuild_url(netloc, path, unique_params)
        # After normalizing the URL, we can check if
        # the URL has a TLD, if not raise an error
        if "." not in normalized_url:
            raise InvalidUrlException(
                f"Invalid URL provided (no TLD in normalized URL) '{normalized_url}'",
                ValueError(f"Normalized URL must contain a top-level domain. '{normalized_url}'"),
            )
        parent_normalized_url = self.get_parent_normalized_url(netloc)
        root_normalized_url = self.get_root_normalized_url(netloc)
        return normalized_url, parent_normalized_url, root_normalized_url

    @staticmethod
    def lowercase_url(url: str) -> str:
        return url.lower() if url else url

    @staticmethod
    def parse_url(url: str) -> ParseResult:
        parsed_url: ParseResult = urlparse(url)

        # Handle URLs with neither scheme nor netloc
        if not parsed_url.scheme and not parsed_url.netloc:
            parsed_url = urlparse(f"http://{url}")

        return parsed_url

    @staticmethod
    def validate_url(parsed_url: ParseResult) -> tuple[str, str, str]:
        # This will also capture localhost by its nature
        if "." not in parsed_url.netloc:
            raise InvalidUrlException(
                f"Invalid URL provided (no dots) '{parsed_url.geturl()}'",
                ValueError(f"URLs without a tld are forbidden. '{parsed_url.netloc}'"),
            )

        # Only http(s) urls are currently allowed; this means no file, ftp, etc.
        if not str(parsed_url.scheme).startswith("http"):
            raise InvalidUrlException(
                f"Invalid URL provided (non-HTTP) '{parsed_url.geturl()}'",
                ValueError(f"Only http(s) URLs are currently allowed, received: '{parsed_url.scheme}'"),
            )

        # Some oddball or broken URLs will be caught here
        if not parsed_url.scheme or not parsed_url.netloc:
            raise InvalidUrlException(
                f"Invalid URL provided: (empty) '{parsed_url.geturl()}'",
                ValueError(f"URL could not be parsed. '{parsed_url.netloc}'"),
            )

        # Check again the mega regular-expression
        if not pattern.match(parsed_url.geturl()):
            raise InvalidUrlException(
                f"Invalid URL provided (regex.fail) '{parsed_url.geturl()}'", ValueError("URL failed regex check.")
            )

        return parsed_url.netloc, parsed_url.path, parsed_url.query

    @staticmethod
    def remove_www_subdomain(netloc: str) -> str:
        return netloc[4:] if str(netloc).startswith("www.") else netloc

    @staticmethod
    def remove_trailing_slash(path: str) -> str:
        return path.rstrip("/")

    @staticmethod
    def parse_query_params(query: str) -> list[tuple[str, str]]:
        return parse_qsl(query, keep_blank_values=True)

    def remove_unwanted_params(self, query_params: list[tuple[str, str]]) -> list[tuple[str, str]]:
        def is_unwanted_param(param: str) -> bool:
            return any(fnmatch.fnmatch(param, pattern) for pattern in self.query_params_to_remove)

        return [(k, v) for k, v in query_params if not is_unwanted_param(k)]

    @staticmethod
    def sort_query_params(query_params: list[tuple[str, str]]) -> list[tuple[str, str]]:
        return sorted(query_params, key=lambda x: (x[0], x[1]))

    @staticmethod
    def remove_duplicate_params(query_params: list[tuple[str, str]]) -> list[tuple[str, str]]:
        seen_params: set = set()
        unique_params: list[tuple[str, str]] = []
        for param in query_params:
            if param not in seen_params:
                seen_params.add(param)
                unique_params.append(param)
        return unique_params

    @staticmethod
    def rebuild_url(netloc: str, path: str, query_params: list[tuple[str, str]]) -> str:
        query_string: str = urlencode(query_params)
        return f"{netloc}{path}?{query_string}" if query_string else f"{netloc}{path}"

    @staticmethod
    def get_parent_normalized_url(netloc: str) -> str:
        return netloc

    @staticmethod
    def get_root_normalized_url(netloc: str) -> str:
        return ".".join(netloc.split(".")[-2:])

    def compute_hashes(self) -> dict[str, str]:
        def sha256_hash(value: str) -> str:
            return hashlib.sha256(value.encode()).hexdigest()

        return {
            "normalized_url_hash": sha256_hash(self.normalized_url),
            "parent_normalized_url_hash": sha256_hash(self.parent_normalized_url),
            "root_normalized_url_hash": sha256_hash(self.root_normalized_url),
        }

    def to_dict(self) -> dict[str, str | list[tuple[str, str]]]:
        return {
            "normalized_url": self.normalized_url,
            "parent_normalized_url": self.parent_normalized_url,
            "root_normalized_url": self.root_normalized_url,
            "query_string": self.query_string,
            "path": self.path,
            **self.url_hashes,
        }

    def __iter__(self) -> Iterator[str]:
        """Return an iterator over the keys of the normalized URL dict."""
        return iter(self.to_dict())

    def __getitem__(self, key: str) -> str | list[tuple[str, str]]:
        """Allow dict-like access to normalized URL fields."""
        return self.to_dict()[key]

    def keys(self) -> KeysView[str]:
        """Return the keys of the normalized URL dict."""
        return self.to_dict().keys()

    def __str__(self) -> str:
        return self.normalized_url
