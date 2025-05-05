from src import log
from src.lib.model import Model
from src.lib.model.txt import GentxtParams


def main():

    model = Model("openai/gpt-4.1")
    result = model.gentxt(GentxtParams(prompt="Howdy"))
    log.info(result.output)
