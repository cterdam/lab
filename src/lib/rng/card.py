from enum import StrEnum

from pydantic import Field

from src.core import Dataclass


class Suit(StrEnum):
    """Playing card suit."""

    HEARTS = "H"
    DIAMONDS = "D"
    CLUBS = "C"
    SPADES = "S"


class Rank(StrEnum):
    """Playing card rank."""

    ACE = "A"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    JOKER = "joker"


class Card(Dataclass):
    """A playing card with a rank and suit.

    Standard cards have both rank and suit. Jokers have
    ``rank=Rank.JOKER`` and ``suit=None``.
    """

    rank: Rank = Field(description="The card's rank.")
    suit: Suit | None = Field(
        default=None,
        description="The card's suit. None for jokers.",
    )
