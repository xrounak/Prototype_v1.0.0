"""Random scan strategy uniformly picking from available bands."""
import logging
import random as py_random
from typing import List, Optional
from backend.scheduler.base import ScanStrategy
from backend.scheduler.models import SchedulerContext

logger = logging.getLogger("ew.scheduler.random")


class RandomStrategy(ScanStrategy):
    """Uniform random selection strategy across available scan bands.
    
    Randomly chooses from the same valid discrete scan bands used by the receiver/environment.
    Supports an optional seed for deterministic testing and reproducible simulation runs.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._seed = seed
        self._rng = py_random.Random(seed)

    @property
    def name(self) -> str:
        return "random"

    @property
    def seed(self) -> Optional[int]:
        return self._seed

    def select_band(
        self,
        bands: List[float],
        context: Optional[SchedulerContext] = None
    ) -> float:
        """Select a random band from the provided available bands list."""
        if not bands:
            raise ValueError("Available bands list cannot be empty")
        return self._rng.choice(bands)

    def reset(self) -> None:
        """Reset random generator (re-seeding if a seed was specified)."""
        self._rng = py_random.Random(self._seed)
        logger.debug("RandomStrategy reset.")
