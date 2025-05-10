import random
from pathlib import Path

from src import log
from src.lib.data import DataBasis


class WordBank(DataBasis):
    """A simple bank of words."""

    @log.input()
    def __init__(self, log_name: str = "word_bank", *args, **kwargs):
        super().__init__(
            log_name=log_name,
            *args,
            **kwargs,
        )
        self.words = []
        self.load_file()

    @log.input()
    def load_file(self, path: Path = Path("/usr/share/dict/words")):
        target = [word for word in path.read_text().splitlines()]
        self.words.extend(target)

    @log.output()
    def pick_word(self):
        target = random.choice(self.words)
        return target
