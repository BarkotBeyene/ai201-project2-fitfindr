import pytest

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_suggest_outfit_with_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert len(results) > 0

    suggestion = suggest_outfit(results[0], get_example_wardrobe())
    assert isinstance(suggestion, str)
    assert len(suggestion.strip()) > 0


def test_suggest_outfit_empty_wardrobe_does_not_crash():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert len(results) > 0

    suggestion = suggest_outfit(results[0], get_empty_wardrobe())
    assert isinstance(suggestion, str)
    assert len(suggestion.strip()) > 0


def test_create_fit_card_happy_path():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert len(results) > 0

    outfit = suggest_outfit(results[0], get_example_wardrobe())
    card = create_fit_card(outfit, results[0])

    assert isinstance(card, str)
    assert len(card.strip()) > 0


def test_create_fit_card_empty_outfit_returns_error_string():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert len(results) > 0

    card = create_fit_card("", results[0])
    assert isinstance(card, str)
    assert len(card.strip()) > 0
    assert "suggest_outfit" in card.lower() or "styling" in card.lower()


def test_create_fit_card_whitespace_outfit_returns_error_string():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert len(results) > 0

    card = create_fit_card("   ", results[0])
    assert isinstance(card, str)
    assert len(card.strip()) > 0