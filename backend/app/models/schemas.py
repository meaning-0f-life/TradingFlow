from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# API Key schemas
class APIKeyCreate(BaseModel):
    name: str
    service: str
    key: str  # Plain text key, will be encrypted

class APIKeyResponse(BaseModel):
    id: int
    name: str
    service: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Workflow schemas
class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: dict = Field(default_factory=dict)

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None

class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    is_active: bool
    config: dict
    version: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Execution schemas
class ExecutionCreate(BaseModel):
    workflow_id: int
    input_data: dict = Field(default_factory=dict)

class ExecutionResponse(BaseModel):
    id: int
    workflow_id: int
    triggered_by: int
    status: str
    input_data: dict
    result_data: dict
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True