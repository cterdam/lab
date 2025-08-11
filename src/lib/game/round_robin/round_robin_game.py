from transitions import Machine

from src.lib.game.game import Game


class RoundRobinGame(Game):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fsm = Machine(
            model=self,
            states=[States.START, States.GOING, States.ENDED],
        )
