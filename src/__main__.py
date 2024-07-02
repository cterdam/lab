from .config import config
from .log import logger
import random

logger.info(f"Random number {random.randint(1, 100)} generated.")

# wandb: handle incremental log entries by:
#   - add option to toggle WANDB_CONSOLE (capture_stdout)
#   - keep a table in logger consisting of logs and repeatedly upload (tabulate_logs)

# wandb warnings:
#   - wandb capture stdout but disabling stdout
#   - log to wandb but stdout and tabulate both off
