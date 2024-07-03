from .config import config
from .log import logger
import random

logger.info(f"Random number {random.randint(1, 100)} generated.")

# wandb: handle incremental log entries by:
#   - keep a table in logger consisting of logs and repeatedly upload (tabulate_logs)
#   - present source code asset name directly from asset itself

# Rewrite readme logging levels as markdown table
