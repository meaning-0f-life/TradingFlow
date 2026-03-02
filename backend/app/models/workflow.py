from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Workflow(Base):
    """Workflow model - stores the visual workflow definition"""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    config = Column(JSON, default=dict)  # Stores the workflow graph (nodes, edges)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow")