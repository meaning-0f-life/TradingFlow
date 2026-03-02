from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseNode(ABC):
    """Base class for all nodes"""

    # Metadata (can be overridden by subclasses)
    display_name: str = "Base Node"
    description: str = "Base node description"
    category: str = "general"

    def __init__(self, node_id: str, config: Dict[str, Any]):
        self.node_id = node_id
        self.config = config

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the node

        Args:
            inputs: Input data from connected nodes (keyed by port)
            context: Execution context (execution_id, db session, etc.)

        Returns:
            Dictionary with output data (can have multiple ports)
        """
        pass

    @classmethod
    @abstractmethod
    def get_ui_schema(cls) -> Dict[str, Any]:
        """
        Return JSON Schema for UI configuration

        Example:
        {
            "parameters": [
                {
                    "name": "model",
                    "type": "string",
                    "title": "Model",
                    "default": "gpt-4",
                    "description": "LLM model to use"
                },
                {
                    "name": "temperature",
                    "type": "number",
                    "default": 0.7,
                    "minimum": 0,
                    "maximum": 2
                }
            ],
            "outputs": [
                {"name": "response", "type": "string", "description": "LLM response"},
                {"name": "tokens", "type": "number", "description": "Tokens used"}
            ]
        }
        """
        pass

    def _validate_config(self, required_fields: Optional[list] = None):
        """Validate node configuration"""
        if required_fields:
            missing = [field for field in required_fields if field not in self.config]
            if missing:
                raise ValueError(f"Missing required config fields: {missing}")

    def _get_input(self, inputs: Dict[str, Any], port: str = "default", default: Any = None) -> Any:
        """Get input from a specific port"""
        return inputs.get(port, default)

    def _log(self, message: str, level: str = "info", **kwargs):
        """Log with node context"""
        log_func = getattr(logger, level)
        log_func(f"[Node {self.node_id}] {message}", extra={"node_id": self.node_id, **kwargs})