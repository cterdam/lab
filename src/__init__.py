from src.core.config import Config
from src.core.context import Context
from src.core.logger import Logger

cfg = Config()
ctx = Context()
log: Logger = None  # pyright:ignore

del Config, Context, Logger
