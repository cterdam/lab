import os
import platform
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
    def load_file(self, path: Path = None):
        if path is None:
            if platform.system() == "Windows":
                # Use dictionary.txt in the user's home directory on Windows.
                path = Path(os.path.expanduser("~")) / "dictionary.txt"
                if not path.exists():
                    self.log.warning(f"cannot find dictionary file: {path}")
                    self.log.info(
                        "Please refer to https://github.com/STAT545-UBC/Discussion/issues/49 to download the dictionary file."
                    )
                    self.words = ["default", "word", "list", "as", "fallback"]
                    return
            else:
                # Use system dictionary on Linux/Mac.
                path = Path("/usr/share/dict/words")

        try:
            target = [word for word in path.read_text().splitlines()]
            self.words.extend(target)
            self.log.info(f"loaded {len(target)} words")
        except Exception as e:
            self.log.error(f"failed to load dictionary file: {e}")
            self.words = ["default", "word", "list", "as", "fallback"]

    @log.output()
    def pick_word(self):
        target = random.choice(self.words)
        return target
