import pytest
from pydantic import ValidationError

from src.lib.rng.card import Card, Rank, Suit


def test_suit_values():
    """All four suits exist with correct short values."""
    assert Suit.HEARTS == "H"
    assert Suit.DIAMONDS == "D"
    assert Suit.CLUBS == "C"
    assert Suit.SPADES == "S"
    assert len(Suit) == 4


def test_rank_values():
    """All thirteen ranks exist."""
    assert Rank.ACE == "A"
    assert Rank.TWO == "2"
    assert Rank.TEN == "10"
    assert Rank.JACK == "J"
    assert Rank.QUEEN == "Q"
    assert Rank.KING == "K"
    assert len(Rank) == 13


def test_card_construction():
    """Card can be created with Rank and Suit."""
    c = Card(rank=Rank.ACE, suit=Suit.SPADES)
    assert c.rank == Rank.ACE
    assert c.suit == Suit.SPADES


def test_card_from_strings():
    """Card accepts string values that match enum members."""
    c = Card(rank="A", suit="S")
    assert c.rank == Rank.ACE
    assert c.suit == Suit.SPADES


def test_card_rejects_invalid():
    """Card rejects invalid rank or suit."""
    with pytest.raises(ValidationError):
        Card(rank="X", suit="S")
    with pytest.raises(ValidationError):
        Card(rank="A", suit="Z")


def test_card_has_sid():
    """Card has auto-generated sid and cls fields."""
    c = Card(rank=Rank.ACE, suit=Suit.SPADES)
    assert hasattr(c, "sid")
    assert hasattr(c, "cls")
    assert "Card" in c.cls


def test_card_equality():
    """Two cards with same rank and suit are equal (aside from sid)."""
    c1 = Card(rank=Rank.ACE, suit=Suit.SPADES)
    c2 = Card(rank=Rank.ACE, suit=Suit.SPADES)
    assert c1.rank == c2.rank
    assert c1.suit == c2.suit


def test_full_deck_count():
    """Generating all combinations produces 52 cards."""
    deck = [Card(rank=r, suit=s) for s in Suit for r in Rank]
    assert len(deck) == 52
