from src.lib.game.round_based_game import RoundBasedGame


class RoundRobinGame(RoundBasedGame):
    """A round-robin game.

    A round-robin game is a round-based game where each round is defined as
    each player taking a turn in order.
    """
