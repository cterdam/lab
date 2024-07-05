from .config import config
from .log import logger
import random

logger.info(f"Random number {random.randint(1, 100)} generated.")

# wandb: handle incremental log entries by:

#   - add wandb sink which takes a msg and reports it to wandb using internal
#   table. This is only added as a sink if wandb/tabulate_logs.

#   - add metric method which is called during training loop and formats a dict as msgs
#   to log. if using wandb, then it also reports the dict directly to wandb.

# Rewrite readme logging levels as markdown table
