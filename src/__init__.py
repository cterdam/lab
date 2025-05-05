from src.core.logger import Logger
from src.core.run_config import RunConfig
from src.core.run_context import RunContext

cfg = RunConfig()
ctx = RunContext()
log: Logger = None  # pyright:ignore

del RunConfig, RunContext, Logger
