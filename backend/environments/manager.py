"""Environment Manager tracking active scenario and handling switching."""
import logging
from typing import List, Optional
from backend.environments.models import EnvironmentConfig, EnvironmentSummary
from backend.environments.registry import EnvironmentRegistry, global_environment_registry

logger = logging.getLogger("ew.environment")


class EnvironmentManager:
    """Manages active environment selection and scenario definitions."""

    def __init__(self, registry: Optional[EnvironmentRegistry] = None, default_env_id: str = "OPEN_SPARSE"):
        self.registry = registry or global_environment_registry
        self.current_environment: EnvironmentConfig = self.load_environment(default_env_id)

    def load_environment(self, environment_id: str) -> EnvironmentConfig:
        """Switch to and return the specified environment configuration."""
        loader = self.registry.get_loader(environment_id)
        if not loader:
            valid_ids = ", ".join(self.registry.list_environment_ids())
            raise ValueError(f"Unknown environment_id '{environment_id}'. Valid environments: [{valid_ids}]")

        config = loader()
        self.current_environment = config
        logger.info(f"Environment switched to '{config.name}' ({config.environment_id}) with {len(config.emitters)} emitters.")
        return config

    def get_current_environment(self) -> EnvironmentConfig:
        """Return the currently loaded environment configuration."""
        return self.current_environment

    def list_environments(self) -> List[EnvironmentSummary]:
        """List metadata summaries for all registered environments."""
        return self.registry.list_summaries()


global_environment_manager = EnvironmentManager()
