from fastapi import APIRouter
from app.nodes import get_available_nodes

router = APIRouter()

@router.get("/types")
def get_node_types():
    """Get all available node types with their schemas"""
    return get_available_nodes()