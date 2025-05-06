from src.core.arguments import Arguments
from src.core.environment import Environment
from src.core.logger import Logger

arg = Arguments()
env = Environment()
log: Logger = None  # pyright:ignore

del Arguments, Environment, Logger
