"""Modular behaviour strategy registry and factory."""
from typing import Dict, Union
from backend.emitter.models import BehaviorType
from backend.emitter.behaviours.base import BaseBehaviour
from backend.emitter.behaviours.continuous import ContinuousBehaviour
from backend.emitter.behaviours.periodic import PeriodicBehaviour
from backend.emitter.behaviours.burst import BurstBehaviour
from backend.emitter.behaviours.jittered import JitteredBehaviour
from backend.emitter.behaviours.staggered import StaggeredBehaviour
from backend.emitter.behaviours.frequency_hopping import FrequencyHoppingBehaviour
from backend.emitter.behaviours.frequency_agile import FrequencyAgileBehaviour

_BEHAVIOUR_INSTANCES: Dict[str, BaseBehaviour] = {
    "CONTINUOUS": ContinuousBehaviour(),
    "PERIODIC": PeriodicBehaviour(),
    "BURST": BurstBehaviour(),
    "JITTERED": JitteredBehaviour(),
    "STAGGERED": StaggeredBehaviour(),
    "FREQUENCY_HOPPING": FrequencyHoppingBehaviour(),
    "FREQUENCY_AGILE": FrequencyAgileBehaviour(),
}


def get_behaviour_strategy(behaviour_type: Union[BehaviorType, str]) -> BaseBehaviour:
    """Return the strategy handler instance for the specified behaviour type."""
    key = str(behaviour_type.value if hasattr(behaviour_type, "value") else behaviour_type).upper()
    if key not in _BEHAVIOUR_INSTANCES:
        # Default fallback to periodic
        return _BEHAVIOUR_INSTANCES["PERIODIC"]
    return _BEHAVIOUR_INSTANCES[key]


__all__ = [
    "BaseBehaviour",
    "ContinuousBehaviour",
    "PeriodicBehaviour",
    "BurstBehaviour",
    "JitteredBehaviour",
    "StaggeredBehaviour",
    "FrequencyHoppingBehaviour",
    "FrequencyAgileBehaviour",
    "get_behaviour_strategy",
]
