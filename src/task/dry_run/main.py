from src import log
from src.lib.data.word_bank import WordBank
from src.lib.model import Model
from src.lib.model.txt import GentxtParams


def main():

    model = Model("openai/gpt-4.1")
    word_bank = WordBank()
    result = model.gentxt(
        GentxtParams(prompt=f"In 10 words, what is {word_bank.pick_word()}")
    )
    log.info(result.output)
