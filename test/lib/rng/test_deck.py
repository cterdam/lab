import gc
import weakref

from src.lib.rng.card import Card, Rank, Suit
from src.lib.rng.deck import Deck
from src.lib.rng.rng import RNG


# INIT & TYPE ###################################################################


def test_is_rng_subclass():
    """Deck is a subclass of RNG."""
    assert issubclass(Deck, RNG)


def test_instance_of_rng():
    """Deck instance is also an RNG."""
    d = Deck(seed=1, logname="test_isinstance")
    assert isinstance(d, RNG)


def test_logspace():
    """logspace includes both 'rng' and 'deck'."""
    d = Deck(seed=1, logname="test_logspace")
    assert "rng" in d.logspace
    assert "deck" in d.logspace


def test_default_deck_size():
    """Default deck has 52 cards."""
    d = Deck(seed=1, logname="test_default_size")
    assert d.pool_size == 52
    assert d.remaining == 52


def test_deck_with_jokers():
    """Deck with jokers=2 has 54 cards."""
    d = Deck(jokers=2, seed=1, logname="test_jokers")
    assert d.pool_size == 54
    assert d.remaining == 54


def test_deck_with_one_joker():
    """Deck with jokers=1 has 53 cards."""
    d = Deck(jokers=1, seed=1, logname="test_1joker")
    assert d.pool_size == 53


# CARD TYPES ####################################################################


def test_all_items_are_cards():
    """Every item in the deck is a Card."""
    d = Deck(seed=1, logname="test_card_types")
    cards = d.draw(52)
    for card in cards:
        assert isinstance(card, Card)


def test_standard_cards_have_rank_and_suit():
    """Standard cards have valid Rank and Suit."""
    d = Deck(seed=1, logname="test_rank_suit")
    card = d.draw()
    assert isinstance(card.rank, Rank)
    assert isinstance(card.suit, Suit)


def test_joker_cards_have_no_suit():
    """Joker cards have rank=JOKER and suit=None."""
    d = Deck(jokers=2, seed=1, logname="test_joker_nossuit")
    cards = d.draw(54)
    jokers = [c for c in cards if c.rank == Rank.JOKER]
    assert len(jokers) == 2
    for j in jokers:
        assert j.suit is None


def test_no_jokers_default():
    """Default deck has no jokers."""
    d = Deck(seed=1, logname="test_no_jokers")
    cards = d.draw(52)
    jokers = [c for c in cards if c.rank == Rank.JOKER]
    assert len(jokers) == 0


# COMPLETENESS #################################################################


def test_all_unique_combinations():
    """All 52 cards are unique rank+suit combinations."""
    d = Deck(seed=1, logname="test_unique")
    cards = d.draw(52)
    combos = [(c.rank, c.suit) for c in cards]
    assert len(set(combos)) == 52


def test_all_suits_present():
    """Deck contains every suit."""
    d = Deck(seed=1, logname="test_all_suits")
    cards = d.draw(52)
    suits = {c.suit for c in cards}
    assert suits == set(Suit)


def test_all_ranks_present():
    """Deck contains every standard rank (not JOKER)."""
    d = Deck(seed=1, logname="test_all_ranks")
    cards = d.draw(52)
    ranks = {c.rank for c in cards}
    assert ranks == set(Rank) - {Rank.JOKER}


def test_13_cards_per_suit():
    """Each suit has exactly 13 cards."""
    d = Deck(seed=1, logname="test_13_per_suit")
    cards = d.draw(52)
    for suit in Suit:
        count = sum(1 for c in cards if c.suit == suit)
        assert count == 13


def test_4_cards_per_rank():
    """Each standard rank has exactly 4 cards (one per suit)."""
    d = Deck(seed=1, logname="test_4_per_rank")
    cards = d.draw(52)
    for rank in Rank:
        if rank == Rank.JOKER:
            continue
        count = sum(1 for c in cards if c.rank == rank)
        assert count == 4


# DEAL METHOD ##################################################################


def test_deal_one():
    """deal() returns a single Card."""
    d = Deck(seed=42, logname="test_deal1")
    card = d.deal()
    assert isinstance(card, Card)
    assert d.remaining == 51


def test_deal_many():
    """deal(n) returns a list of n Cards."""
    d = Deck(seed=42, logname="test_deal_many")
    cards = d.deal(5)
    assert isinstance(cards, list)
    assert len(cards) == 5
    assert d.remaining == 47


def test_deal_exhausted():
    """deal() on empty deck returns None."""
    d = Deck(seed=1, logname="test_deal_empty")
    d.draw(52)
    assert d.deal() is None


def test_deal_too_many():
    """deal(n) where n > remaining returns None."""
    d = Deck(seed=1, logname="test_deal_toomany")
    d.draw(50)
    assert d.deal(5) is None
    assert d.remaining == 2


# DETERMINISM ##################################################################


def test_deterministic_deal():
    """Same seed produces same deal order."""
    d1 = Deck(seed=42, logname="test_det1")
    d2 = Deck(seed=42, logname="test_det2")
    hand1 = d1.deal(5)
    hand2 = d2.deal(5)
    assert [(c.rank, c.suit) for c in hand1] == [(c.rank, c.suit) for c in hand2]


def test_different_seeds_differ():
    """Different seeds produce different orders."""
    d1 = Deck(seed=1, logname="test_diff1")
    d2 = Deck(seed=999, logname="test_diff2")
    hand1 = [(c.rank, c.suit) for c in d1.deal(10)]
    hand2 = [(c.rank, c.suit) for c in d2.deal(10)]
    assert hand1 != hand2


# RESHUFFLE ####################################################################


def test_reshuffle():
    """reshuffle() restores the full deck."""
    d = Deck(seed=1, logname="test_resh")
    d.deal(10)
    assert d.remaining == 42
    d.reshuffle()
    assert d.remaining == 52


def test_reshuffle_with_jokers():
    """reshuffle() restores jokers too."""
    d = Deck(jokers=2, seed=1, logname="test_resh_jokers")
    d.deal(54)
    d.reshuffle()
    assert d.remaining == 54


def test_draw_all_after_reshuffle():
    """After reshuffle, all 52 cards are available again."""
    d = Deck(seed=1, logname="test_resh_all")
    first = d.draw(52)
    d.reshuffle()
    second = d.draw(52)
    assert sorted([(c.rank, c.suit) for c in first]) == sorted(
        [(c.rank, c.suit) for c in second]
    )


# VALIDATION ###################################################################


def test_load_rejects_non_cards():
    """load() rejects non-Card items."""
    d = Deck(seed=1, logname="test_load_bad")
    d.load(["not", "cards"])
    # Pool should remain unchanged (52 cards)
    assert d.remaining == 52


def test_load_accepts_cards():
    """load() accepts a list of Card objects."""
    d = Deck(seed=1, logname="test_load_good")
    new_cards = [Card(rank=Rank.ACE, suit=Suit.SPADES)]
    d.load(new_cards)
    assert d.pool_size == 1


def test_load_rejects_mixed():
    """load() rejects mixed list with any non-Card."""
    d = Deck(seed=1, logname="test_load_mixed")
    items = [Card(rank=Rank.ACE, suit=Suit.SPADES), "not a card"]
    d.load(items)
    # Pool should remain unchanged
    assert d.remaining == 52


# RNG METHODS STILL WORK ######################################################


def test_randint_works():
    """Plain RNG methods still work on Deck."""
    d = Deck(seed=42, logname="test_randint")
    val = d.randint(1, 6)
    assert 1 <= val <= 6


def test_choice_works():
    """choice() still works on Deck."""
    d = Deck(seed=42, logname="test_choice")
    val = d.choice(["a", "b", "c"])
    assert val in ["a", "b", "c"]


# CLEANUP ######################################################################


def test_cleanup():
    """Deck is garbage collected cleanly."""
    d = Deck(seed=1, logname="test_gc")
    weak = weakref.ref(d)
    del d
    gc.collect()
    assert weak() is None


# BLACKJACK SCENARIO ###########################################################


def test_blackjack_scenario():
    """Simulate a simple blackjack game."""
    d = Deck(seed=42, logname="test_blackjack")

    # Deal 2 cards each to player and dealer
    player = d.deal(2)
    dealer = d.deal(2)
    assert len(player) == 2
    assert len(dealer) == 2
    assert d.remaining == 48

    # Hit: player draws one more
    hit_card = d.deal()
    assert isinstance(hit_card, Card)
    assert d.remaining == 47

    # New round: reshuffle
    d.reshuffle()
    assert d.remaining == 52

    # Deal again
    player2 = d.deal(2)
    assert len(player2) == 2
