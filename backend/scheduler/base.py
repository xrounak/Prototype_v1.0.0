"""Abstract base class defining the scan strategy interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from backend.scheduler.models import SchedulerContext


class ScanStrategy(ABC):
    """Abstract base class for receiver scan strategies.
    
    The scheduler strategy decides WHAT frequency band should be scanned next.
    Receiver physics (bandwidth, dwell time, RF tuning limits, detection) are strictly decoupled.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique strategy name identifier (e.g. 'round_robin', 'random')."""
        pass

    @abstractmethod
    def select_band(
        self,
        bands: List[float],
        context: Optional[SchedulerContext] = None
    ) -> float:
        """Select the next frequency start point (in Hz) from the available bands.
        
        Args:
            bands: List of valid starting frequencies (Hz) available to scan.
            context: Optional simulation context (time, previous scan, detections, etc.)
            
        Returns:
            The selected frequency start point in Hz.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset internal strategy state (e.g. on simulation reset or scenario change)."""
        pass
