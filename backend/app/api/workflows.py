from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.workflow import Workflow
from app.models.schemas import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse,
    ExecutionCreate, ExecutionResponse
)
from app.api.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[WorkflowResponse])
def get_workflows(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all workflows for current user"""
    workflows = db.query(Workflow).filter(
        Workflow.owner_id == current_user.id
    ).offset(skip).limit(limit).all()
    return workflows

@router.post("/", response_model=WorkflowResponse)
def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new workflow"""
    new_workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        config=workflow_data.config,
        owner_id=current_user.id
    )
    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)
    return new_workflow

@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific workflow"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    return workflow

@router.put("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(
    workflow_id: int,
    workflow_update: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a workflow"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    update_data = workflow_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)

    # Increment version on config update
    if "config" in update_data:
        workflow.version += 1

    db.commit()
    db.refresh(workflow)
    return workflow

@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a workflow"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    db.delete(workflow)
    db.commit()
    return None