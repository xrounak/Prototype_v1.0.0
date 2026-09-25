"""Round-Robin scan strategy sequentially cycling through available bands."""
import logging
from typing import List, Optional
from backend.scheduler.base import ScanStrategy
from backend.scheduler.models import SchedulerContext

logger = logging.getLogger("ew.scheduler.round_robin")


class RoundRobinStrategy(ScanStrategy):
    """Sequential scan strategy cycling through available bands in order.
    
    Given bands [B1, B2, B3], yields B1, B2, B3, B1, B2...
    Maintains its own internal sweep index independently of receiver hardware.
    """

    def __init__(self) -> None:
        self._index: int = 0

    @property
    def name(self) -> str:
        return "round_robin"

    @property
    def index(self) -> int:
        """Current sequence index."""
        return self._index

    @index.setter
    def index(self, value: int) -> None:
        self._index = max(0, value)

    def select_band(
        self,
        bands: List[float],
        context: Optional[SchedulerContext] = None
    ) -> float:
        """Select the next band in sequential order, wrapping around at the end."""
        if not bands:
            raise ValueError("Available bands list cannot be empty")

        selected = bands[self._index % len(bands)]
        self._index += 1
        return selected

    def reset(self) -> None:
        """Reset sequence index back to 0."""
        self._index = 0
        logger.debug("RoundRobinStrategy reset to index 0.")
