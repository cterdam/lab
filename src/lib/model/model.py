from abc import ABC

from src.core import Logger


class Model(ABC, Logger):
    """Base class for models."""

    logspace_part = "model"
