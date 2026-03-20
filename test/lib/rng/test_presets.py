from src.lib.rng.card import Card, Rank, Suit
from src.lib.rng.coin import CoinSide
from src.lib.rng.rng import RNG


# POKER DECK ###################################################################


def test_poker_deck_size():
    """poker_deck creates 52 cards."""
    r = RNG.poker_deck(seed=1, logname="test_pd_size")
    assert r.pool_size == 52
    assert r.remaining == 52


def test_poker_deck_card_types():
    """All items in the poker deck are Card instances."""
    r = RNG.poker_deck(seed=1, logname="test_pd_types")
    card = r.draw()
    assert isinstance(card, Card)
    assert isinstance(card.rank, Rank)
    assert isinstance(card.suit, Suit)


def test_poker_deck_all_unique():
    """All 52 cards are unique rank+suit combinations."""
    r = RNG.poker_deck(seed=1, logname="test_pd_unique")
    cards = r.draw(52)
    combos = [(c.rank, c.suit) for c in cards]
    assert len(set(combos)) == 52


def test_poker_deck_all_suits_and_ranks():
    """Deck contains every suit and every standard rank."""
    r = RNG.poker_deck(seed=1, logname="test_pd_complete")
    cards = r.draw(52)
    suits = {c.suit for c in cards}
    ranks = {c.rank for c in cards}
    assert suits == set(Suit)
    assert ranks == set(Rank) - {Rank.JOKER}


def test_poker_deck_deterministic():
    """Same seed produces same deal order."""
    r1 = RNG.poker_deck(seed=42, logname="test_pd_det1")
    r2 = RNG.poker_deck(seed=42, logname="test_pd_det2")
    hand1 = r1.draw(5)
    hand2 = r2.draw(5)
    assert [(c.rank, c.suit) for c in hand1] == [(c.rank, c.suit) for c in hand2]


def test_poker_deck_reshuffle():
    """poker_deck supports reshuffle."""
    r = RNG.poker_deck(seed=1, logname="test_pd_resh")
    r.draw(10)
    assert r.remaining == 42
    r.reshuffle()
    assert r.remaining == 52


def test_poker_deck_with_jokers():
    """poker_deck with jokers=2 creates 54 cards."""
    r = RNG.poker_deck(jokers=2, seed=1, logname="test_pd_jokers")
    assert r.pool_size == 54
    assert r.remaining == 54


def test_poker_deck_joker_cards():
    """Joker cards have rank=JOKER and suit=None."""
    r = RNG.poker_deck(jokers=2, seed=1, logname="test_pd_joker_cards")
    cards = r.draw(54)
    jokers = [c for c in cards if c.rank == Rank.JOKER]
    assert len(jokers) == 2
    for j in jokers:
        assert j.suit is None


def test_poker_deck_no_jokers_default():
    """poker_deck defaults to 0 jokers."""
    r = RNG.poker_deck(seed=1, logname="test_pd_no_jokers")
    cards = r.draw(52)
    jokers = [c for c in cards if c.rank == Rank.JOKER]
    assert len(jokers) == 0


# COIN #########################################################################


def test_coin_pool():
    """coin creates a pool with heads and tails."""
    r = RNG.coin(seed=1, logname="test_coin")
    assert r.pool_size == 2
    assert r.remaining == 2


def test_coin_draw():
    """Drawing from coin yields CoinSide values."""
    r = RNG.coin(seed=1, logname="test_coin_draw")
    side = r.draw()
    assert isinstance(side, CoinSide)
    assert side in (CoinSide.HEADS, CoinSide.TAILS)


def test_coin_exhaustion():
    """Coin pool has exactly 2 items."""
    r = RNG.coin(seed=1, logname="test_coin_exhaust")
    r.draw()
    r.draw()
    assert r.remaining == 0
    assert r.draw() is None


def test_coin_reshuffle():
    """Coin supports reshuffle."""
    r = RNG.coin(seed=1, logname="test_coin_resh")
    r.draw(2)
    r.reshuffle()
    assert r.remaining == 2


# DICE #########################################################################


def test_dice_default():
    """dice() creates a 6-sided die by default."""
    r = RNG.dice(seed=1, logname="test_dice")
    assert r.pool_size == 6
    assert r.remaining == 6


def test_dice_custom_sides():
    """dice(n_sides=20) creates a 20-sided die."""
    r = RNG.dice(20, seed=1, logname="test_d20")
    assert r.pool_size == 20
    assert r.remaining == 20


def test_dice_draw():
    """Drawing from dice yields integers."""
    r = RNG.dice(seed=1, logname="test_dice_draw")
    face = r.draw()
    assert isinstance(face, int)
    assert 1 <= face <= 6


def test_dice_all_faces():
    """Drawing all faces yields [1..n_sides]."""
    r = RNG.dice(seed=1, logname="test_dice_all")
    faces = r.draw(6)
    assert sorted(faces) == [1, 2, 3, 4, 5, 6]


def test_dice_deterministic():
    """Same seed produces same roll order."""
    r1 = RNG.dice(seed=42, logname="test_dice_det1")
    r2 = RNG.dice(seed=42, logname="test_dice_det2")
    assert r1.draw(6) == r2.draw(6)
