import multiprocessing
import time
from multiprocessing import Process

import pytest

from tk_normalizer import InvalidUrlException, TkNormalizer, url_normalize


def test_duplicate_parameters() -> None:
    normalizer = TkNormalizer(
        "http://www.Example.com/some-sub-folder/or_page.html?b=2&a=1&a=1&b=2&c=3&utm_source=some_value"
    )
    result = normalizer.get_normalized_url()
    assert result["normalized_url"] == "example.com/some-sub-folder/or_page.html?a=1&b=2&c=3"
    assert result["parent_normal_url"] == "example.com"
    assert result["root_normal_url"] == "example.com"


def test_multiple_similar_parameters() -> None:
    normalizer = TkNormalizer(
        "http://blog.example.com/some-folder/some-page.html?b=2&a=1&a=1&b=2&c=3&fbclid=another_value",
    )
    result = normalizer.get_normalized_url()
    assert result["normalized_url"] == "blog.example.com/some-folder/some-page.html?a=1&b=2&c=3"
    assert result["parent_normal_url"] == "blog.example.com"
    assert result["root_normal_url"] == "example.com"


def test_case_sensitivity() -> None:
    normalizer = TkNormalizer(
        "https://example.com/?a=1&b=2",
    )
    result = normalizer.get_normalized_url()
    assert result["normalized_url"] == "example.com?a=1&b=2"
    assert result["parent_normal_url"] == "example.com"
    assert result["root_normal_url"] == "example.com"


def test_protocol_differences() -> None:
    normalizer = TkNormalizer(
        "http://example.com/path/?a=1&a=1&b=2&utm_source=some_value",
    )
    result = normalizer.get_normalized_url()
    assert result["normalized_url"] == "example.com/path?a=1&b=2"
    assert result["parent_normal_url"] == "example.com"
    assert result["root_normal_url"] == "example.com"


def test_subdomain_presence() -> None:
    normalizer = TkNormalizer(
        "https://www.example.com/",
    )
    result = normalizer.get_normalized_url()
    assert result["normalized_url"] == "example.com"
    assert result["parent_normal_url"] == "example.com"
    assert result["root_normal_url"] == "example.com"


def test_subdomain_and_path_presence() -> None:
    normalizer = TkNormalizer(
        "http://example.com/",
    )
    result = normalizer.get_normalized_url()
    assert result["normalized_url"] == "example.com"
    assert result["parent_normal_url"] == "example.com"
    assert result["root_normal_url"] == "example.com"


# This test should allow, but reorder, duplicate parameter keys with different values
def test_multiple_parameters_with_duplicates_and_unwanted() -> None:
    normalizer = TkNormalizer("https://blog.example.com/path/?a=2&a=1&b=3&b=2&c=1&c=3&_ga=test")
    result = normalizer.get_normalized_url()
    assert result["normalized_url"] == "blog.example.com/path?a=1&a=2&b=2&b=3&c=1&c=3"
    assert result["parent_normal_url"] == "blog.example.com"
    assert result["root_normal_url"] == "example.com"


def test_multiple_parameters_with_unwanted() -> None:
    normalizer = TkNormalizer(
        "http://www.example.com/some-path/?a=1&c=3&b=2&utm_source=value&utm_campaign=remove",
    )
    result = normalizer.get_normalized_url()
    assert result["normalized_url"] == "example.com/some-path?a=1&b=2&c=3"
    assert result["parent_normal_url"] == "example.com"
    assert result["root_normal_url"] == "example.com"


# Test case for wildcard parameter removal
def test_wildcard_parameter_removal() -> None:
    normalizer = TkNormalizer(
        "http://www.example.com/some-path/?a=1&c=3&b=2&utm_param=value&utm_source=remove",
    )
    result = normalizer.get_normalized_url()
    assert result["normalized_url"] == "example.com/some-path?a=1&b=2&c=3"
    assert result["parent_normal_url"] == "example.com"
    assert result["root_normal_url"] == "example.com"


# Test case for invalid URL input
def test_invalid_url() -> None:
    with pytest.raises(InvalidUrlException) as excinfo:
        TkNormalizer(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")
    assert "Invalid URL" in str(excinfo.value)


def test_normalized_as_input() -> None:
    normalizer = TkNormalizer("example.com/some-path?a=1&b=2&c=3")
    result = normalizer.get_normalized_url()
    assert result["normalized_url"] == "example.com/some-path?a=1&b=2&c=3"
    assert result["parent_normal_url"] == "example.com"
    assert result["root_normal_url"] == "example.com"


def test_query_string_extraction() -> None:
    normalizer = TkNormalizer(
        "https://www.newscientist.com/article/mg23831750-500-how-can-india-clean-up-when-all-of-its-waste-has-an-afterlife/?utm_campaign=RSS%7CNSNS&utm_source=NSNS&utm_medium=RSS&campaign_id=RSS%7CNSNS-"
    )
    result = normalizer.get_normalized_url()
    assert (
        result["normalized_url"]
        == "newscientist.com/article/mg23831750-500-how-can-india-clean-up-when-all-of-its-waste-has-an-afterlife?campaign_id=rss%7Cnsns-"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://www.colorado.edu/ ",
        "https://www.capitalone.com/learn-grow/money-management/what-is-a-money-order/ ",
        "https://www.youtube.com/@jimmyiovine_ ",
        "https://www.linkedin.com/company/liv-golf/?originalSubdomain=uk  ",
        "https://www.nycfc.com/news/ ",
        " https://www.nycfc.com/news/",
        """https://boardroom.tv/out-of-office-jimmy-iovine/

    """,
        "http://www.hiruzu-.utiya.com/what-is-pull-planning",
        "https://www.ctc-.aps.org.uk/product/aps-annual-conference-2024-2024-09-26",
    ],
)
def test_url_initialization_no_errors(url: str) -> None:
    try:
        normalizer = TkNormalizer(url)
        assert normalizer is not None
    except InvalidUrlException:
        pytest.fail(f"TkNormalizer raised InvalidUrlException unexpectedly for URL: {url}")
    except Exception as e:
        pytest.fail(f"TkNormalizer raised an unexpected exception for URL: {url}. Exception: {str(e)}")


# It's out here for multiprocessing (pickling issues)
def run_normalizer_for_test(result_dict: dict, url: str) -> None:
    try:
        normalizer = TkNormalizer(url)
        result_dict["result"] = normalizer.get_normalized_url()
        result_dict["success"] = True
    except Exception as e:
        result_dict["exception"] = str(e)
        result_dict["success"] = False


def test_catastrophic_backtracking() -> None:
    bad_url = "https://community.nodebb.org/topic/3ec29195-14d7-461b-8970-b593d2699ad3/watching-reece@canadiancivil.com-s-how-to-fix-atlanta-s-broken-rail-system-and-as-usual-the-moment-anyone-shows-me-any-hypothetical-improved-future-marta-service-mad-that-includes-smyrna-i-immediately-get-chocked-up-and-have-to-fight-back-tears-of..."
    timeout = 2.0

    manager = multiprocessing.Manager()
    result_dict = manager.dict()

    process = Process(target=run_normalizer_for_test, args=(result_dict, bad_url))
    start_time = time.time()

    process.start()
    process.join(timeout)

    elapsed_time = time.time() - start_time

    # Adding a note here: We kick off the normalizer in a separate process -- if catastrophic backtracking
    # happens, we don't want it in a thread with our current GIL.
    #
    # If the process is still running after the timeout, that means it hung (or was severely delayed) -- either case
    # indicates a regex backtracking issue.
    # In this case, we kill the process and fail the test.
    if process.is_alive():
        process.terminate()
        process.join()
        pytest.fail(f"Test exceeded time limit of {timeout} seconds (took {elapsed_time:.2f}s)")

    assert "success" in result_dict and result_dict["success"]


# Test the new url_normalize function
def test_url_normalize_function() -> None:
    # Test basic functionality
    result = url_normalize("http://www.Example.com/path?b=2&a=1&utm_source=test")
    assert result == "example.com/path?a=1&b=2"

    # Test with complex URL
    result = url_normalize("https://blog.example.com/path/?a=2&a=1&b=3&b=2&c=1&c=3&_ga=test")
    assert result == "blog.example.com/path?a=1&a=2&b=2&b=3&c=1&c=3"

    # Test that it raises exception for invalid URLs
    with pytest.raises(InvalidUrlException):
        url_normalize("http://localhost")


# These fixtures are at the bottom for readability of the upper tests


@pytest.fixture
def happy_normal_fx() -> list[str]:
    """Everything here should pass, tuples are: (input, expected)"""
    return [
        ("http://www.example.com/some-path/?a=1&b=2&c=3&utm_source=some_value", "example.com/some-path?a=1&b=2&c=3"),
        ("filmărinunți.ro", "filmărinunți.ro"),
        ("всеавтозапчасти.бел", "всеавтозапчасти.бел"),
        ("10xe.orwww.10xe.org", "10xe.orwww.10xe.org"),
        ("https://upair.es.aptoide.com", "upair.es.aptoide.com"),
        ("http://blog.gianniscateringandevents.com/?p=27", "blog.gianniscateringandevents.com?p=27"),
        (
            "https://cazzapoeia.blogspot.com/2017/07/what-makes-good-seafood-restaurant.html?utm_source=feedburner&utm_medium=feed&utm_campaign=Feed:+cazzapoeia+(cazzapoeia)",
            "cazzapoeia.blogspot.com/2017/07/what-makes-good-seafood-restaurant.html",
        ),
        (
            "nordstrom.com/browse/men/clothing/pants?filterbymaterial=mesh&srsltid=afmbooo0gkfvz9kwi-1s5atomy-8mtn6nwvrwub1nmxc9z9b8zse6w7h",
            "nordstrom.com/browse/men/clothing/pants?filterbymaterial=mesh",
        ),
    ]


@pytest.fixture
def happy_edge_fx() -> list[str]:
    return [
        [
            "https://www.varinsights.com/doc/bsms-hottest-tech-articles-to-help-grow-your-business-may-edition-0001?atc~c=771+s=773+r=001+l=a",
            "varinsights.com/doc/bsms-hottest-tech-articles-to-help-grow-your-business-may-edition-0001?atc~c=771+s%3D773+r%3D001+l%3Da",
        ],
        [
            "http://widget3.linkwithin.com/redirect?url=http%3A//www.prestonbailey.com/blog/when-your-dream-wedding-and-budget-conflict-5-things-to-think-about/&rtype=&vars=%5Bnull%2C%20122890%2C%200%2C%20%22http%3A//www.prestonbailey.com/blog/budget-vs-dream-wed",
            "widget3.linkwithin.com/redirect?rtype=&url=http%3A%2F%2Fwww.prestonbailey.com%2Fblog%2Fwhen-your-dream-wedding-and-budget-conflict-5-things-to-think-about%2F&vars=%5Bnull%2C+122890%2C+0%2C+%22http%3A%2F%2Fwww.prestonbailey.com%2Fblog%2Fbudget-vs-dream-wed",
        ],
        [
            "https://books.google.com/books?id=bkMhYEJPLiAC&pg=PP5&lpg=PP5&dq=%22*+Construction+Company%22&source=bl&ots=Iv96Y1b3BD&sig=vC4wKxKFuEfV4-iTkTmgW0xRXL0&hl=en&sa=X&ved=0ahUKEwif2svxy7faAhULxVkKHXVjAK443gIQ6AEIyAEwHw",
            "books.google.com/books?dq=%22%2A+construction+company%22&hl=en&id=bkmhyejpliac&lpg=pp5&ots=iv96y1b3bd&pg=pp5&sa=x&sig=vc4wkxkfuefv4-itktmgw0xrxl0&source=bl&ved=0ahukewif2svxy7faahulxvkkhxvjak443giq6aeiyaewhw",
        ],
        [
            "https://search.datacite.org/api?q=*%3A*&fq=publisher_facet%3A%22Elsevier%22&fl=doi,creator,title,publisher,publicationYear,datacentre&fq=is_active:true&fq=has_metadata:true&rows=8930&wt=xml&indent=true",
            "search.datacite.org/api?fl=doi%2Ccreator%2Ctitle%2Cpublisher%2Cpublicationyear%2Cdatacentre&fq=has_metadata%3Atrue&fq=is_active%3Atrue&fq=publisher_facet%3A%22elsevier%22&indent=true&q=%2A%3A%2A&rows=8930&wt=xml",
        ],
        [
            "https://www.technojobs.co.uk/job/2515205//",
            "technojobs.co.uk/job/2515205",
        ],
        [
            "http://association-life.com/blog-page.php?article_id=MTIwNjE4ODkyNDg=",
            "association-life.com/blog-page.php?article_id=mtiwnje4odkyndg%3D",
        ],
        ["https://blogs.cedarville.edu/globaloutreach/?utmv", "blogs.cedarville.edu/globaloutreach?utmv="],
        [
            "http://www.oychicago.com/blog.aspx?blogmonth=12&blogyear=2014&%EF%BF%BD%C2%B6=-1",
            "oychicago.com/blog.aspx?blogmonth=12&blogyear=2014&%EF%BF%BD%C2%B6=-1",
        ],
        [
            "https://xn--d1aciiaflalce3a6l.xn--p1ai/qdxmoy28few13",
            "xn--d1aciiaflalce3a6l.xn--p1ai/qdxmoy28few13",
        ],
        [
            "https://caregiver-inc-.mightyrecruiter.com/",
            "caregiver-inc-.mightyrecruiter.com",
        ],
    ]


@pytest.fixture
def sad_normal_fx() -> list[str]:
    """
    Everything here should raise an exception
    All exceptions should at least be wrapped in InvalidUrlException
    """
    return [
        "http://localhost",
        "http://google..",
        "",
        "\\",
        "//",
        ".com",
        "http://.co",
        "https://www.google.comftp://ftp.ics.uci.edu/pub/wayne1/octa-bus-routes/route085.pdf",
    ]


def test_happy_normals(happy_normal_fx: list[str]) -> None:
    for url, expected in happy_normal_fx:
        normalizer = TkNormalizer(url)
        assert normalizer.get_normalized_url()["normalized_url"] == expected


def test_happy_edges(happy_edge_fx: list[str]) -> None:
    for url, expected in happy_edge_fx:
        normalizer = TkNormalizer(url)
        assert normalizer.get_normalized_url()["normalized_url"] == expected


def test_sad_normals(sad_normal_fx: list[str]) -> None:
    for url in sad_normal_fx:
        with pytest.raises(InvalidUrlException) as excinfo:
            print(url)
            TkNormalizer(url)
        assert "Invalid URL" in str(excinfo.value)
