from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution
from app.models.schemas import ExecutionCreate, ExecutionResponse
from app.api.auth import get_current_user
from app.core.engine import WorkflowExecutor

router = APIRouter()

@router.post("/run", response_model=ExecutionResponse)
async def run_workflow(
    execution_data: ExecutionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a workflow execution"""
    # Verify workflow exists and belongs to user
    workflow = db.query(Workflow).filter(
        Workflow.id == execution_data.workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    # Create execution record
    execution = WorkflowExecution(
        workflow_id=workflow.id,
        triggered_by=current_user.id,
        status="pending",
        input_data=execution_data.input_data
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # Start async execution (in background)
    # In production, use Celery/ARQ
    executor = WorkflowExecutor(workflow.config, execution.id, db)
    await executor.execute()

    # Update execution status
    execution.status = "running"
    db.commit()

    return execution

@router.get("/executions", response_model=List[ExecutionResponse])
def get_executions(
    workflow_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get execution history"""
    query = db.query(WorkflowExecution).join(Workflow).filter(
        Workflow.owner_id == current_user.id
    )
    if workflow_id:
        query = query.filter(WorkflowExecution.workflow_id == workflow_id)

    executions = query.order_by(WorkflowExecution.started_at.desc())\
        .offset(skip).limit(limit).all()
    return executions

@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
def get_execution(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific execution details"""
    execution = db.query(WorkflowExecution).join(Workflow).filter(
        WorkflowExecution.id == execution_id,
        Workflow.owner_id == current_user.id
    ).first()
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    return execution