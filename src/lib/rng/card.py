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


class Card(Dataclass):
    """A playing card with a rank and suit."""

    rank: Rank = Field(description="The card's rank.")
    suit: Suit = Field(description="The card's suit.")
