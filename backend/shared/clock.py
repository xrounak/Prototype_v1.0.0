"""Centralized Simulation Clock.

Decouples simulation progression from real wall-clock time.
Allows discrete steps, deterministic playback, and pause/resume capability.
"""
from threading import Lock


class SimulationClock:
    """Central simulation time abstraction."""

    def __init__(self, initial_time: float = 0.0):
        self._lock = Lock()
        self._current_time: float = round(float(initial_time), 6)

    def now(self) -> float:
        """Return the current simulation time in seconds."""
        with self._lock:
            return self._current_time

    @property
    def current_time(self) -> float:
        """Property getter for current simulation time."""
        return self.now()

    def advance(self, delta_seconds: float) -> float:
        """Advance the simulation time by delta_seconds and return updated time.

        Args:
            delta_seconds: Non-negative elapsed time to advance in seconds.
        """
        if delta_seconds < 0:
            raise ValueError(f"Cannot advance negative simulation time: {delta_seconds}")
        with self._lock:
            self._current_time = round(self._current_time + delta_seconds, 6)
            return self._current_time

    def set_time(self, new_time: float) -> float:
        """Set simulation time to an explicit non-negative value."""
        if new_time < 0:
            raise ValueError(f"Simulation time cannot be negative: {new_time}")
        with self._lock:
            self._current_time = round(float(new_time), 6)
            return self._current_time

    def reset(self, start_time: float = 0.0) -> float:
        """Reset the simulation clock to start_time."""
        return self.set_time(start_time)
