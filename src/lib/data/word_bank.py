import random
from pathlib import Path

from src import log
from src.core import DataCore
from src.core.util import multiline
from src.lib.data import DataBasis


class WordBank(DataBasis):
    """A simple bank of words."""

    def __init__(self, log_name: str = "word_bank", *args, **kwargs):
        super().__init__(
            log_name=log_name,
            *args,
            **kwargs,
        )
        self.words = []
        self.load_file()

    def load_file(self, path: Path = Path("/usr/share/dict/words")):
        target = [word for word in path.read_text().splitlines()]
        self.words.extend(target)

    def pick_word(self):
        target = random.choice(self.words)
        return target
