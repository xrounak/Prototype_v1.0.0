"""Environment Registry linking environment identifiers to their configuration factories."""
from typing import Callable, Dict, List, Optional
from backend.environments.models import EnvironmentConfig, EnvironmentSummary
from backend.environments.open_sparse import get_open_sparse_config
from backend.environments.dense_urban import get_dense_urban_config
from backend.environments.mountainous import get_mountainous_config
from backend.environments.frequency_agile import get_frequency_agile_config

EnvironmentLoader = Callable[[], EnvironmentConfig]


class EnvironmentRegistry:
    """Registry managing available simulation environments."""

    def __init__(self):
        self._loaders: Dict[str, EnvironmentLoader] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register the 4 standard baseline simulation environments."""
        self.register("OPEN_SPARSE", get_open_sparse_config)
        self.register("DENSE_URBAN", get_dense_urban_config)
        self.register("MOUNTAINOUS", get_mountainous_config)
        self.register("FREQUENCY_AGILE", get_frequency_agile_config)

    def register(self, environment_id: str, loader: EnvironmentLoader) -> None:
        """Register a new environment factory."""
        self._loaders[environment_id.upper()] = loader

    def get_loader(self, environment_id: str) -> Optional[EnvironmentLoader]:
        """Get the factory for a specific environment."""
        return self._loaders.get(environment_id.upper())

    def list_environment_ids(self) -> List[str]:
        """List registered environment IDs."""
        return list(self._loaders.keys())

    def list_summaries(self) -> List[EnvironmentSummary]:
        """Retrieve metadata summaries for all registered environments."""
        summaries: List[EnvironmentSummary] = []
        for env_id, loader in self._loaders.items():
            try:
                cfg = loader()
                summaries.append(cfg.to_summary())
            except Exception as e:
                # Log error and continue
                continue
        return summaries


global_environment_registry = EnvironmentRegistry()
