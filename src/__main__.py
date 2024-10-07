from .config import config
from .log import logger
import random

logger.info(f"Random number {random.randint(1, 100)} generated.")
