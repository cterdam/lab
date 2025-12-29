from enum import StrEnum

from src.lib.data.data import Data


class Serial(Data):
    """Service to generate monotonically increasing serial numbers."""

    logspace_part = "serial"

    class coke(StrEnum):
        SERIAL = "serial"

    def __init__(self, *args, logname: str = "serial", **kwargs):
        """Initialize the Serial service."""
        super().__init__(*args, logname=logname, **kwargs)

    def next(self) -> int:
        """Get the next serial number using a Redis counter."""
        return self.incr(Serial.coke.SERIAL)
