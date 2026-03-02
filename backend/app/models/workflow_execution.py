from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class WorkflowExecution(Base):
    """Workflow Execution model - tracks each run of a workflow"""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, nullable=False)
    triggered_by = Column(Integer, nullable=False)  # User ID
    status = Column(String, default="pending")  # pending, running, completed, failed
    input_data = Column(JSON, default=dict)  # Input parameters
    result_data = Column(JSON, default=dict)  # Output results
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")