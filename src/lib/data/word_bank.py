import random
from pathlib import Path

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
        self.log.info("Finished init")

    def load_file(self, path: Path = Path("/usr/share/dict/words")):
        self.log.debug(f"Loading file {path}")
        target = [word for word in path.read_text().splitlines()]
        self.words.extend(target)
        self.log.debug(f"Loaded {len(target)} words from {path}")

    def pick_word(self):
        target = random.choice(self.words)
        self.log.trace(
            multiline(
                f"""
                    Picking a random word from {len(self.words)} candidates:
                    {target}
                """
            )
        )
        return target
