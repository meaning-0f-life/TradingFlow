from typing import Dict, Any, Type
from .base import BaseNode
from .llm_node import LLMNode
from .data_node import DataFetcherNode

# Node registry
NODE_REGISTRY: Dict[str, Type[BaseNode]] = {
    "llm": LLMNode,
    "data_fetcher": DataFetcherNode,
}

def register_node(node_type: str, node_class: Type[BaseNode]):
    """Register a node type"""
    NODE_REGISTRY[node_type] = node_class

def get_node_class(node_type: str) -> Type[BaseNode]:
    """Get node class by type"""
    if node_type not in NODE_REGISTRY:
        raise ValueError(f"Unknown node type: {node_type}. Available types: {list(NODE_REGISTRY.keys())}")
    return NODE_REGISTRY[node_type]

def get_available_nodes() -> Dict[str, Dict]:
    """Get all available nodes with their UI schemas"""
    result = {}
    for node_type, node_class in NODE_REGISTRY.items():
        result[node_type] = {
            "name": node_type,
            "display_name": getattr(node_class, "display_name", node_type),
            "description": getattr(node_class, "description", ""),
            "category": getattr(node_class, "category", "general"),
            "ui_schema": node_class.get_ui_schema()
        }
    return result