import pytest

from bot.src.utils.majority import parse_majority, has_majority


def test_parse_fraction():
    assert parse_majority("2/3") == (2, 3)


def test_parse_percent():
    assert parse_majority("66%") == (66, 100)


def test_has_majority_true():
    # 2 yes, 1 no, 0 abstain with simple majority 1/2
    assert has_majority(2, 1, 0, 1, 2) is True


def test_has_majority_false():
    # 1 yes, 2 no, 0 abstain with 2/3 majority required
    assert has_majority(1, 2, 0, 2, 3) is False