from src.core.arguments import Arguments
from src.core.environment import Environment
from src.core.logger import Logger

arg = Arguments()
env = Environment()
log = Logger(log_name="global")

del Arguments, Environment, Logger
