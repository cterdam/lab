from src import log
from src.lib.data.word_bank import WordBank
from src.lib.model.txt.api.openai import (
    OpenaiLm,
    OpenaiLmGentxtParams,
    OpenaiLmInitParams,
)


def main():

    word_bank = WordBank()
    model = OpenaiLm(params=OpenaiLmInitParams(model_name="gpt-4.1"))
    result = model.gentxt(
        OpenaiLmGentxtParams(prompt=f"In 10 words, what is {word_bank.pick_word()}")
    )
    log.info(result.output)
