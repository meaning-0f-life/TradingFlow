from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db, SessionLocal
from app.models.user import User
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution
from app.models.schemas import ExecutionCreate, ExecutionResponse
from app.api.auth import get_current_user
from app.core.engine import WorkflowExecutor

router = APIRouter()

def run_workflow_background(execution_id: int, workflow_config: dict):
    """Background task to run workflow execution"""
    # Create new DB session for background task
    db = SessionLocal()
    try:
        # Get execution record
        execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
        if not execution:
            print(f"Execution {execution_id} not found")
            return

        # Update status to running
        execution.status = "running"
        db.commit()

        # Create executor and run
        executor = WorkflowExecutor(workflow_config, execution_id, db)
        await executor.execute()

        # Update execution with results
        execution.status = "completed"
        execution.result_data = {
            "node_results": executor.results,
            "execution_order": executor.execution_order,
            "errors": executor.errors
        }
        db.commit()

    except Exception as e:
        # Update execution with error
        execution.status = "failed"
        execution.error_message = str(e)
        execution.result_data = {
            "partial_results": getattr(executor, 'results', {}),
            "errors": getattr(executor, 'errors', [])
        }
        db.commit()
        print(f"Workflow execution {execution_id} failed: {e}")

    finally:
        db.close()

@router.post("/run", response_model=ExecutionResponse)
async def run_workflow(
    execution_data: ExecutionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a workflow execution (returns immediately, runs in background)"""
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

    # Create execution record with running status
    execution = WorkflowExecution(
        workflow_id=workflow.id,
        triggered_by=current_user.id,
        status="running",  # Set to running immediately
        input_data=execution_data.input_data
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # Start execution in background
    background_tasks.add_task(run_workflow_background, execution.id, workflow.config)

    # Return execution record immediately
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