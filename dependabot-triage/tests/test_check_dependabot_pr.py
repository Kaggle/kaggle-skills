import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_dependabot_pr import (  # noqa: E402
    normalize, version_le, is_major_bump, within_cutoff,
)


def test_normalize_collapses_separators():
    assert normalize("Flask_Cors") == "flask-cors"
    assert normalize("zope.interface") == "zope-interface"
    assert normalize("a__b..c") == "a-b-c"


def test_version_le_uses_numeric_ordering():
    assert version_le("1.2.3", "1.10.0")  # not lexicographic
    assert version_le("2.0", "2.0")  # equal
    assert version_le("1.9", "1.9.1")  # zero-padding
    assert not version_le("2.0.0", "1.9.9")


def test_is_major_bump():
    assert is_major_bump("1.4.2", "2.0.0")
    assert not is_major_bump("1.4.2", "1.9.0")
    assert not is_major_bump("garbage", "2.0")  # unparseable -> not a bump


def test_within_cutoff():
    assert within_cutoff("2024-01-01T00:00:00Z", "2024-06-01T00:00:00Z")
    assert not within_cutoff("2024-12-01T00:00:00Z", "2024-06-01T00:00:00Z")
    assert within_cutoff("anything", None)  # no cutoff configured
    assert not within_cutoff(None, "2024-06-01T00:00:00Z")  # unknown upload time
