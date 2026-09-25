"""Scan scheduler manager coordinating active scanning strategy and runtime switching."""
import logging
from typing import Dict, List, Optional, Type
from backend.shared.config import settings
from backend.scheduler.base import ScanStrategy
from backend.scheduler.models import SchedulerContext
from backend.scheduler.round_robin import RoundRobinStrategy
from backend.scheduler.random import RandomStrategy

logger = logging.getLogger("ew.scheduler.manager")


class SchedulerManager:
    """Manages receiver scan strategies, runtime switching, and band selection.
    
    Acts as the single point of contact for ReceiverService to ask:
    "Give me the next scan band."
    
    Decoupled from receiver hardware limits and detection physics.
    Supports dynamic registration so future strategies (e.g. ML, RL) can be added cleanly.
    """

    def __init__(
        self,
        default_strategy: Optional[str] = None,
        random_seed: Optional[int] = None,
    ) -> None:
        self._strategy_registry: Dict[str, Type[ScanStrategy]] = {
            "round_robin": RoundRobinStrategy,
            "random": RandomStrategy,
        }
        self._instances: Dict[str, ScanStrategy] = {
            "round_robin": RoundRobinStrategy(),
            "random": RandomStrategy(seed=random_seed),
        }
        initial_name = default_strategy or getattr(settings, "DEFAULT_SCAN_STRATEGY", "round_robin")
        self._current_strategy_name: str = ""
        self._current_strategy: ScanStrategy = self._instances["round_robin"]
        self.set_strategy(initial_name)

    @property
    def current_strategy(self) -> ScanStrategy:
        """The active ScanStrategy instance."""
        return self._current_strategy

    def get_strategy(self) -> str:
        """Return the identifier of the active scan strategy."""
        return self._current_strategy_name

    def get_available_strategies(self) -> List[str]:
        """Return list of supported strategy names."""
        return list(self._strategy_registry.keys())

    def register_strategy(
        self,
        name: str,
        strategy_cls: Type[ScanStrategy],
        instantiate: bool = True
    ) -> None:
        """Register a new scan strategy class (e.g. future MLStrategy)."""
        canonical_name = name.strip().lower()
        self._strategy_registry[canonical_name] = strategy_cls
        if instantiate:
            self._instances[canonical_name] = strategy_cls()
        logger.info(f"Registered new scan strategy: '{canonical_name}' -> {strategy_cls.__name__}")

    def set_strategy(self, name: str) -> str:
        """Change the active strategy at runtime.
        
        Args:
            name: Strategy identifier (e.g. 'round_robin', 'random').
            
        Returns:
            The confirmed active strategy name.
            
        Raises:
            ValueError: If the requested strategy is not supported.
        """
        canonical_name = name.strip().lower()
        if canonical_name not in self._strategy_registry:
            raise ValueError(f"Unsupported scan strategy: {name}")

        if canonical_name not in self._instances:
            self._instances[canonical_name] = self._strategy_registry[canonical_name]()

        self._current_strategy_name = canonical_name
        self._current_strategy = self._instances[canonical_name]
        logger.info(f"Active scan strategy set to '{canonical_name}'.")
        return canonical_name

    def next_scan(
        self,
        bands: List[float],
        context: Optional[SchedulerContext] = None
    ) -> float:
        """Select the next scan band using the active strategy."""
        return self._current_strategy.select_band(bands, context)

    def reset(self) -> None:
        """Reset the active strategy and all strategy instances."""
        for strategy in self._instances.values():
            strategy.reset()
        logger.info("SchedulerManager reset all strategies.")


# Alias for flexible naming convention
ScanScheduler = SchedulerManager
